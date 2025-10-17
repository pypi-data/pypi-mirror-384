from abc import ABC, abstractmethod

class Reader(ABC):
    """
    Interface de base pour la lecture des données depuis une connexion.
    """
    def __init__(self, connection):
        """
        Initialise le Reader avec une connexion donnée.
        :param connection: Instance de la classe Connection utilisée pour accéder aux données.
        """
        self.connection = connection

    @abstractmethod
    def read(self, query_or_path: str, batch_size: int = None):
        """
        Lit les données depuis la ressource.
        :param query_or_path: Requête SQL ou chemin de fichier.
        :param batch_size: Taille des données à lire par lot (None pour tout lire).
        :return: Données lues (liste, DataFrame, etc.).
        """
        pass