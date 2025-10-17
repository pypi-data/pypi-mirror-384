import os
import dotenv

class env:
    def __init__(self, logger, file=None):
        """
        Charge les variables d'environnement à partir d'un fichier `.env`.
        Si aucune fichier n'est spécifié et que `.env` n'est pas trouvé, on se contente des variables
        d'environnement déjà définis
        :param logger: Le Logger est un objet d'adsToolBox. Veuillez définir un Logger() avant de faire appel à cette méthode.
        :param file: Le chemin vers un fichier `.env` spécifique à charger. Si ce paramètre est omis,
            la classe cherche automatiquement un fichier `.env` à la racine du projet.
        """
        if file:
            if os.path.isfile(file):
                dotenv_file = dotenv.find_dotenv(file)
                dotenv.load_dotenv(dotenv_file)
                logger.debug("Fichier spécifié pour l'environnement trouvé")
            else:
                logger.warning("Fichier spécifié non trouvé")
        elif os.path.isfile('.env'):
            dotenv_file = dotenv.find_dotenv('.env')
            dotenv.load_dotenv(dotenv_file)
        else:
            logger.warning("Fichier .env non trouvé à la racine du projet")
            logger.warning("Veuillez créer un fichier .env à la racine du projet ou en spécifier un vous même")
        for cle, valeur in os.environ.items():
            setattr(self, cle, valeur)