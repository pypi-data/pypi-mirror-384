import pymssql
import psycopg2
import os
import pymysql
import timeit
import polars as pl

from io import StringIO

from .timer import timer, get_timer
from .dataFactory import data_factory

class dbSql(data_factory):
    def __init__(self, dictionnary: dict, logger, batch_size=10_000):
       """
       instancie la classe dbSql, qui hérite de dataFactory
       :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion sql server
       :param logger: un logger ads qui va gérer les logs des actions de la classe
       :param batch_size: la taille des batchs en lecture et écriture
       :param package: le package à utiliser ('pymssql' qui gère les connexion encryptées mais qui encode mal des
           caractères spéciaux en bulk ou alors 'pytds' qui est moins permissif et ne gère pas les connexion encryptées
           mais n'encode pas mal les caractères spéciaux
       """
       self.connection = None
       self.logger = logger
       self.__techno = dictionnary.get('techno')
       self.__database = dictionnary.get('database')
       self.__user = dictionnary.get('user')
       self.__password = dictionnary.get('password')
       self.__port = dictionnary.get('port')
       self.__host = dictionnary.get('host')
       self.__charset = dictionnary.get('charset', 'UTF-8')
       self.batch_size = batch_size

    def __connect_mssql(self):
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
            if self.logger is not None: self.logger.info("Connexion établie avec la base de données.")
            return self.connection
        except Exception as e:
            if self.logger is not None: self.logger.error(f"Échec de la connexion à la base de données: {e}")
            raise

    def __connect_pg(self):
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

    def __connect_mysql(self, additionnal_parameters=None):
        if self.logger is not None: self.logger.info("Tentative de connexion avec la base de données.")
        try:
            self.connection = pymysql.connect(
                host=self.__host,
                port=int(self.__port),
                user=self.__user,
                password=self.__password,
                database=self.__database,
                autocommit=False,
                local_infile=True
            )
            if additionnal_parameters:
                cursor = self.connection.cursor()
                for param, value in additionnal_parameters.items():
                    cursor.execute(f"SET SESSION {param} = {value}")
                self.connection.commit()
            if self.logger is not None: self.logger.info("Connexion établie avec la base de données.")
            return self.connection
        except Exception as e:
            if self.logger is not None: self.logger.error(f"Échec de la connexion à la base de données: {e}")
            raise

    @timer
    def connect(self):
        """
        lance la connexion avec les identifiants passés à l'initialisation de la classe
        toutes les méthodes de la classe nécéssitent une connexion active
        :return: la connexion
        """
        if self.__techno == "mssql":
            connexion = self.__connect_mssql()
        elif self.__techno == "postgresql":
            connexion = self.__connect_pg()
        elif self.__techno == "mysql":
            connexion = self.__connect_mysql()
        else:
            msg = f"La connexion {self.__techno} n'est pas supportée. Tentez avec 'mssql', 'postgresql' ou 'mysql'"
            self.logger.error(msg)
            raise ValueError(msg)
        return connexion

    @timer
    def sqlQuery(self, query):
        """
        lit la base de données avec la requête query
        :param query: la requête
        :return: les données lues avec yield
        """
        self.logger.debug(f"Exécution de la requête de lecture : {query}")
        try:
            timer_start = timeit.default_timer()
            cpt_rows = 0
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                self.logger.info("Requête exécutée avec succès, début de la lecture des résultats.")
                while True:
                    rows = cursor.fetchmany(self.batch_size)
                    if not rows:
                        break
                    yield rows
                    cpt_rows += len(rows)
                    self.logger.info(f"{cpt_rows} ligne(s) lue(s).")
            if get_timer():
                elapsed_time = timeit.default_timer() - timer_start
                self.logger.info(f"Temps d'exécution de sqlQuery: {elapsed_time:.4f} secondes")
            return cpt_rows
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
            df = pl.DataFrame(rows, schema=cols, orient='row', infer_schema_length=10_000)
        elif isinstance(rows, pl.DataFrame):
            df = rows
        else:
            raise ValueError("Les données doivent être une liste de tuples ou un DataFrame polars")
        return df

    def __insertBulk_mssql(self, schema: str, table: str, cols: [], rows):
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
            if len(non_null_values) > 0:
                sample_value = non_null_values[0]
            else:
                sample_value = 0
            if isinstance(sample_value, datetime.date):
                type_mapping[col] = "DATETIME2"
            elif isinstance(sample_value, datetime.time):
                type_mapping[col] = "TIME(3)"
            else:
                type_mapping[col] = "NVARCHAR(MAX)"
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

    def __insertBulk_pg(self, schema: str, table: str, cols: [], rows):
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

    def __insertBulk_mysql(self, schema: str, table: str, cols: [], rows):
        failed_batches = []
        errors = []
        total_inserted = 0
        table_full = f"{schema}.{table}" if schema else table
        temp_file = "temp_bulk_insert.csv"
        query = f"""
        LOAD DATA LOCAL INFILE '{temp_file}'
        INTO TABLE {table_full}
        FIELDS TERMINATED BY ','
        LINES TERMINATED BY '\n'
        ({', '.join(cols)})
        """
        try:
            df = self.__get_df(rows, cols)
            n_rows = df.shape[0]
            with self.connection.cursor() as cursor:
                for batch_index, start in enumerate(range(0, n_rows, self.batch_size), start=1):
                    batch = df.slice(start, self.batch_size)
                    try:
                        batch.write_csv(temp_file, include_header=False)
                        cursor.execute(query)
                        self.connection.commit()
                        os.remove(temp_file)
                        total_inserted += batch.shape[0]
                        self.logger.info(
                            f"Batch {batch_index}: {batch.shape[0]} ligne(s) insérée(s) avec succès dans la table {table_full}. "
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
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

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
        if self.__techno == "mssql":
            result, errors, failed_batches = self.__insertBulk_mssql(schema, table, cols, rows)
        elif self.__techno == "postgresql":
            result, errors, failed_batches = self.__insertBulk_pg(schema, table, cols, rows)
        elif self.__techno == "mysql":
            result, errors, failed_batches = self.__insertBulk_mysql(schema, table, cols, rows)
        else:
            msg = f"La connexion {self.__techno} n'est pas supportée. Tentez avec 'mssql', 'postgresql' ou 'mysql'"
            self.logger.error(msg)
            raise ValueError(msg)
        return result, errors, failed_batches

    def __upsert_mssql(self, schema: str, table: str, cols: [], row: [], conflict_cols: []):
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

    def __upsert_pg(self, schema: str, table: str, cols: [], row: [], conflict_cols: []):
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

    def __upsert_mysql(self, schema: str, table: str, cols: [], row: [], conflict_cols: []):
        table_full = f"{schema}.{table}" if schema else table
        columns = ', '.join([f"'{col}'" for col in cols])
        placeholders = ', '.join(['%s'] * len(cols))
        update_clause = ', '.join([f"'{col}' = VALUES('{col}')" for col in cols if col not in conflict_cols])
        query = f"""
        INSERT INTO {table_full} ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause};
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, row)
                self.connection.commit()
                self.logger.info(f"{len(row)} valeurs insérée(s) ou mise(s) à jour dans la table {table_full}.")
                return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur lors de l'upsert dans la table {table}.")
            return "ERROR", str(e), row

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
        if self.__techno == "mssql":
            result, errors, failed_batches = self.__upsert_mssql(schema, table, cols, row, conflict_cols)
        elif self.__techno == "postgresql":
            result, errors, failed_batches = self.__upsert_pg(schema, table, cols, row, conflict_cols)
        elif self.__techno == "mysql":
            result, errors, failed_batches = self.__upsert_mysql(schema, table, cols, row, conflict_cols)
        else:
            msg = f"La connexion {self.__techno} n'est pas supportée. Tentez avec 'mssql', 'postgresql' ou 'mysql'"
            self.logger.error(msg)
            raise ValueError(msg)
        return result, errors, failed_batches

    def __upsertMany_mssql(self, schema: str, table: str, cols: [], rows: [[]], conflict_cols: []):
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

    def __upsertMany_pg(self, schema: str, table: str, cols: [], rows: [[]], conflict_cols: []):
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

    def __upsertMany_mysql(self, schema: str, table: str, cols: [], rows: [[]], conflict_cols: []):
        failed_batches = []
        errors = []
        total_inserted = 0
        table_full = f"{schema}.{table}" if schema else table
        columns = ', '.join([f"'{col}'" for col in cols])
        placeholders = ', '.join(['%s'] * len(cols))
        update_clause = ', '.join([f"'{col}' = VALUES('{col}')" for col in cols if col not in conflict_cols])
        query = f"""
        INSERT INTO {table_full} ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause};
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
        if self.__techno == "mssql":
            result, errors, failed_batches = self.__upsertMany_mssql(schema, table, cols, rows, conflict_cols)
        elif self.__techno == "postgresql":
            result, errors, failed_batches = self.__upsertMany_pg(schema, table, cols, rows, conflict_cols)
        elif self.__techno == "mysql":
            result, errors, failed_batches = self.__upsertMany_mysql(schema, table, cols, rows, conflict_cols)
        else:
            msg = f"La connexion {self.__techno} n'est pas supportée. Tentez avec 'mssql', 'postgresql' ou 'mysql'"
            self.logger.error(msg)
            raise ValueError(msg)
        return result, errors, failed_batches

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

    def __upsertBulk_mssql(self, schema: str, table: str, cols: [], rows, conflict_cols):
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
            self.logger.info(f"{len(rows)} ligne(s) insérée(s) ou mise(s) à jour dans la tables {table}.")
            return "SUCCESS", [], []
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Erreur critique lors de l'UPSERT: {e}")
            return "ERROR", str(e), rows
        finally:
            self.sqlExec(f"DROP TABLE IF EXISTS {schema}.{temp_table}")
            self.logger.info(f"Table temporaire supprimée.")

    def __upsertBulk_pg(self, schema: str, table: str, cols: [], rows, conflict_cols: []):
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

    def __upsertBulk_mysql(self, schema: str, table: str, cols: [], rows, conflict_cols: []):
        temp_table = f"{table}_temp"
        table_full, temp_table_full = (f"{schema}.{table}", f"{schema}.{temp_table}") if schema else (table, temp_table)
        columns = ', '.join(cols)
        update_clause = ', '.join([f"{col} = VALUES({col})" for col in cols if col not in conflict_cols])
        query = f"""
        INSERT INTO {table_full} ({columns})
        SELECT {columns} FROM {temp_table_full}
        ON DUPLICATE KEY UPDATE {update_clause};
        """
        try:
            self.sqlExec(f"CREATE TEMPORARY TABLE {temp_table_full} LIKE {table_full}")
            self.logger.info(f"Table temporaire {temp_table_full} créée.")
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
            self.sqlExec(f"DROP TEMPORARY TABLE IF EXISTS {temp_table_full}")
            self.logger.info(f"Table temporaire {temp_table_full} supprimée.")

    @timer
    def upsertBulk(self, schema: str, table: str, cols: [], rows, conflict_cols: []):
        """
        Réalise une opération upsert en bulk par batch sur la base en lots et avec l'aide d'une table temporaire
        :param schema: Le schéma de la table
        :param table: Le nom de la table
        :param cols: Liste des colonnes dans lequelles insérer
        :param rows: Liste des lignes à insérer
        :param conflict_cols: Colonnes à utiliser pour détecter les conflits
        :return: Le résultat de l'opération, l'erreur et le batch en cas d'erreur
        """
        if self.__techno == "mssql":
            result, errors, failed_batches = self.__upsertBulk_mssql(schema, table, cols, rows, conflict_cols)
        elif self.__techno == "postgresql":
            result, errors, failed_batches = self.__upsertBulk_pg(schema, table, cols, rows, conflict_cols)
        elif self.__techno == "mysql":
            result, errors, failed_batches = self.__upsertBulk_mysql(schema, table, cols, rows, conflict_cols)
        else:
            msg = f"La connexion {self.__techno} n'est pas supportée. Tentez avec 'mssql', 'postgresql' ou 'mysql'"
            self.logger.error(msg)
            raise ValueError(msg)
        return result, errors, failed_batches