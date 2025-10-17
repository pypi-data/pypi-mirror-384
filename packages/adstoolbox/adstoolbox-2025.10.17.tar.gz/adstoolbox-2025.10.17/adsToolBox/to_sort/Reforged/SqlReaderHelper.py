from to_sort.Reforged.ReaderHelper import ReaderHelper

class SqlReaderHelper(ReaderHelper):
    """
    Implémentation de ReaderHelper pour une base SQL.
    """
    def get_columns(self, source: str):
        """
        Récupère les colonnes d'une table ou d'une requête SQL.
        :param source: Nom de la table ou requête SQL.
        :return: Liste de tuples (nom_colonne, type_colonne).
        """
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = '{source}'
        """
        try:
            cursor = self.connection.connection.cursor()
            cursor.execute(query)
            return cursor.fetchall()
        except Exception as e:
            raise RuntimeError(f"Erreur lors de la récupération des colonnes: {e}")

    def guess_read(self, source: str):
        """
        Devine les paramètres nécéssaires pour lire les données d'une source SQL.
        :param source: Nom de la table SQL ou requête SQL.
        :return: Structure devinée des données (colonnes, types...)
        """
        columns = self.get_columns(source)
        return {
            "columns": [col[0] for col in columns],
            "types": [col[1] for col in columns]
        }