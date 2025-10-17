from to_sort.Reforged.Writer import Writer
import csv

class CsvWriter(Writer):
    """
    Implémentation du Writer pour écrire des données dans un fichier CSV.
    """
    def __init__(self, connection):
        """
        Initialise le Writer CSV.
        :param connection: Instance de la classe Connection (doit être de type 'file').
        """
        if connection.resource_type != 'file':
            raise ValueError("Le Writer CSV nécéssite une connexion de type 'file'.")
        super().__init__(connection)

    def write(self, data, mode: str = "insert", batch_size: int = None, if_exists: str = "none", if_not_exists: str = "fail"):
        """
        Écrit des données dans un fichier CSV.
        :param data: Données à écrire (liste de listes).
        :param mode: Mode d'écriture (seul 'insert' est supporté pour les CSV).
        :param batch_size: Taille des lots (non utilisé pour les CSV).
        :param if_exists: Action si le fichier existe (supprime, écrase, etc).
        :param if_not_exists: Action si le fichier n'existe pas.
        """
        file_path = self.connection.params.get("file_path")
        mode = "w" if if_exists == "deleteAndCreate" else "a"
        try:
            with open(file_path, mode=mode, newline='', encoding=self.connection.params.get("encoding", "utf-8")) as csv_file:
                writer = csv.writer(csv_file)
                if if_exists == "deleteAndCreate":
                    writer.writerow(data[0]) # Écrire l'en-tête si on recrée le fichier
                writer.writerow(data[1:])
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'écriture dans le fichier CSV: {e}")

