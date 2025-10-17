import psycopg2
import timeit
import polars as pl
from io import StringIO
from .timer import timer, get_timer
from .dataFactory import data_factory

class dbPgsql(data_factory):
    def __init__(self, dictionnary: dict, logger, batch_size=10_000):
        """
        instancie la classe dbMssql, qui hérite de dataFactory
        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion postgre
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
            self.connection = psycopg2.connect(
                database=self.__database,
                user=self.__user,
                password=self.__password,
                port=self.__port,
                host=self.__host
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
        self.logger.debug(f"Exécution de la requête de lecture: {query}")
        try:
            timer_start = timeit.default_timer()
            cpt_rows = 0
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                if return_columns:
                    cols = [desc for desc in cursor.description]
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
                data = result[0] if result else None
                return data
        except Exception as e:
            self.logger.error(f"Échec de l'exécution de la requête: {e}")
            raise

    @timer
    def insert(self, schema: str, table: str, cols: [], row: []):
        """
        Insère des données dans la base de données
        :param schema: Nom du schema dans lequel est la table
        :param table: nom de la table dans laquelle insérer
        :param cols: liste des colonnes dans lesquelles insérer
        :param row: liste des valeurs à insérer
        :return: le résultat de l'opération, l'erreur et la ligne
        """
        placeholders = ', '.join(["%s"] * len(cols))
        table = f"{schema}.{table}" if schema else table
        query = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeur(s) insérée(s) avec succès dans la table {table}.")
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
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, len(rows), self.batch_size), start=1):
                    batch = rows[start: start + self.batch_size]
                    try:
                        cursor.executemany(query, batch)
                        self.connection.commit()
                        total_inserted += len(batch)
                        self.logger.info(f"Batch {batch_index}: {len(batch)} ligne(s) insérée(s) avec succès dans la table {table}. "
                                         f"Total inséré: {total_inserted}/{len(rows)} ligne(s).")
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
        Insère des données dans une table avec la méthode rapide COPY (via copy_expert), en lots pour éviter les erreurs critiques.

        :param schema: Nom du schéma
        :param table: Nom de la table dans laquelle insérer
        :param cols: Liste des colonnes dans lesquelles insérer
        :param rows: Liste des lignes à insérer
        :return: Le résultat de l'opération, l'erreur et la le batch concerné en cas d'erreur
        """
        failed_batches = []
        errors = []
        total_inserted = 0
        try:
            df = self.__get_df(rows, cols)
            table = f"{schema}.{table}" if schema else table
            n_rows = df.shape[0]
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, n_rows, self.batch_size), start=1):
                    batch = df.slice(start, self.batch_size)
                    try:
                        buffer = StringIO()
                        batch.write_csv(buffer, include_header=False)
                        buffer.seek(0)
                        columns = ', '.join(cols)
                        query = f"COPY {table} ({columns}) FROM STDIN WITH CSV DELIMITER ','"
                        cursor.copy_expert(query, buffer)
                        self.connection.commit()
                        buffer.close()
                        total_inserted += batch.shape[0]
                        self.logger.info(f"Batch {batch_index}: {batch.shape[0]} ligne(s) insérée(s) avec succès dans la table {table}. "
                                         f"Total inséré: {total_inserted}/{n_rows} ligne(s).")
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
    def upsert(self, schema: str, table: str, cols: [], row: [], conflict_cols: []):
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
        placeholders = ', '.join(["%s"] * len(cols))
        conflict_clause = ', '.join(conflict_cols)
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_cols])
        query = f"""
        INSERT INTO {table} ({', '.join(cols)})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_clause}) DO UPDATE
        SET {update_clause};
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeurs insérée(s) ou mise(s) à jour dans la table {table}.")
                return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur lors de l'upsert dans la table {table}: {e}")
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
        placeholders = ', '.join(["%s"] * len(cols))
        conflict_clause = ', '.join(conflict_cols)
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_cols])
        query = f"""
        INSERT INTO {table} ({', '.join(cols)})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_clause}) DO UPDATE
        SET {update_clause};
        """
        try:
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, len(rows), self.batch_size), start=1):
                    batch = rows[start: start + self.batch_size]
                    try:
                        cursor.executemany(query, batch)
                        self.connection.commit()
                        total_inserted += len(batch)
                        self.logger.info(
                            f"Batch {batch_index}: {len(batch)} ligne(s) insérées ou mises à jour dans la table {table}. "
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

    @timer
    def upsertBulk(self, schema: str, table: str, cols: [], rows, conflict_cols: []):
        """
        Réalise une opération upsert par batch sur la base avec copy_expert, en lots et avec l'aide d'une table temporaire
        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param rows: Liste des lignes à insérer
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits
        :return: Le résultat de l'opération, l'erreur et le batch en cas d'erreur
        """
        temp_table = f"{table}_temp"
        table_full, temp_table_full = (f"{schema}.{table}", f"{schema}.{temp_table}") if schema else (table, temp_table)
        conflict_clause = ', '.join(conflict_cols)
        update_clause = ', '.join([f"{col} = EXCLUDED.{col}" for col in cols if col not in conflict_cols])
        query = f"""
        INSERT INTO {table_full} ({', '.join(cols)})
        SELECT {', '.join(cols)} FROM {temp_table_full}
        ON CONFLICT ({conflict_clause}) DO UPDATE
        SET {update_clause};
        """
        try:
            self.sqlExec(f"CREATE TEMP TABLE {temp_table_full} (LIKE {table_full} INCLUDING DEFAULTS)")
            result, errors, failed_batches = self.insertBulk(schema, temp_table, cols, rows)
            if result == "ERROR":
                return result, errors, failed_batches
            self.sqlExec(query)
            self.logger.info(f"{len(rows)} lignes insérée(s) ou mise(s) à jour dans la table {table}.")
            return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'UPSERT : {e}")
            return "ERROR", str(e), rows
        finally:
            self.sqlExec(f"DROP TABLE IF EXISTS {temp_table_full}")
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
        SELECT c.table_schema, c.table_name, c.column_name
        FROM information_schema.columns c
        INNER JOIN information_schema.tables t
            ON c.table_schema = t.table_schema
            AND c.table_name = t.table_name
        WHERE c.data_type IN ('character varying', 'character', 'text')
        """
        params = []
        if not include_views:
            base_sql += " AND t.table_type = 'BASE TABLE'"
        if schema:
            base_sql += " AND c.table_schema = %s"
            params.append(schema)
        if table:
            base_sql += " AND c.table_name = %s"
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
                for i, (schema, table, column) in enumerate(cols, start=1):
                    full_table = f'{schema}.{table}'
                    query = f'SELECT COUNT(*) FROM {full_table} WHERE "{column}" ILIKE %s'
                    if i % log_every == 0 or i == total:
                        self.logger.debug(f"[{i}/{total}] Vérification de {full_table}.{column}")
                    try:
                        cursor.execute(query, (search,))
                        count = cursor.fetchone()[0]
                        if count > 0:
                            select_query = f'SELECT * FROM {full_table} WHERE "{column}" ILIKE \'{search}\''
                            results.append({
                                "schema": schema,
                                "table": table,
                                "column": column,
                                "count": count,
                                "query": select_query
                            })
                            self.logger.info(f"{count} ligne(s) trouvée(s) dans {full_table}.{column}")
                    except Exception as e:
                        self.logger.error(f"Erreur sur {full_table}.{column}: {e}")
            return results
        except Exception as e:
            self.logger.error(f'Erreur lors de la recherche du champ {search}: {e}')
            raise