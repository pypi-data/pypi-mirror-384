import re
import email
import chardet
import imaplib
import requests
import mimetypes
from email import policy

class mail:
    def __init__(self, configuration: dict, logger, auth_mode: str):
        """
        Instancie la classe mail
        :param configuration: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion imap
        :param logger: Un logger ads qui va gérer les logs des actions de la classe
        :param auth_mode: Le mode d'authentification 'oauth2' ou 'credentials'
        """
        self.logger = logger
        self.__url=configuration.get("url")
        self.__clientId=configuration.get("clientId")
        self.__clientSecret=configuration.get("clientSecret")
        self.__email=configuration.get("email")
        self.__emailFrom=configuration.get("emailFrom")
        self.__subject=configuration.get("subject")
        self.__scope=configuration.get("scope")
        self.__server=configuration.get("server")
        self.__login=configuration.get("login")
        self.__password=configuration.get("password")
        self.__token=None
        self.__connection=None
        if auth_mode == 'oauth2':
            self.__connect_with_token()
        elif auth_mode == 'credentials':
            self.__connect_with_credentials()
        else:
            raise ValueError (f"Le mode d'authentification {auth_mode} n'est pas reconnu. Utiliser 'oauth2' ou 'credentials'")

    def __connect_with_credentials(self):
        """Se connecte à un server imap et récupère le token"""
        if self.logger: self.logger.info("Tentative de connexion avec le serveur mail.")
        try:
            imap_conn = imaplib.IMAP4_SSL(self.__server)
            # Authentification avec les identifiants utilisateur
            imap_conn.login(self.__login, self.__password)
            self.__connection = imap_conn
            if self.logger: self.logger.info("Connexion établie.")
        except Exception as e:
            if self.logger: self.logger.error(f"La tentative de connexion a échoué : {str(e)}")
            raise

    def __connect_with_token(self):
        """Se connecte à un server imap et récupère le token"""
        if self.logger: self.logger.info("Tentative de connexion avec le server mail.")
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.__clientId,
            'client_secret': self.__clientSecret,
            'scope': self.__scope
        }
        response = requests.post(self.__url, data=payload)
        if response.status_code==200:
            if self.logger: self.logger.info("Connexion établie")
            if self.logger: self.logger.debug("Tentative de récupération du token.")
            token_data = response.json()
            if "access_token" in token_data:
                if self.logger: self.logger.debug("Token récupéré avec succès !")
                self.__token = token_data["access_token"]
                imap_conn = imaplib.IMAP4_SSL(self.__server)
                auth_string = f"user={self.__email}\1auth=Bearer {self.__token}\1\1"
                imap_conn.authenticate("XOAUTH2", lambda x: auth_string.encode("utf-8"))
                self.__connection = imap_conn
            else:
                self.logger.error(f"Le token n'a pas pu être récupéré {response.reason}.")
                raise

        else:
            self.logger.error(f"La tentative de connexion a echoué {response.reason}.")
            raise

    def mark_as_seen(self, id):
        imap_conn = self.__connection
        if self.logger: self.logger.info(f"Changement du flag du mail {id} à 'Seen'.")
        try:
            imap_conn.store(id, '+FLAGS', '\\Seen')
        except Exception as e:
            if self.logger: self.logger.info(f"Le changement de flag a échoué: {str(e)}.")
            raise

    def mark_as_un_seen(self, id):
        imap_conn = self.__connection
        if self.logger: self.logger.info(f"Changement du flag du mail {id} à 'UnSeen'.")
        try:
            imap_conn.store(id, '-FLAGS', '\\UnSeen')
        except Exception as e:
            if self.logger: self.logger.info(f"Le changement de flag a échoué: {str(e)}.")
            raise

    def delete(self,id):
        imap_conn = self.__connection
        if self.logger: self.logger.info(f"Suppression du mail {id}.")
        try:
            imap_conn.store(id, '+FLAGS', '\\Deleted')
        except Exception as e:
            if self.logger: self.logger.info(f"La suppression a échoué: {str(e)}.")
            raise

    def get_email(self, mailbox='INBOX', readonly=False, emailFrom=None, emailSubject=None, flag="UnSeen", charset=None):
        """
        Récupère les mails selon les paramètres renseignés
        :mailbox string: Contient le dossier de lecture (ex : INBOX)
        :readonly bool: définit si le mail est modifiable. Si False, alors le mail sera automatiqumeent marqué comme lu.
        :emailFrom string: Permet de filtrer sur le destinataire du mail
        :emailSubject string: Permet de filtrer sur l'objet du mail
        :flag string: Permet de filtrer sur le flag ;
            "ALL",
            "SEEN",
            "UNSEEN",
            "FLAGGED",
            "UNFLAGGED",
            "ANSWERED",
            "UNANSWERED",
            "DELETED",
            "UNDELETED",
            "DRAFT"
        :charset string: Permet de définir le charset ex : UTF-8, US-ASCII
        """
        matching_emails=[]
        imap_search_criteria = [
            "ALL",
            "SEEN",
            "UNSEEN",
            "FLAGGED",
            "UNFLAGGED",
            "ANSWERED",
            "UNANSWERED",
            "DELETED",
            "UNDELETED",
            "DRAFT"
        ]
        if flag.upper() not in imap_search_criteria:
            msg = ('Flag incorrect :  ["ALL", "SEEN", "UNSEEN", "FLAGGED", "UNFLAGGED", "ANSWERED", '
                   '"UNANSWERED", "DELETED", "UNDELETED", "DRAFT"]')
            if self.logger: self.logger.error(msg)
            raise ValueError(msg)
        if self.logger: self.logger.info("Tentative de récupération des mails.")
        if not self.__connection:
            if self.logger: self.logger.error("Une connexion doit être établie avant de réaliser cette opération.")
            raise
        imap_conn=self.__connection
        imap_conn.select(mailbox.upper(), readonly)
        if emailFrom :
            status, email_ids = imap_conn.search(charset, f'{flag} FROM "{emailFrom}"')
        else:
            status, email_ids = imap_conn.search(charset, str(flag))
        if status != "OK":
            if self.logger: self.logger.error(
                f"Erreur de la récupération des emails, {status, email_ids[0]}")
        if not email_ids[0]:
            if self.logger: self.logger.info(f"Aucun email n'a été trouvé.")
            return []
        email_ids = email_ids[0].split()
        if emailSubject:
            for e_id in email_ids:
                status, msg_data = imap_conn.fetch(e_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject = msg.get("Subject", "")
                        if re.search(emailSubject, subject) or emailSubject.upper() in subject.upper():
                            matching_emails.append(e_id)
            if len(matching_emails)==0:
                if self.logger: self.logger.info("Aucun mail, n'a été trouvé.")
        else:
            matching_emails = email_ids
            if self.logger: self.logger.info(f"{len(email_ids)} mail(s) trouvé(s).")
        return matching_emails

    def read_email(self,email_id, get_attachment = False):
        if self.logger: self.logger.info(f"Tentative de lecture de l'email {email_id}.")
        imap_conn = self.__connection
        status, msg_data = imap_conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            if self.logger: self.logger.error(f"Erreur lors de la lecture de l'email {email_id}.")
            raise
        if  msg_data[0]:
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email, policy=policy.default)
            if self.logger: self.logger.info(f"Contenu de l'email {email_id} correctement lu.")
            message=""
            for part in msg.walk():
                if part.get_content_type() in ["text/plain", "text/html"]:
                    raw = part.get_payload(decode=True)
                    encoding = chardet.detect(raw)["encoding"] or part.get_content_charset() or "utf-8"
                    if self.logger: self.logger.debug(f"Encodage détecté : {encoding} pour {part.get_content_type()}")
                    try:
                        message = raw.decode(encoding, errors='replace')
                    except LookupError:
                        message = raw.decode("iso-8859-1", errors='replace')
            if self.logger is not None and len(message) == 0: self.logger.info(f"Le contenu du mail est vide.")
            if not get_attachment:
                return {"message":message}
            else:
                data = self.__get_attachment(msg)
                return {"message": message, "attachement": data}
        else:
            if self.logger: self.logger.info(f"Le contenu du mail {email_id} est vide.")

    def __get_attachment(self, msg):
        lst = []
        if self.logger: self.logger.info(f"Récupération des pièces jointes.")
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename:
                    if self.logger: self.logger.info(f"Téléchargement de la pièce jointe : {filename}.")
                    raw = part.get_payload(decode=True)
                    mime_type, _ = mimetypes.guess_type(filename)
                    is_text = mime_type and mime_type.startswith("text")
                    binary = not is_text
                    encoding = None
                    content = raw
                    if is_text:
                        encoding = chardet.detect(raw)["encoding"]
                        if self.logger: self.logger.debug(f"Encodage détecté pour {filename}: {encoding}")
                        if encoding:
                            try:
                                content = raw.decode(encoding)
                                binary = False
                            except UnicodeDecodeError:
                                if self.logger: self.logger.error(
                                    f"Échec du décodage avec {encoding} pour {filename}. Enregistrement en binaire.")
                    lst.append({
                        "filename": filename,
                        "content": content,
                        "is_binary": binary,
                        "encoding": encoding if not binary else "binary"
                    })
        if self.logger and not lst: self.logger.info(f"Aucune pièce jointe n'a été trouvée.")
        return lst

    def logout(self):
        self.__connection.logout()