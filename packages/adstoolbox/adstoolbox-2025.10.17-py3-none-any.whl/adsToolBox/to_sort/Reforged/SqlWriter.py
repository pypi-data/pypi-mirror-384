from to_sort.Reforged.Writer import Writer

class SqlWriter(Writer):
    """
    Implémentation du Writer pour écrire des données dans une base SQL.
    """
    def __init__(self, connection):
        """
        Initialise le Writer SQL.
        :param connection: Instance de la classe Connection SQL
        """
        super().__init__(connection)

    def write(self, data, mode: str = "insert", batch_size: int = None, if_exists: str = "none", if_not_exists: str = "fail"):
        """
        Écrit des données dans une base SQL.
        :param data: Données à écrire (liste de tuples).
        :param mode: Mode d'écriture (insert, update, delete, etc.).
        :param batch_size: Taille des lots.
        :param if_exists: Action si la ressource existe.
        :param if_not_exists: Action si la ressource n'existe pas.
        :return:
        """
        if not self.connection.is_open():
            raise RuntimeError("La connexion doit être ouverte avant d'écrire des données.")
        self._handle_resource(if_exists, if_not_exists)
        if mode == "insert":
            self._write_insert(data, batch_size)
        elif mode == "update":
            self._write_update(data, batch_size)
        elif mode == "delete":
            self._write_delete(data, batch_size)
        else:
            raise ValueError(f"Mode d'écriture non supporté: {mode}")

    def _handle_resource(self, if_exists, if_not_exists):
        """
        Gère les actions à effectuer sur la resource (table) en fonction des options 'if_exists' et 'if_not_exists'
        """
        cursor = self.connection.connection.cursor()
        if if_not_exists == "create":
            cursor.execute("CREATE TABLE IF NOT EXISTS ...")
            self.connection.commit()
        elif if_not_exists == "fail":
            cursor.execute("SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE ...")
            if not cursor.fetchone():
                raise RuntimeError("La table n'existe pas.")
        if if_exists == "deleteAndCreate":
            cursor.execute("DROP TABLE IF EXISTS ...")
            cursor.execute("CREATE TABLE ...")
            self.connection.commit()
        elif if_exists == "truncate":
            cursor.execute("TRUNCATE TABLE ...")
            self.connection.commit()

    def _write_insert(self, data, batch_size):
        """
        Gère l'insertion des données.
        """
        cursor = self.connection.connection.cursor()
        for batch in self._batch_data(data, batch_size):
            query = "INSERT INTO ... VALUES (%s, %s, ...)"
            cursor.executemany(query, batch)
            self.connection.commit()

    def _write_update(self, data, batch_size):
        """
        Gère la mise à jour des données.
        """
        cursor = self.connection.connection.cursor()
        for batch in self._batch_data(data, batch_size):
            query = "UPDATE ... SET col1 = %s, col2 = %s WHERE ..."
            cursor.executemany(query, batch)
            self.connection.commit()

    def _write_delete(self, data, batch_size):
        """
        Gère la suppression des données.
        """
        cursor = self.connection.connection.cursor()
        for batch in self._batch_data(data, batch_size):
            query = "DELETE FROM ... WHERE ..."
            cursor.executemany(query, batch)
            self.connection.commit()

    @staticmethod
    def _batch_data(data, batch_size):
        """
        Divise les données en lots pour éviter les surcharges mémoires
        """
        if batch_size:
            for i in range(0, len(data), batch_size):
                yield data[i:i + batch_size]
        else:
            yield data