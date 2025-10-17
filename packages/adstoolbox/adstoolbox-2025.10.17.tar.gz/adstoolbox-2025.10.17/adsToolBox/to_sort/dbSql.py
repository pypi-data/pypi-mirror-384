class dbSql:
    def __init__(self, dictionnary: dict, logger, batch_size=10_000):
        """
        instancie la classe dbSql, qui permet la communication avec une base de données
        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion MySQL
        :param logger: Un logger ads qui va gérer les logs des actions de la classe
        :param batch_size: La taille des batchs en lecture et écriture
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
        self.__package = dictionnary.get('package', 'pymssql')