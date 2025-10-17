from to_sort.Reforged.Reader import Reader
import csv

class CsvReader(Reader):
    """
    Implémentation du Reader pour lire des données depuis un fichier CSV.
    """
    def __init__(self, connection):
        """
        Initialise le Reader CSV.
        :param connection: Instance de la classe Connection (doit être de type 'file').
        """
        if connection.resource_type != "file":
            raise ValueError("Le Reader CSV nécessite une connexion de type 'file'.")
        super().__init__(connection)

    def read(self, file_path: str, batch_size: int = None):
        """
        Lit les données d'un fichier CSV.
        :param file_path: Chemin du fichier CSV.
        :param batch_size: Nombre de lignes à lire par lot (None pour tout lire).
        :return: Un générateur qui retourne les données par lots ou en entier.
        """
        self.connection.logger.debug(f"Lecture du fichier CSV : {file_path}")
        try:
            with open(file_path, mode='r', encoding=self.connection.params.get("encoding", "utf-8")) as csv_file:
                reader = csv.reader(csv_file)
                header = next(reader)  # Lire l'en-tête
                if batch_size:
                    batch = []
                    for row in reader:
                        batch.append(row)
                        if len(batch) == batch_size:
                            yield [header] + batch
                            batch = []
                    if batch:
                        yield [header] + batch
                else:
                    yield [header] + list(reader)
        except Exception as e:
            self.connection.logger.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            raise