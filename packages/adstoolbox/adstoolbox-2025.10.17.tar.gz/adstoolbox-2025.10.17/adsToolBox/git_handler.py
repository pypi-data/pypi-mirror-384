import os
from .logger import Logger
from git import Repo
from github import Github
from .timer import timer

class GitHandler:
    def __init__(self, token: str, logger: Logger):
        self.token = token
        self.github = Github(token)
        self.logger = logger

    def check_permissions(self, path: str):
        if not os.access(path, os.R_OK):
            raise PermissionError(f"Le script n'a pas la permission de lecture sur le chemin: {path}")

    @timer
    def clone_or_update(self, destination_path: str, repository: str, branch: str = None):
        """Clone le repo s'il existe pas localement, sinon pull la dernière version."""
        self.logger.info(f"Connexion au repo {repository}")
        url = f"https://{self.token}@github.com/{repository}.git"
        try:
            if os.path.exists(destination_path):
                self.check_permissions(destination_path)
                repo = Repo(destination_path)

                self.logger.debug("Mise à jour du remote origin avec le token.")
                repo.remotes.origin.set_url(url)

                repo.remotes.origin.fetch()
                if branch:
                    self.logger.debug(f"Changement de branche : {branch}")
                    repo.git.checkout(branch)
                repo.remotes.origin.pull()
                self.logger.info(f"Le repo {repository} a été mis à jour.")
            else:
                self.logger.info(f"Clonage du repo {repository} dans {destination_path}...")
                if branch:
                    Repo.clone_from(url, destination_path, branch=branch)
                else:
                    Repo.clone_from(url, destination_path)
                self.logger.info(f"Le repo {repository} a été cloné avec succès.")
        except Exception as e:
            self.logger.error(f"Erreur lors du clonage du repo {repository}: {e}")
            raise

    @timer
    def setup_virtualenv(self, repo_path: str):
        """Création et installation d'un environnement virtuel dans le repo."""
        venv_path = os.path.join(repo_path, "venv")
        requirements_path = os.path.join(repo_path, "requirements.txt")
        launch_script = os.path.join(repo_path, "launch.sh")
        self.logger.info(f"Création de l'environnement virtuel dans {venv_path}...")
        os.system(f"python -m venv {venv_path}")
        if os.path.exists(requirements_path):
            self.logger.info("Installation des dépendances à partir de requirements.txt...")
            activate = os.path.join(venv_path, "Scripts",
                                    "activate") if os.name == "nt" else f"source {venv_path}/bin/activate"
            install_cmd = f"{activate} && pip install -r {requirements_path}"
            os.system(install_cmd)
        else:
            self.logger.warning("Aucun fichier requirements.txt trouvé, installation ignorée.")
        # Attribution des droits d’exécution au script launch.sh (si présent)
        if os.path.exists(launch_script):
            self.logger.info("Attribution des droits d'exécution sur launch.sh...")
            try:
                os.chmod(launch_script, 0o755)
                self.logger.info("Droits d'exécution appliqués avec succès sur launch.sh.")
            except Exception as e:
                self.logger.error(f"Impossible de modifier les permissions de launch.sh : {e}")
        else:
            self.logger.warning("Aucun fichier launch.sh trouvé dans le dépôt.")
        self.logger.info("Environnement virtuel configuré avec succès.")