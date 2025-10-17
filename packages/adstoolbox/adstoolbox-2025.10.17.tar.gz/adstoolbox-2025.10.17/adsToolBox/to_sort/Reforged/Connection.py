from abc import ABC, abstractmethod

class Connection(ABC):
    """
    Interface de base pour fournir un accès aux données.
    Permet de gérer la connexion à une ressource (base de données, fichier, etc.).
    """
    def __init__(self, resource_type: str, **kwargs):
        """
        Initialise la connexion.

        :param resource_type: Type de ressource (ex: 'sql', 'file').
        :param kwargs: Détails de connexion spécifiques à l'implémentation (serveur, utilisateur, mot de passe...).
        """
        self.resource_type = resource_type
        self.params = kwargs
        self.connection = None

    @abstractmethod
    def open(self):
        """Ouvre la connexion à la ressource."""
        pass

    @abstractmethod
    def close(self):
        """Ferme la connexion à la ressource."""
        pass

    @abstractmethod
    def commit(self):
        """Valide les changements (le cas échéant)."""
        pass

    @abstractmethod
    def is_open(self) -> bool:
        """Vérifie si la connexion est ouverte."""
        pass