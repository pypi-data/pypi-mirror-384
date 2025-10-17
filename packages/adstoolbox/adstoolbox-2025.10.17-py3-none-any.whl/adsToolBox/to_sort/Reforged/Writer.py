from abc import ABC, abstractmethod

class Writer(ABC):
    """
    Interface de base pour écrire des données dans une ressource.
    """
    def __init__(self, connection):
        """
        Initialise le Writer avec une connexion donnée.
        :param connection: Instance de la classe Connection utilisée pour accéder à la ressource.
        """
        self.connection = connection

    @abstractmethod
    def write(self, data, mode: str = "insert", batch_size: int = None, if_exists: str = "none",
              if_not_exists: str = "fail"):
        """
        Écrit des données dans la ressource.
        :param data: Données à écrire (liste de tuples, DataFrame, etc.).
        :param mode: Mode d'écriture (insert, update, delete, etc.).
        :param batch_size: Taille des données à écrire par lot (None pour tout écrire d'un coup).
        :param if_exists: Action si la ressource existe (deleteAndCreate, deleteRows, truncate, fail, none, syncSchema).
        :param if_not_exists: Action si la ressource n'existe pas (create, fail).
        """
        pass