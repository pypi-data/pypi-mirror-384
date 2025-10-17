from abc import ABC, abstractmethod

class data_factory(ABC):
    """Classe abstraite qui pose un modèle de connexion ads"""
    @abstractmethod
    def connect(self):
        """Lance la connexion avec les identifiants passés à l'initialisation de la classe"""
        pass

    @abstractmethod
    def insert(self, schema: str, table: str, cols: [], row: []):
        """
        Insère des données dans la base de données, nécessite une connexion active
        :param schema: nom du schéma dans lequel insérer
        :param table: nom de la table dans laquelle insérer
        :param cols: liste des colonnes dans lesquelles insérer
        :param row: liste des valeurs à insérer
        """
        pass

    @abstractmethod
    def insertBulk(self, schema: str, table: str, cols: [], rows):
        """
        Similaire à insert classique, mais insère par batch de taille 'batch_size' définie
        :param schema: nom du schéma dans lequel insérer
        :param table: nom de la table dans laquelle insérer
        :param cols: liste des colonnes dans lesquelles insérer
        :param rows: liste des lignes à insérer
        """
        pass

    @abstractmethod
    def sqlQuery(self, query: str, return_columns: bool = False):
        """
        Lit la base de données avec la requête query
        :param return_columns: le premier élément retourné sera la liste des colonnes
        :param query: la requête
        :return: un générateur de liste de tuples
        """
        pass

    @abstractmethod
    def sqlExec(self, query):
        """
        Execute une requête sur la base de données
        :param query: la requête
        """
        pass