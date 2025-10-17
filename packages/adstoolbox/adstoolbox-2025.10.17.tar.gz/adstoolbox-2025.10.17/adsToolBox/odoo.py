import xmlrpc.client

class OdooConnector:
    def __init__(self, dictionnary: dict, logger):
        """
        Classe pour se connecter à Odoo via xmlrpc et exécuter des opérations CRUD
        :param dictionnary: Un dictionnaire contenant tous les paramètres nécéssaires pour lancer une connexion Odoo
        :param logger: Un logger ads qui va gérer les logs des actions de la classe
        """
        self.models = None
        self.uid = None
        self.common = None
        self.name = dictionnary['name']
        self.url = dictionnary['url']
        self.db = dictionnary['db']
        self.user = dictionnary['user']
        self.password = dictionnary['password']
        self.logger = logger

    def connect(self):
        """
        Lance la connection à Odoo
        """
        try:
            self.logger.info("Tentative de connexion à Odoo...")
            self.common = xmlrpc.client.ServerProxy('{}/xmlrpc/common'.format(self.url))
            self.uid = self.common.authenticate(self.db, self.user, self.password, {})
            if not self.uid:
                msg = "Échec de l'authentification, identifiants incorrects."
                self.logger.error(msg)
                raise Exception(msg)
            self.models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(self.url))
            self.logger.info(f"Connexion à Odoo réussie.")
            self.logger.debug(f"Connecté en tant que {self.user} (UID: {self.uid})")
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion à Odoo : {e}")
            raise

    def __str__(self):
        """
        Retourne le nom de la connexion Odoo
        """
        return f"Connexion Odoo: {self.name}"

    def desc(self, table: str):
        """
        Retourne la description des champs d'une table Odoo
        :param table: Le nom du modèle
        :return: Un dictionnaire qui contient les informations sur les champs
        """
        try:
            self.logger.info(f"Récupération des informations de la table: {table}")
            fields = self.models.execute_kw(
                self.db, self.uid, self.password, table, 'fields_get', [], {'attributes': ['string', 'help', 'type']}
            )
            self.logger.info(f"Descriptions récupérées pour la table: {table}")
            return fields
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des descriptions: {e}")
            raise

    def get(self, table, fields, filter):
        """
        Récupère des enregistrements dans Odoo avec un filtre
        :param table: Le nom du modèle Odoo
        :param fields: Une liste de champs à récupérer
        :param filter: Un filtre Odoo
        :return: Une liste d'enregistrements correspondant au filtre
        """
        try:
            self.logger.info(f"Récupération des enregistrements depuis la table {table} avec le filtre: {filter}")
            records = self.models.execute_kw(
                self.db, self.uid, self.password, table, 'search_read', [filter], {'fields': fields}
            )
            self.logger.info(f"{len(records)} enregistrement(s) récupérés depuis {table}")
            return records
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des enregistrements depuis {table}: {e}")
            raise

    def put(self, table: str, lines: []):
        """
        Insère de nouveaux enregistrements dans Odoo
        :param table: Le nom du modèle où insérer
        :param lines: Une liste contenant les données à insérer
        :return: Une liste d'IDs des enregistrements crées
        """
        try:
            self.logger.info(f"Insertion de {len(lines)} enregistrements dans {table}")
            ids = []
            for line in lines:
                id = self.models.execute_kw(
                    self.db, self.uid, self.password, table, 'create', [line]
                )
                ids.append(id)
                self.logger.info(f"Enregistrement(s) inséré(s) avec succès, ID: {id}")
            return ids
        except Exception as e:
            self.logger.error(f"Erreur lors de l'insertion dans {table}: {e}")
            raise
