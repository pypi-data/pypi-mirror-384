from typing import Callable, List, Dict

class Pipeline:
    """
    Pipeline qui lie un Reader à un Writer et exécute un flux de données
    """
    def __init__(self, reader, writer, logger=None):
        """
        Initialise le Pipeline avec un Reader et un Writer
        :param reader: Instance d'un Reader pour lire les données
        :param writer: Instance d'un Writer pour écrire les données
        :param logger: Logger pour suivre l'exécution du pipeline
        """
        self.reader = reader
        self.writer = writer
        self.logger = logger
        self.column_mapping = {}
        self.calculated_columns = []
        self.join_sources = []

    def set_mapping(self, column_mapping: Dict[str, str]):
        """
        Définit le mapping entre les colonnes sources et les colonnes cibles
        :param column_mapping: Dictionnaire {colonne_source: colonne_cible}.
        """
        self.column_mapping = column_mapping

    def add_calculated_column(self, column_name: str, function: Callable):
        """
        Ajoute une colonne calculée au flux.
        :param column_name: Nom de la nouvelle colonne
        :param function: Fonction qui calcule la colonne (prend une ligne en entrée et retourne une valeur)
        """
        self.calculated_columns.append((column_name, function))

    def add_join(self, join_reader, join_key_source: str, join_key_target: str, join_type: str = "inner"):
        """
        Ajoute une jointure avec une autre source de données.
        :param join_reader: Instance d'un Reader pour la source à joindre.
        :param join_key_source: Clé de jointure dans les données sources.
        :param join_key_target: Clé de jointure dans les données cibles.
        :param join_type: Type de jointure (inner, left, right, full).
        """
        self.join_sources.append({
            "reader": join_reader,
            "source_key": join_key_source,
            "target_key": join_key_target,
            "type": join_type,
        })

    def _apply_mapping(self, row: Dict):
        """
        Applique le mapping des colonnes sur une ligne de données.
        :param row: Ligne de données source.
        :return: Ligne de données avec les colonnes mappées.
        """
        if not self.column_mapping:
            return row
        return {self.column_mapping.get(key, key): value for key, value in row.items()}

    def _apply_calculations(self, row: Dict):
        """
        Applique les colonnes calculées sur une ligne de données.
        :param row: Ligne de données.
        :return: Ligne de données enrichie avec les colonnes calculées
        """
        for column_name, function in self.calculated_columns:
            row[column_name] = function(row)
        return row

    def _join_data(self, rows: List[Dict]):
        """
        Applique les jointures entre les données sources et les autres sources.
        :param rows: Ligne de données sources.
        :return: Ligne de données jointes.
        """
        for join in self.join_sources:
            join_reader = join["reader"]
            source_key = join["source_key"]
            target_key = join["target_key"]
            join_type = join["type"]
            joined_rows = list(join_reader.read())
            join_index = {row[target_key]: row for row in joined_rows}
            for row in rows:
                join_value = row.get(source_key)
                if join_value in join_index:
                    row.update(join_index[join_value])
                elif join_type == "left":
                    continue
                elif join_type == "inner":
                    rows.remove(row)
                elif join_type == "right":
                    raise NotImplementedError("Right join non supportée dans cet exemple.")
        return rows

    def execute(self, source_query_or_path: str, mode: str = "insert", batch_size: int = None):
        """
        Exécute le flux de données entre le Reader et le Writer.
        :param source_query_or_path: Requête SQL ou chemin de fichier pour le Reader.
        :param mode: Mode d'écriture (insert, update, etc.)
        :param batch_size: Taille des lots à lire et à écrire
        """
        if self.logger:
            self.logger.info("Début de l'exécution du pipeline.")
        for batch in self.reader.read(source_query_or_path, batch_size=batch_size):
            if isinstance(batch, list):
                batch = [dict(row) for row in batch]
            batch = [self._apply_mapping(row) for row in batch]
            batch = [self._apply_calculations(row) for row in batch]
            batch = self._join_data(batch)
            self.writer.write(batch, mode=mode, batch_size=batch_size)
        if self.logger:
            self.logger.info("Exécution du pipeline terminée avec succès.")