import os
import timeit
import chardet
import smbclient
import unicodedata
from typing import List
from .timer import timer, get_timer
from .dataFactory import data_factory

class FileHandler:
    def __init__(self, logger, smb_config: dict=None, batch_size: int=4_096):
        """Initialise le gestionnaire de fichiers avec le chemin du fichier"""
        self.logger = logger
        self.smb_config = smb_config
        self.batch_size = batch_size
        if smb_config:
            self._setup_smb_connection()

    @timer
    def _setup_smb_connection(self):
        """
        Configure la connection SMB
        """
        try:
            smbclient.register_session(
                self.smb_config.get("server"),
                username=self.smb_config.get("username"),
                password=self.smb_config.get("password")
            )
            self.logger.info("Connexion SMB établie.")
        except Exception as e:
            self.logger.error(f"Échec de la connexion SMB : {e}")
            raise

    def read_file(self, file_path: str, mode: str='rb', encoding: str=None):
        """Lit un fichier local ou SMB en batchs"""
        if self.smb_config and file_path.startswith("//"):
            return self._read_smb_file(file_path, mode, encoding)
        return self._read_local_file(file_path, mode, encoding)

    def _read_smb_file(self, file_path, mode, encoding):
        """Lit un fichier sur un partage SMB en batchs"""
        timer_start = timeit.default_timer()
        try:
            with smbclient.open_file(file_path, mode=mode, encoding=encoding) as file:
                while chunk := file.read(self.batch_size):
                    yield chunk
                self.logger.info(f"Lecture réussie du fichier : {file_path}")
            if get_timer():
                elapsed_time = timeit.default_timer() - timer_start
                self.logger.info(f"Temps d'exécution de sqlQuery: {elapsed_time:.4f} secondes")
        except Exception as e:
            self.logger.error(f"Erreur de lecture du fichier SMB : {e}")
            raise

    def _read_local_file(self, file_path, mode, encoding):
        """Lit un fichier en local en batchs"""
        timer_start = timeit.default_timer()
        try:
            with open(file_path, mode=mode, encoding=encoding) as file:
                while chunk := file.read(self.batch_size):
                    yield chunk
                self.logger.info(f"Lecture réussie du fichier: {file_path}")
            if get_timer():
                elapsed_time = timeit.default_timer() - timer_start
                self.logger.info(f"Temps d'exécution de sqlQuery: {elapsed_time:.4f} secondes")
        except Exception as e:
            self.logger.error(f"Erreur de lecture du fichier en local: {e}")
            raise

    @timer
    def write_file(self, file_path: str, content, mode: str='wb', clean: bool=False):
        """Écrit du contenu dans un fichier local ou SMB en batchs"""
        if clean:
            self.logger.info(f"Nettoyage du fichier {file_path}.")
        if self.smb_config and file_path.startswith("//"):
            return self._write_smb_file(file_path, content, mode, clean)
        return self._write_local_file(file_path, content, mode, clean)

    def _write_smb_file(self, file_path, content, mode, clean: bool=False):
        """Écrit du contenu dans un fichier via partage SMB en batchs"""
        try:
            encoding = "utf-8" if "b" not in mode else None
            with smbclient.open_file(file_path, mode=mode, encoding=encoding) as file:
                for chunk in content:
                    if clean:
                        chunk = self.clean_text(chunk)
                    for i in range(0, len(chunk), self.batch_size):
                        file.write(chunk[i:i + self.batch_size])
                self.logger.info(f"Succès: contenu écrit dans '{file_path}' (SMB).")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'écriture du fichier '{file_path}' via SMB: {e}")
            raise

    def _write_local_file(self, file_path, content, mode, clean: bool=False):
        """Écrit du contenu dans un fichier local en batchs"""
        try:
            encoding = "utf-8-sig" if "b" not in mode else None
            with open(file_path, mode=mode, encoding=encoding) as file:
                for chunk in content:
                    if clean:
                        chunk = self.clean_text(chunk)
                    for i in range(0, len(chunk), self.batch_size):
                        file.write(chunk[i:i + self.batch_size])
                self.logger.info(f"Succès: Contenu écrit dans '{file_path}' (local).")
        except Exception as e:
            self.logger.error(f"Erreur lors de l'écriture du fichier '{file_path}' en local: {e}")
            raise

    def list_dir(self, dir_path: str):
        """Liste le contenu d'un dossier en local ou via SMB"""
        try:
            if self.smb_config and dir_path.startswith("//"):
                return smbclient.listdir(dir_path)
            return os.listdir(dir_path)
        except Exception as e:
            self.logger.error(f"Erreur lors de la lecture du dossier {dir_path}: {e}")
            return []

    def file_exists(self, file_path: str):
        """Vérifie si le fichier existe (local ou SMB)"""
        if self.smb_config and file_path.startswith("//"):
            return self._smb_file_exists(file_path)
        return self._local_file_exists(file_path)

    def _smb_file_exists(self, file_path):
        """Vérifie si un fichier SMB existe"""
        try:
            exists = smbclient.path.exists(file_path) and smbclient.path.isfile(file_path)
            if exists:
                self.logger.info(f"Le fichier existe: {file_path}")
            else:
                self.logger.warning(f"Le fichier n'existe pas: {file_path}")
            return exists
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification d'existence du fichier {file_path}: {e}")

    def _local_file_exists(self, file_path):
        """Vérifie si un fichier en local existe"""
        exists = os.path.exists(file_path) and os.path.isfile(file_path)
        if exists:
            self.logger.info(f"Le fichier existe: {file_path}")
        else:
            self.logger.warning(f"Le fichier n'existe pas: {file_path}")
        return exists

    def directory_exists(self, dir_path: str):
        """Vérifie si le fichier existe (local ou SMB)"""
        if self.smb_config and dir_path.startswith("//"):
            return self._smb_directory_exists(dir_path)
        return self._local_directory_exists(dir_path)

    def _smb_directory_exists(self, dir_path: str):
        try:
            exists = smbclient.path.exists(dir_path) and smbclient.path.isdir(dir_path)
            if exists:
                self.logger.info(f"Le dossier existe: {dir_path}")
            else:
                self.logger.warning(f"Le dossier n'existe pas: {dir_path}")
            return exists
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification d'existence du dossier {dir_path}: {e}")

    def _local_directory_exists(self, dir_path):
        exists = os.path.exists(dir_path) and os.path.isdir(dir_path)
        if exists:
            self.logger.info(f"Le dossier existe: {dir_path}")
        else:
            self.logger.warning(f"Le dossier n'existe pas: {dir_path}")
        return exists

    def remove_file(self, file_path: str):
        """Supprime un fichier (local ou SMB)"""
        try:
            if self.smb_config and file_path.startswith("//"):
                smbclient.remove(file_path)
            else:
                os.remove(file_path)
            self.logger.info("Fichier supprimé avec succès.")
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression du fichier '{file_path}': {e}")
            raise

    def create_empty_file(self, file_path: str, mode: str='wb'):
        """Crée un fichier vide (local ou SMB)"""
        try:
            if self.smb_config and file_path.startswith("//"):
                with smbclient.open_file(file_path, mode=mode) as file:
                    pass
                self.logger.info(f"Fichier vide créé sur SMB: {file_path}")
            else:
                with open(file_path, mode=mode) as file:
                    pass
                self.logger.info(f"Fichier vide créé localement: {file_path}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la création du fichier vide '{file_path}': {e}")
            raise

    def clean_text(self, text):
        if isinstance(text, bytes):
            encoding = chardet.detect(text)["encoding"]
            text = text.decode(encoding or "utf-8", errors='ignore')
        text = unicodedata.normalize('NFKD', text)
        text = ''.join([c for c in text if not unicodedata.combining(c)])
        text = ''.join([f'&#{ord(c)};' if ord(c) > 127 else c for c in text])
        return text.encode("utf-8")

    def _get_dir_size(self, path='.'):
        """Calcule récursivement la taille d'un répertoire"""
        total = 0
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += self._get_dir_size(entry.path)
                except Exception as e:
                    self.logger.error(f"Erreur sur le fichier {entry.name}: {e}")
                    raise
        return total

    def _convertir_octets(self, taille_octets):
        """Convertit une taille en octets dans une unité lisible"""
        for unite in ['octets', 'Ko', 'Mo', 'Go', 'To']:
            if taille_octets < 1024.0:
                return round(taille_octets, 2), unite
            taille_octets /= 1024.0
        return round(taille_octets, 2), 'To'

    def _ensure_table_exists(self, db: data_factory, schema: str, table: str):
        """Crée la table cible si elle n'existe pas encore."""
        from .dbMysql import dbMysql
        from .dbMssql import dbMssql
        from .dbPgsql import dbPgsql

        cols = ["tenantname", "date", "taille", "unite", "fichier"]
        cols_def = ["VARCHAR(255)", "TIMESTAMP", "FLOAT", "VARCHAR(10)", "VARCHAR(255)"]
        if isinstance(db, dbMssql):
            cols_def[1] = "DATETIME2"
        columns = ", ".join(f"{col} {typ}" for col, typ in zip(cols, cols_def))
        full_table = f"{schema}.{table}" if schema else table
        if isinstance(db, (dbMysql, dbPgsql)):
            query = f"CREATE TABLE IF NOT EXISTS {full_table} ({columns});"
        elif isinstance(db, dbMssql):
            query = f"""
            IF OBJECT_ID('{full_table}', 'U') IS NULL
            CREATE TABLE {full_table} ({columns});
            """
        else:
            raise ValueError(f"Type de base de données non pris en charge: {type(db).__name__}")
        db.sqlExec(query)

    def _collect_files(self, base_path: str, filter: str):
        """Retourne la liste complète des fichiers correspondant au filtre."""
        import os
        return [
            os.path.join(root, f)
            for root, _, files in os.walk(base_path)
            for f in files
            if filter in f
        ]

    def _process_files(self, db: data_factory, schema: str, table: str, fichiers: List[str], tenant_name: str, date: str, base_path: str):
        """Traite les fichiers, calcule les tailles et insère les résultats dans la base."""
        total_size = 0
        bulk_data = []
        cols = ["tenantname", "date", "taille", "unite", "fichier"]

        for fichier in fichiers:
            try:
                size = os.path.getsize(fichier)
                total_size += size
                value, unit = self._convertir_octets(size)
                bulk_data.append([tenant_name, date, str(value), unit, fichier])
            except Exception as e:
                self.logger.error(f"Erreur sur le fichier {fichier}: {e}")

        if bulk_data:
            db.insertBulk(schema, table, cols, bulk_data)

        total_value, total_unit = self._convertir_octets(total_size)
        total_data = [f"{tenant_name} TOTAL", date, str(total_value), total_unit, f"TOTAL {base_path}"]
        db.insert(schema, table, cols, total_data)

        self.logger.info(f"Taille totale: {total_value} {total_unit}")

    @timer
    def disk_check(self, db: data_factory, schema: str, table: str, base_path: str, tenant_name: str = 'DEFAULT', filter: str = 'python-'):
        """
        Calcule la taille des fichiers correspondant à un filtre dans un répertoire
        et enregistre les résultats dans la table {schema}.{table}.
        :param db: Instance de data_factory (dbMssql, dbPgsql, dbMysql)
        :param schema: Nom du schéma
        :param table: Nom de la table cible
        :param base_path: Répertoire racine à scanner
        :param tenant_name: Nom du tenant à enregistrer
        :param filter: Mot-clé à rechercher dans les fichiers
        """
        from datetime import date

        self.logger.info(f"Lancement du disk_check à partir de {base_path}")
        db.connect()
        today = str(date.today())

        self._ensure_table_exists(db, schema, table)
        fichiers = self._collect_files(base_path, filter)
        if not fichiers:
            self.logger.warning(f"Aucun fichier contenant '{filter}' trouvé dans {base_path}.")
            return
        self._process_files(db, schema, table, fichiers, tenant_name, today, base_path)

    def wait_for_file(self, path: str, filename: str, retry: int = 20):
        """
        Attend qu'un fichier spécifique soit disponible dans un répertoire donné (local ou SMB),
        avec un nombre limité de tentatives
        :param path: Chemin du répertoire où chercher le fichier
        :param filename: Nom du fichier à attendre
        :param retry: Nombre maximal de tentatives
        :return: True si le fichier est trouvé dans le nombre de tentatives sinon False
        """
        import time

        full_path = os.path.join(path, filename)
        self.logger.info(f"Attente du fichier '{filename}' dans le répertoire '{path}'.")

        try:
            if self.smb_config and path.startswith("//"):
                exists = smbclient.path.exists(path)
            else:
                exists = os.path.exists(path)
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du chemin '{path}': {e}")
            raise
        if not exists:
            msg = f"Le chemin spécifié n'existe pas: {path}"
            self.logger.error(msg)
            raise ValueError(msg)
        i = 1
        while i <= retry:
            try:
                if self.smb_config and full_path.startswith("//"):
                    found = smbclient.path.isfile(full_path)
                else:
                    found = os.path.isfile(full_path)
            except Exception as e:
                self.logger.error(f"Erreur lors de la vérification du fichier '{full_path}': {e}")
                raise
            if found:
                self.logger.info(f"Fichier '{filename}' trouvé après {i} tentative(s).")
                return True
            time.sleep(1)
            i += 1
        self.logger.warning(f"Fichier '{filename}' introuvable après {retry} tentative(s).")
        return False