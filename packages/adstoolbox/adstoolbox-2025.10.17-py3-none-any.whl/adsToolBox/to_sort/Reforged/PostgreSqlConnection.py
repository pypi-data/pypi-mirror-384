import psycopg2
from to_sort.Reforged.Connection import Connection

class PostgreSqlConnection(Connection):
    """
    Implémentation de l'interface Connection pour PostgreSQL.
    """
    def __init__(self, **kwargs):
        """
        Initialise la connexion PostgreSQL.
        :param kwargs: Paramètres spécifiques à la connexion (hôte, utilisateur, etc.).
        """
        super().__init__(resource_type="sql", **kwargs)

    def open(self):
        if self.connection:
            raise RuntimeError("La connexion est déjà ouverte.")
        try:
            self.connection = psycopg2.connect(
                host=self.params.get("host"),
                user=self.params.get("user"),
                password=self.params.get("password"),
                dbname=self.params.get("database"),
                port=self.params.get("port"),
                connect_timeout=self.params.get("timeout", 10)
            )
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'ouverture de la connexion PostgreSQL : {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def commit(self):
        if self.connection:
            try:
                self.connection.commit()
            except Exception as e:
                raise RuntimeError(f"Erreur lors du commit PostgreSQL : {e}")
        else:
            raise RuntimeError("Impossible de commit : aucune connexion active.")

    def is_open(self) -> bool:
        return self.connection is not None and self.connection.closed == 0