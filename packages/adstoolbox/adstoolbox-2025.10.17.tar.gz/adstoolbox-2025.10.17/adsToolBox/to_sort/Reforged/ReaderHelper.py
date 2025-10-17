from abc import ABC, abstractmethod

class ReaderHelper(ABC):
    """
    Interface pour aider à paramétrer un Reader.
    """
    def __init__(self, connection):
        """
        Initialise le ReaderHelper avec une connexion donnée.
        :param connection: Instance de la classe connection utilisée pour accèder aux données.
        """
        self.connection = connection

    @abstractmethod
    def get_columns(self, source: str):
        """
        Récupère les colonnes disponibles dans la source (table, fichier...).
        :param source: Requête SQL ou chemin du fichier.
        :return: Liste des colonnes (nom et type).
        """
        pass

    @abstractmethod
    def guess_read(self, source: str):
        """
        Devine les paramètres nécéssaires pour lire les données.
        :param source: Requête SQL ou chemin du fichier.
        :return: Paramètres devinés (structure, types...).
        """
        pass