import timeit
import pymssql
import polars as pl
from .timer import timer, get_timer
from .dataFactory import data_factory

class dbMssql(data_factory):
    def __init__(self, dictionnary: dict, logger, batch_size=10_000):
        """
        instancie la classe dbMssql, qui hérite de dataFactory
        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion sql server
        :param logger: un logger ads qui va gérer les logs des actions de la classe
        :param batch_size: la taille des batchs en lecture et écriture
        """
        self.connection = None
        self.logger = logger
        self.__database = dictionnary.get('database')
        self.__user = dictionnary.get('user')
        self.__password = dictionnary.get('password')
        self.__port = dictionnary.get('port')
        self.__host = dictionnary.get('host')
        self.__charset = dictionnary.get('charset', 'UTF-8')
        self.batch_size = batch_size

    @timer
    def connect(self):
        """
        lance la connexion avec les identifiants passés à l'initialisation de la classe
        toutes les méthodes de la classe nécéssitent une connexion active
        :return: la connexion
        """
        if self.logger is not None: self.logger.info("Tentative de connexion avec la base de données.")
        try:
            server = f"{self.__host}:{self.__port}" if self.__port else self.__host
            self.connection = pymssql.connect(
                server=server,
                user=self.__user,
                password=self.__password,
                database=self.__database,
                charset=self.__charset
            )
            if self.logger is not None: self.logger.info(f"Connexion établie avec la base de données.")
            return self.connection
        except Exception as e:
            if self.logger is not None: self.logger.error(f"Échec de la connexion à la base de données: {e}")
            raise

    def sqlQuery(self, query: str, return_columns: bool = False):
        """
        lit la base de données avec la requête query
        :param return_columns: booléen qui indique si l'on veut récupérer les colonnes de la tables
        :param query: la requête
        :return: les données lues avec yield
        """
        self.logger.debug(f"Exécution de la requête de lecture : {query}")
        try:
            timer_start = timeit.default_timer()
            cpt_rows = 0
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if return_columns:
                    cols = [desc[0] for desc in cursor.description]
                    yield cols
                self.logger.info("Requête exécutée avec succès, début de la lecture des résultats.")
                while True:
                    rows = cursor.fetchmany(self.batch_size)
                    if not rows:
                        break
                    yield rows
                    cpt_rows+=len(rows)
                    self.logger.info(f"{cpt_rows} ligne(s) lue(s).")
            if get_timer():
                elapsed_time = timeit.default_timer() - timer_start
                self.logger.info(f"Temps d'exécution de sqlQuery: {elapsed_time:.4f} secondes")
        except Exception as e:
            self.logger.error(f"Échec de la lecture des données: {e}")
            raise

    @timer
    def sqlExec(self, query):
        """
        execute une requête sur la base de données, un create ou delete table par exemple
        :param query: la requête
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.connection.commit()
                self.logger.info(f"Requête exécutée avec succès.")
        except Exception as e:
            self.logger.error(f"Échec de l'exécution de la requête: {e}")
            raise

    @timer
    def sqlScalaire(self, query):
        """
        execute une requête et retourne le premier résultat
        :param query: la requête
        :return: le résultat de la requête
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                self.logger.info(f"Requête scalaire exécutée avec succès.")
                return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Échec de l'exécution de la requête: {e}")
            raise

    @staticmethod
    def __escape_value(value):
        if isinstance(value, str):
            return value.replace('"', '""').replace("'", "''")
        return value

    @timer
    def insert(self, schema: str, table: str, cols: [], row: []):
        """
        Insère des données dans la base de données
        :param schema: Nom du schéma dans lequel est la table
        :param table: Nom de la table dans laquelle insérer
        :param cols: liste des colonnes dans lesquelles insérer
        :param row: liste des valeurs à insérer
        :return: le résultat de l'opération, l'erreur et la la ligne concernée en cas d'erreur
        """
        placeholders = ", ".join(["%s"] * len(cols))
        table = f"{schema}.{table}" if schema else table
        query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        row = [self.__escape_value(value) for value in row]
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeur(s) insérée(s) avec succès dans la table {table}")
                return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Échec de l'insertion des données: {e}")
            return "ERROR", str(e), row

    @timer
    def insertMany(self, schema: str, table: str, cols: [], rows: [[]]):
        """
        Insère des données par batch dans une table avec gestion des erreurs

        :param schema: Nom du schéma dans lequel se trouve la table
        :param table: Nom de la table dans laquelle insérer
        :param cols: Liste des colonnes dans lesquelles insérer
        :param rows: Liste des lignes à insérer
        :return: Le résultat de l'opération, l'erreur et la le batch concerné en cas d'erreur
        """
        failed_batches = []
        errors = []
        total_inserted = 0
        placeholders = ', '.join(["%s"] * len(cols))
        table = f"{schema}.{table}" if schema else table
        query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        rows = [[self.__escape_value(value) for value in row] for row in rows]
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, len(rows), self.batch_size), start=1):
                    batch = rows[start: start + self.batch_size]
                    try:
                        cursor.executemany(query, batch)
                        self.connection.commit()
                        total_inserted += len(batch)
                        self.logger.info(
                            f"Batch {batch_index}: {len(batch)} ligne(s) insérée(s) avec succès dans la table {table}. "
                            f"Total inséré: {total_inserted}/{len(rows)} ligne(s)."
                        )
                    except Exception as batch_error:
                        self.connection.rollback()
                        self.logger.error(f"Erreur lors de l'insertion du batch {batch_index}: {batch_error}")
                        failed_batches.append(batch)
                        errors.append(str(batch_error))
                return ("ERROR" if failed_batches else "SUCCESS"), errors, failed_batches
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'insertion des données: {e}")
            return "ERROR", str(e), rows

    def __get_df(self, rows, cols):
        if isinstance(rows, list):
            df = pl.DataFrame(rows, schema=cols, orient='row', infer_schema_length=len(rows))
        elif isinstance(rows, pl.DataFrame):
            df = rows
        else:
            raise ValueError("Les données doivent être une liste de tuples ou un DataFrame polars")
        return df

    @timer
    def insertBulk(self, schema: str, table: str, cols: [], rows):
        """
        Insère des données dans une table en bulk, en lots

        :param schema: Nom du schéma
        :param table: Nom de la table dans laquelle insérer
        :param cols: Liste des colonnes dans lesquelles insérer
        :param rows: Liste des lignes à insérer
        :return: Le résultat de l'opération, l'erreur et la le batch concerné en cas d'erreur
        """
        import json
        import datetime
        failed_batches = []
        errors = []
        total_inserted = 0
        table_full = f"{schema}.{table}" if schema else table
        df = self.__get_df(rows, cols)
        type_mapping = {}
        for col in cols:
            non_null_values = df[col].drop_nulls()
            sample_value = non_null_values[0] if len(non_null_values) > 0 else 0
            type_mapping[col] = (
                "DATETIME2" if isinstance(sample_value, datetime.date)
                else "TIME(3)" if isinstance(sample_value, datetime.time)
                else "NVARCHAR(MAX)"
            )
        col_defs = ", ".join([f"[{col}]" for col in cols])
        openjson_defs = ", ".join([f"[{col}] {type_mapping[col]} '$.{col}'" for col in cols])
        query = f"""
        INSERT INTO {table_full} ({col_defs})
        SELECT {col_defs}
        FROM OPENJSON(%s)
        WITH ({openjson_defs});
        """
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, df.height, self.batch_size), start=1):
                    batch = df.slice(start, self.batch_size)
                    try:
                        as_json = [row for row in batch.iter_rows(named=True)]
                        json_data = json.dumps(as_json, default=str)
                        cursor.execute(query, (json_data,))
                        self.connection.commit()
                        total_inserted += len(batch)
                        self.logger.info(
                            f"Batch {batch_index}: {len(batch)} ligne(s) insérée(s) avec succès dans la table {table_full}. "
                            f"Total inséré: {total_inserted}/{len(rows)} ligne(s)."
                        )
                    except Exception as batch_error:
                        self.connection.rollback()
                        self.logger.error(f"Erreur lors de l'insertion du batch {batch_index}: {batch_error}")
                        failed_batches.append(batch)
                        errors.append(str(batch_error))
            return ("ERROR" if failed_batches else "SUCCESS"), errors, failed_batches
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'insertion des données: {e}")
            return "ERROR", str(e), rows

    @timer
    def upsert(self, schema :str, table: str, cols: [], row: [], conflict_cols: []):
        """
        Réalise une opération upsert sur la base
        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param row: Liste des valeurs à insérer
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits
        :return: Le résultat de l'opération, l'erreur et la ligne en cas d'erreur
        """
        table = f"{schema}.{table}" if schema else table
        target_cols = ', '.join(cols)
        source_cols = ', '.join([f"source.{col}" for col in cols])
        update_clause = ', '.join([f"target.{col} = source.{col}" for col in cols if col not in conflict_cols])
        conflict_cdt = ' AND '.join([f"target.{col} = source.{col}" for col in conflict_cols])
        query = f"""
        MERGE INTO {table} AS target
        USING (VALUES ({', '.join(['%s'] * len(cols))})) AS source ({', '.join(cols)})
        ON {conflict_cdt}
        WHEN MATCHED THEN
            UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN
            INSERT ({target_cols})
            VALUES ({source_cols});"""
        row = [self.__escape_value(value) for value in row]
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeur(s) insérée(s) ou mise(s) à jour dans la table {table}.")
                return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur lors de l'upsert dans la table {table}.")
            return "ERROR", str(e), row

    @timer
    def upsertMany(self, schema: str, table: str, cols: [], rows: [[]], conflict_cols: []):
        """
        Réalise une opération upsert par batch sur la base
        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param rows: Liste des lignes à insérer
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits
        :return: Le résultat de l'opération, l'erreur et le batch en cas d'erreur
        """
        failed_batches = []
        errors = []
        total_inserted = 0
        table = f"{schema}.{table}" if schema else table
        target_cols = ', '.join(cols)
        source_cols = ', '.join([f"source.{col}" for col in cols])
        update_clause = ', '.join([f"target.{col} = source.{col}" for col in cols if cols not in conflict_cols])
        conflict_cdt = ' AND '.join([f"target.{col} = source.{col}" for col in conflict_cols])
        query = f"""
        MERGE INTO {table} AS target
        USING (VALUES ({', '.join(['%s'] * len(cols))})) AS source ({', '.join(cols)})
        ON {conflict_cdt}
        WHEN MATCHED THEN
            UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN
            INSERT ({target_cols})
            VALUES ({source_cols});"""
        rows = [[self.__escape_value(value) for value in row] for row in rows]
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, len(rows), self.batch_size), start=1):
                    batch = rows[start: start + self.batch_size]
                    try:
                        cursor.executemany(query, batch)
                        self.connection.commit()
                        total_inserted += len(batch)
                        self.logger.info(
                            f"Batch {batch_index}: {len(batch)} ligne(s) insérée(s) ou mise(s) à jour dans la table {table}. "
                            f"Total inséré ou mis à jour: {total_inserted}/{len(rows)} ligne(s)."
                        )
                    except Exception as batch_error:
                        self.connection.rollback()
                        self.logger.error(f"Erreur lors de l'upsert du batch {batch_index}: {batch_error}")
                        failed_batches.append(batch)
                        errors.append(str(batch_error))
                return ("ERROR" if failed_batches else "SUCCESS"), errors, failed_batches
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'upsert des données: {e}")
            return "ERROR", str(e), rows

    def __create_temp_table(self, schema: str, table: str, temp_table: str, cols: []):
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table}'
        """
        self.logger.info(f"Récupération des colonnes depuis {schema}.{table}")
        column_definitions = list(self.sqlQuery(query))[0]
        col_def = []
        for col in cols:
            col_info = next((c for c in column_definitions if c[0] == col), None)
            if col_info:
                col_name, data_type, char_length = col_info
                if char_length:
                    col_def.append(f"{col_name} {data_type.upper()}({char_length})")
                else:
                    col_def.append(f"{col_name} {data_type.upper()}")
            else:
                raise ValueError(f"Column {col} not found in {schema}.{table}")
        col_def_sql = ', '.join(col_def)
        self.sqlExec(f"DROP TABLE IF EXISTS {schema}.{temp_table}")
        self.sqlExec(f"CREATE TABLE {schema}.{temp_table} ({col_def_sql})")

    @timer
    def upsertBulk(self, schema: str, table: str, cols: [], rows, conflict_cols):
        """
        Réalise une opération upsert en bulk par batch sur la base en lots et avec l'aide d'une table temporaire
        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param rows: Liste des lignes à insérer
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits
        :return: Le résultat de l'opération, l'erreur et le batch en cas d'erreur
        """
        temp_table = f"{table}_temp"
        table_full = f"{schema}.{table}" if schema else table
        conflict_cdt = ' AND '.join([f"target.{col} = source.{col}" for col in conflict_cols])
        update_clause = ', '.join([f"target.{col} = source.{col}" for col in cols if col not in conflict_cols])
        target_cols = ', '.join(cols)
        source_cols = ', '.join([f"source.{col}" for col in cols])
        query = f"""
        MERGE INTO {table_full} AS target
        USING {temp_table} AS source
        ON {conflict_cdt}
        WHEN MATCHED THEN
            UPDATE SET {update_clause}
        WHEN NOT MATCHED THEN
            INSERT ({target_cols})
            VALUES ({source_cols});
        """
        try:
            self.__create_temp_table(schema, table, temp_table, cols)
            result, errors, failed_batches = self.insertBulk(schema, temp_table, cols, rows)
            if result == "ERROR":
                return result, errors, failed_batches
            self.sqlExec(query)
            self.logger.info(f"{len(rows)} lignes insérée(s) ou mise(s) à jour dans la tables {table}.")
            return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'UPSERT: {e}")
            return "ERROR", str(e), rows
        finally:
            self.sqlExec(f"DROP TABLE IF EXISTS {schema}.{temp_table}")
            self.logger.info(f"Table temporaire supprimée.")

    @timer
    def find_text_anywhere(self, search: str, include_views: bool = False, schema: str = None, table: str = None, log_every: int = 50):
        """
        Recherche une valeur textuelle dans toutes les colonnes textuelles de toutes les tables
        (et éventuellement vues) de tous les schémas.

        :param search: Texte à rechercher
        :param include_views: Inclure les vues dans la recherche (False par défaut)
        :param schema: Filtrer sur un schéma particulier
        :param table: Filtrer sur une table particulière
        :param log_every: Log de progression toutes les N colonnes
        """
        results = []
        base_sql = """
        SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS c
        INNER JOIN INFORMATION_SCHEMA.TABLES t
            ON c.TABLE_SCHEMA = t.TABLE_SCHEMA
            AND c.TABLE_NAME = t.TABLE_NAME
        WHERE c.DATA_TYPE IN ('char', 'varchar', 'nvarchar', 'text', 'ntext')
        """
        if not include_views:
            base_sql += " AND t.TABLE_TYPE = 'BASE TABLE'"
        if schema:
            base_sql += " AND c.TABLE_SCHEMA = %s"
        if table:
            base_sql += " AND c.TABLE_NAME = %s"
        params = []
        if schema:
            params.append(schema)
        if table:
            params.append(table)
        try:
            with self.connection.cursor() as cursor:
                self.logger.debug("Début de la recherche...")
                cursor.execute(base_sql, params)
                cols = cursor.fetchall()
                if not cols:
                    self.logger.warning("Aucune colonne trouvée correspondant aux critères.")
                    return results
                total = len(cols)
                total_tables = len(set((s, t) for s, t, _ in cols))
                total_schemas = len(set(s for s, _, _ in cols))
                self.logger.info(f"Analyse de {total} colonne(s) répartie(s) sur {total_tables} table(s) et {total_schemas} schéma(s)...")
                for i, (schema_name, table_name, column) in enumerate(cols, start=1):
                    full_table = f"[{schema_name}].[{table_name}]"
                    query = f"SELECT COUNT(*) FROM {full_table} WHERE [{column}] LIKE %s"
                    if i % log_every == 0 or i == total:
                        self.logger.debug(f"[{i}/{total}] Vérification de {full_table}.{column}")
                    try:
                        cursor.execute(query, (search,))
                        count = cursor.fetchone()[0]
                        if count > 0:
                            select_query = f"SELECT * FROM {full_table} WHERE [{column}] LIKE '{search}'"
                            results.append({
                                "schema": schema_name,
                                "table": table_name,
                                "column": column,
                                "count": count,
                                "query": select_query
                            })
                            self.logger.info(f"{count} ligne(s) trouvée(s) dans {full_table}.{column}")
                    except Exception as e:
                        self.logger.error(f"Erreur sur {full_table}.{column}: {e}")
            return results
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche du champ {search}: {e}")
            raise