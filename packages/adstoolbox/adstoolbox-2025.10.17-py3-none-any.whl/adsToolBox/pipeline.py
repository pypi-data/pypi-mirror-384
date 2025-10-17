from .timer import timer
from .logger import Logger
from .dbMysql import dbMysql
from .dbMssql import dbMssql
import polars as pl
import hashlib

class pipeline:
    SQL_TO_POLARS = {
        "int": pl.Int64,
        "integer": pl.Int64,
        "bigint": pl.Int64,
        "smallint": pl.Int32,
        "varchar": pl.Utf8,
        "text": pl.Utf8,
        "char": pl.Utf8,
        "time": pl.Time,
        "timestamp": pl.Datetime,
        "datetime": pl.Datetime,
        "datetime2": pl.Datetime,
        "date": pl.Date,
        "decimal": pl.Decimal,
        "numeric": pl.Decimal,
        "float": pl.Float64,
        "double": pl.Float64,
        "boolean": pl.Boolean,
    }

    def __init__(self, dictionnary: dict, logger: Logger):
        """
        Initialise un pipeline avec les informations de connexions aux bases de données
        :param dictionnary: le dictionnaire qui contient les informations du pipeline
            - 'db_source': la base de données source
            - 'query_source': la requête à envoyer à la source
            - 'tableau': les données sous forme de tableau (source alternative)
            - 'db_destination': la base de données destination
            - 'executemany' ou 'bulk'
            - 'batch_size': la taille des lots pour le traitement en batch
        :param logger: le logger pour gérer la journalisation des évènements du pipeline
        """
        self.logger = logger
        self.__db_source = dictionnary.get('db_source')
        self.__query_source = dictionnary.get('query_source')
        self.__tableau = dictionnary.get('tableau')
        self.db_destination = dictionnary.get('db_destination')
        self.operation_type = dictionnary.get('operation_type', 'insert')
        self.insert_method = dictionnary.get("insert_method", "bulk")
        self.batch_size = dictionnary.get('batch_size', 10_000)
        self.db_destination.get('db').batch_size = self.batch_size
        if self.__db_source:
            self.__db_source.batch_size = self.batch_size

    def _generate_hash(self, row, cols):
        """
        Génère un hash MD5 pour une ligne de valeurs donnée
        :param row: La ligne de données
        :param cols: Les colonnes de la table
        :return: Le hash de la ligne
        """
        concat_cols = "|".join(str(row[col]) if row[col] is not None else "null" for col in cols)
        return hashlib.md5(concat_cols.encode("utf-8")).hexdigest()

    def sql_defs_to_polars_schema(self, cols, cols_def, logger=None):
        schema = {}
        for col, sql_type in zip(cols, cols_def):
            base_type = sql_type.split("(")[0].lower()
            if isinstance(self.__db_source, dbMysql) and sql_type.lower() == 'time':
                pl_type = pl.Utf8
            else:
                pl_type = pipeline.SQL_TO_POLARS.get(base_type)
                if not pl_type:
                    if logger:
                        logger.debug(f"Type SQL non reconnu '{sql_type}', fallback en Utf8 pour la colonne '{col}'.")
                    pl_type = pl.Utf8
            schema[col] = pl_type
        return schema

    def _update_schema(self, old_schema, new_schema):
        """
        Met à jour l'ancien schéma en remplaçant les colonnes encore set à pl.Null
        :param old_schema: L'ancien schéma
        :param new_schema: Le nouveau schéma du batch en cours
        :return: Le schéma mis à jour
        """
        updated_schema = old_schema.copy()
        for col, dtype in old_schema.items():
            if dtype == pl.Null and col in new_schema:
                updated_schema[col] = new_schema[col]
        return updated_schema

    def _data_generator(self):
        """
        Générateur de données qui itère sur les données sources, qu'elles proviennent d'un tableau en mémoire
        ou d'une base de données, en les renvoyant sous forme de DataFrame par lots (batches).
        :return: Yield un DataFrame Polars contenant un batch de données.
        :raises ValueError: Si deux sources de données sont spécifiées (tableau et base de données)
        ou si aucune source de données valide n'est définie.
        """
        self.logger.info("Chargement des données depuis la source...")
        if self.__tableau is not None and self.__db_source is not None:
            msg = "Deux sources de données différentes sont définies, veuillez n'en choisir qu'une."
            self.logger.error(msg)
            raise ValueError(msg)
        cols = self.db_destination.get("cols", [])
        cols_def = self.db_destination.get("cols_def", [])
        hash_col = self.db_destination.get("hash")
        apply_hash = hash_col in cols if hash_col else False
        schema = None

        def process_batch(batch):
            nonlocal schema
            if isinstance(batch, pl.DataFrame):
                return batch
            batch_dicts = [dict(zip(cols, row)) for row in batch]
            if apply_hash:
                for row in batch_dicts:
                    cols_to_hash = [col for col in cols if col != hash_col]
                    row[hash_col] = self._generate_hash(row, cols_to_hash)
            if schema is None:
                if cols_def and all(t is not None for t in cols_def):
                    schema = self.sql_defs_to_polars_schema(cols, cols_def)
                    df = pl.DataFrame(batch_dicts, schema=schema, orient='row', strict=False)
                else:
                    self.logger.debug("Inférence des types sur le premier batch")
                    df = pl.DataFrame(batch_dicts, orient='row', strict=False, infer_schema_length=len(batch_dicts))
                    schema = df.schema
            else:
                if any(dtype == pl.Null for dtype in schema.values()):
                    self.logger.debug("Réinférence partielle des types")
                    df_temp = pl.DataFrame(batch_dicts, orient='row', strict=False, infer_schema_length=len(batch_dicts))
                    schema = self._update_schema(schema, df_temp.schema)
                df = pl.DataFrame(batch_dicts, schema=schema, orient='row', strict=False)
            return df

        if self.__tableau is not None and len(self.__tableau) > 0:
            for start in range(0, len(self.__tableau), self.batch_size):
                batch = self.__tableau[start:start + self.batch_size]
                try:
                    yield process_batch(batch)
                except Exception as e:
                    self.logger.error(f"Échec de la création du dataframe: {e}")
                    yield None, batch
        elif self.__db_source and self.__query_source:
            log_level, log_base = self.logger.disable()
            self.__db_source.connect()
            self.logger.enable(log_level, log_base)
            for batch in self.__db_source.sqlQuery(self.__query_source):
                try:
                    yield process_batch(batch)
                except Exception as e:
                    msg = f"Échec de la création du dataframe: {e}"
                    if isinstance(self.__db_source, dbMysql):
                        msg += "\n(Pour MySQL, pensez à utiliser TIME_FORMAT(col, '%H:%i:%s') sur vos colonnes TIME)"
                    elif isinstance(self.__db_source, dbMssql):
                        msg += "\n(Pour SQL Server, pensez à CAST(uuid_col AS NVARCHAR(36)) si vous avez des UUID en UNIQUEIDENTIFIER)"
                    for line in msg.split("\n("):
                        self.logger.error(line)
                    yield None, batch
        else:
            raise ValueError("Source de données non supportée.")

    @timer
    def create_destination_table(self, drop: bool=False):
        """Supprime et crée la table de destination du pipeline"""
        dst = self.db_destination.get('db')
        schema = self.db_destination.get('schema')
        table = self.db_destination.get('table')
        full_table = f"{schema}.{table}" if schema else table
        cols = self.db_destination.get('cols')
        cols_def = self.db_destination.get('cols_def')
        if len(cols) != len(cols_def):
            raise ValueError("Le nombre de colonnes (cols) ne correspond pas au nombre de définitions (cols_def)")
        columns = ', '.join([f"{col} {defn}" for col, defn in zip(cols, cols_def)])
        dst.connect()
        self.logger.info("Création de la table de destination...")
        try:
            if drop:
                dst.sqlExec(f"DROP TABLE IF EXISTS {full_table}")
            dst.sqlExec(f"CREATE TABLE {full_table} ({columns})")
            self.logger.info("Table de destination créée.")
        except Exception as e:
            self.logger.error(f"Erreur lors de la création de la table de destination: {e}")
            raise

    def _insert(self, rows):
        """Insertion par bulk ou executemany"""
        if self.insert_method == "bulk":
            return self.db_destination.get("db").insertBulk(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols")
            )
        elif self.insert_method == "executemany":
            return self.db_destination.get("db").insertMany(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols")
            )

    def _upsert(self, rows):
        """Upsert par bulk ou executemany"""
        if self.insert_method == "bulk":
            return self.db_destination.get("db").upsertBulk(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols"),
                conflict_cols=self.db_destination.get("conflict_cols")
            )
        elif self.insert_method == "executemany":
            return self.db_destination.get("db").upsertMany(
                schema=self.db_destination.get("schema"),
                table=self.db_destination.get("table"),
                rows=rows,
                cols=self.db_destination.get("cols"),
                conflict_cols=self.db_destination.get("conflict_cols")
            )

    def _perform_insertion(self, rows):
        """Effectue l'insertion ou l'upsert des données"""
        method_map = {
            "insert": self._insert,
            "upsert": self._upsert
        }
        return method_map[self.operation_type](rows)

    @timer
    def run(self):
        """
        Exécute le pipeline en insérant des données depuis la source vers la destination définie.
        :return: Une liste des lots rejetés contenant les erreurs lors de l'insertion.
        :raises Exception: Si une erreur autre qu'une erreur d'insertion survient pendant l'exécution du pipeline
        """
        rejects = []
        res = {"nb_lines_success": 0, "nb_lines_error": 0, "errors": rejects}
        batch_cpt = 1
        total = 0
        total_inserted = 0
        schema = self.db_destination.get('schema')
        table = self.db_destination.get('table')
        table_full = f"{schema}.{table}" if schema else table
        try:
            log_level, base_level = self.logger.disable()
            self.db_destination['db'].connect()
            self.logger.enable(log_level, base_level)
            name = self.db_destination.get('name', 'bdd')
            self.logger.info(f"Connexion à {name} réussie.")
            for batch_df in self._data_generator():
                taille = len(batch_df)
                total += taille
                if isinstance(batch_df, tuple) and batch_df[0] is None:
                    rejects.append((name, "Échec création dataframe", batch_df[1]))
                    res["nb_lines_error"] += len(batch_df[1])
                    continue
                rows = batch_df.rows()
                old_global, old_base = self.logger.disable()
                self.logger.enable(Logger.ERROR, Logger.ERROR)
                insert_result = self._perform_insertion(rows)
                self.logger.enable(old_global, old_base)
                if not insert_result:
                    raise ValueError("Aucune opération n'a été réalisée, vérifiez les operation_type et insert_method.")
                if insert_result[0] == "ERROR":
                    rejects.append((name, insert_result, rows))
                    res["nb_lines_error"] += taille
                else:
                    total_inserted += taille
                    res["nb_lines_success"] += taille
                    self.logger.info(
                        f"Batch {batch_cpt}: {taille} ligne(s) insérée(s) avec succès dans la table {table_full}. "
                        f"Total inséré: {total_inserted}/{total} ligne(s).")
                    batch_cpt += 1
        except Exception as e:
                self.logger.enable()
                self.logger.error(f"Échec de l'exécution du pipeline: {e}")
                raise
        return res