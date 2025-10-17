from abc import ABC, abstractmethod

class WriterHelper(ABC):
    """
    Interface pour aider à paramètrer un Writer
    """
    def __init__(self, connection):
        """
        Initialise le WriterHelper avec une connexion donnée.
        :param connection: Instance de la classe connection utilisée pour accèder aux données.
        """
        self.connection = connection

    @abstractmethod
    def guess_insert(self, target: str, columns: list):
        """
        Génère automatiquement une requête d'insertion.
        :param target: Nom de la table ou du fichier cible.
        :param columns: Liste des colonnes.
        :return: Requête ou commande d'insertion
        """
        pass

    @abstractmethod
    def guess_update(self, target: str, columns: list, conflict_cols: list):
        """
        Génère automatiquement une requête de mise à jour.
        :param target: Nom de la table ou du fichier cible.
        :param columns: Liste des colonnes à mettre à jour.
        :param conflict_cols: Colonnes utilisées pour détecter les conflits.
        :return: Requête de mise à jour.
        """
        pass

    @abstractmethod
    def guess_if_exists_delete_and_create(self, target: str):
        """
        Génère automatiquement les commandes pour supprimer et recréer une ressource.
        :param target: Nom de la table ou du fichier cible.
        :return: Commandes pour supprimer et recréer.
        """
        pass