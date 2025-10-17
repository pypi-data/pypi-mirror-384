from to_sort.Reforged.WriterHelper import WriterHelper

class SqlWriterHelper(WriterHelper):
    """
    Implémentation de WriterHelper pour une base SQL.
    """
    def guess_insert(self, target: str, columns: list):
        """
        Génère une requête d'insertion.
        :param target: Nom de la table cible.
        :param columns: Liste des colonnes.
        :return: Requête SQL d'insertion.
        """
        placeholders =  ", ".join(["%s"] * len(columns))
        col_names = ", ".join(columns)
        return f"INSERT INTO {target} ({col_names}) VALUES ({placeholders})"

    def guess_update(self, target: str, columns: list, conflict_cols: list):
        """
        Génère une requête de mise à jour.
        :param target: Nom de la table cible.
        :param columns: Liste des colonnes à mettre à jour.
        :param conflict_cols: Liste des colonnes pour détecter les conflits.
        :return: Requête SQL d'update.
        """
        update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in columns if col not in conflict_cols])
        conflict_cols = ", ".join(conflict_cols)
        return f"""
        INSERT INTO {target} ({', '.join(columns)}
        VALUES ({', '.join(["%s"] * len(columns))}
        ON CONFLICT ({conflict_cols} DO UPDATE
        SET {update_clause}
        """

    def guess_if_exists_delete_and_create(self, target: str):
        """
        Génère les commandes pour supprimer et recréer une table SQL.
        :param target: Nom de la table.
        :return: Commandes SQL pour drop et create.
        """
        return [
            f"DROP TABLE IF EXISTS {target}",
            f"CREATE TABLE {target} (...)"
        ]