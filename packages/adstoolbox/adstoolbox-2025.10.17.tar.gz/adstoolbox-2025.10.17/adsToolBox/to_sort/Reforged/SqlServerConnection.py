import pymssql
import pytds
from to_sort.Reforged.Connection import Connection

class SqlServerConnection(Connection):
    """
    Implémentation de l'interface Connection pour SQL Server.
    """
    def __init__(self, driver: str = "pymssql", **kwargs):
        """
        Initialise la connexion SQL Server.
        :param driver: Pilote à utiliser ('pymssql' ou 'pytds').
        :param kwargs: Paramètres spécifiques à la connexion (serveur, utilisateur, etc.).
        """
        super().__init__(resource_type="sql", **kwargs)
        self.driver = driver

    def open(self):
        if self.connection:
            raise RuntimeError("La connexion est déjà ouverte.")
        try:
            if self.driver == "pymssql":
                self.connection = pymssql.connect(
                    server=self.params.get("server"),
                    user=self.params.get("user"),
                    password=self.params.get("password"),
                    database=self.params.get("database"),
                    port=self.params.get("port"),
                    charset=self.params.get("charset", "UTF-8")
                )
            elif self.driver == "pytds":
                self.connection = pytds.connect(
                    dsn=self.params.get("server"),
                    port=self.params.get("port"),
                    user=self.params.get("user"),
                    password=self.params.get("password"),
                    database=self.params.get("database"),
                    autocommit=self.params.get("autocommit", False)
                )
            else:
                raise ValueError(f"Pilote non supporté : {self.driver}")
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'ouverture de la connexion SQL Server : {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def commit(self):
        if self.connection:
            try:
                self.connection.commit()
            except Exception as e:
                raise RuntimeError(f"Erreur lors du commit SQL Server : {e}")
        else:
            raise RuntimeError("Impossible de commit : aucune connexion active.")

    def is_open(self) -> bool:
        return self.connection is not None and not self.connection.closed