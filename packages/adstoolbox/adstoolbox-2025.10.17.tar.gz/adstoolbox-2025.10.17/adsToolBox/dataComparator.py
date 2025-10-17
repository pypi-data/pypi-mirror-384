import polars as pl
from .timer import timer
from .logger import Logger
from polars.testing import assert_frame_equal

class DataComparator:
    def __init__(self, dictionnary: dict, logger: Logger):
        """
        Initialise un dataComparator avec les informations de connexions aux bases de données
        :param dictionnary: le dictionnaire qui contient les informations du pipeline
            - 'db_source_1': la base de données source 1
            - 'query_source_1': la requête à envoyer à la source 1
            - 'db_source_2': la base de données source 2
            - 'query_source_2': la requête à envoyer à la source 2
            - 'batch_size': la taille des lots pour le traitement en batch
        :param logger: le logger pour gérer la journalisation des évènements du pipeline
        """
        self.logger = logger
        self.__db_source_1 = dictionnary.get('db_source_1')
        self.__query_source_1 = dictionnary.get('query_source_1')
        self.__db_source_2 = dictionnary.get('db_source_2')
        self.__query_source_2 = dictionnary.get('query_source_2')
        self.__batch_size = dictionnary.get('batch_size', 10_000)

    def _fetch_data(self, db, query):
        """
        Exécute la requête donnée sur la base spécifiée et retourne un DataFrame Polars
        :param db: la base sur laquelle envoyer la requête
        :param query: la requête à envoyer
        :return: le résultat de la requête sous forme de DataFrame
        """
        db.connect()
        data = list(db.sqlQuery(query))[0]
        return pl.DataFrame(data, orient='row', strict=False, infer_schema_length=10_000)

    @timer
    def compare(self):
        """
        Compare les résultats des deux requêtes SQL entre les deux bases de données.
        :return: Un dictionnaire contenant les différences si elles existent
        """
        try:
            data_1 = self._fetch_data(self.__db_source_1, self.__query_source_1)
            data_2 = self._fetch_data(self.__db_source_2, self.__query_source_2)
            assert_frame_equal(data_1, data_2)
        except Exception as e:
            self.logger.error(f"Erreur lors de la comparaison des données: {e}")
            raise
