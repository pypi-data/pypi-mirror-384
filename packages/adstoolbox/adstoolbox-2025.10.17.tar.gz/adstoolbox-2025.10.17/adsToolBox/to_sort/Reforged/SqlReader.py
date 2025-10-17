from to_sort.Reforged.Reader import Reader

class SQLReader(Reader):
    """
    Implémentation du Reader pour lire des données depuis une base SQL.
    """
    def __init__(self, connection):
        """
        Initialise le Reader SQL.
        :param connection: Instance de la classe Connection SQL.
        """
        super().__init__(connection)

    def read(self, query: str, batch_size: int = None):
        """
        Lit les données d'une base SQL via une requête.
        :param query: Requête SQL à exécuter.
        :param batch_size: Nombre de lignes à lire par lot (None pour tout lire).
        :return: Un générateur qui retourne les données par lots ou en entier.
        """
        if not self.connection.is_open():
            raise RuntimeError("La connexion doit être ouverte avant de lire des données.")

        self.connection.logger.debug(f"Exécution de la requête : {query}")
        try:
            with self.connection.Connection.cursor() as cursor:
                cursor.execute(query)
                if batch_size:
                    while True:
                        rows = cursor.fetchmany(batch_size)
                        if not rows:
                            break
                        yield rows
                else:
                    yield cursor.fetchall()
        except Exception as e:
            self.connection.logger.error(f"Erreur lors de la lecture des données SQL : {e}")
            raise