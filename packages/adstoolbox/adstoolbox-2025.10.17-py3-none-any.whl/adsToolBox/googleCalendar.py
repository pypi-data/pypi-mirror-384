import os
import datetime
import polars as pl
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

class GoogleCalendarConnector:
    def __init__(self, dictionnary: dict, logger):
        """
        Classe pour se connecter à l'API Google Calendar et récupérer des événements de calendrier.
        :param dictionnary: Un dictionnaire contenant les paramètres requis (comme les calendriers des collègues).
        :param logger: Un logger pour gérer les logs d'actions de la classe.
        """
        self.logger = logger
        self.scopes = dictionnary.get("scopes", ['https://www.googleapis.com/auth/calendar.readonly'])
        self.calendar_ids = dictionnary["calendar_ids"]
        self.token_file = dictionnary.get('token_file', 'token.json')
        self.credentials_file = dictionnary.get('credentials_file', 'credentials.json')
        self.service = None

    def __str__(self):
        """Retourne une représentation textuelle de l'objet GoogleCalendarConnector"""
        return f"Connexion Google Calendar avec les calendriers: {', '.join(self.calendar_ids)}"

    def connect(self):
        """Etablit la connexion à l'API Google Calendar."""
        try:
            self.logger.info("Tentative de connexion à Google Calendar...")
            creds = None
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            self.service = build('calendar', 'v3', credentials=creds)
            self.logger.info("Connexion à Google Calendar réussie.")
        except Exception as e:
            self.logger.error(f"Erreur lors de la connexion à Google Calendar: {e}")
            raise

    def get_events(self, max_results=10):
        """
        Récupère les événelents des calendriers des collègues spécifiés.
        :param max_results: Le nombre maximal d'événements à récupérer par calendrier
        :return: Un dictionnaire des événements pour chaque calendrier
        """
        try:
            now = datetime.datetime.now().isoformat() +  'Z'
            events_data = {}
            for calendar_id in self.calendar_ids:
                self.logger.info(f"Récupération des événements du calendrier: {calendar_id}")
                events_results = self.service.events().list(
                    calendarId=calendar_id,
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_results.get('items', [])
                events_data[calendar_id] = events
                self.logger.info(f"{len(events)} événement(s) récupéré(s) pour {calendar_id}")
            return events_data
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des événements: {e}")
            raise

    def save_events_to_csv(self, events_data, csv_filename='calendar_events.csv'):
        """
        Enregistre les événements dans un fichier csv en utilisant polars.
        :param events_data: Un dictionnaire contenant les événements par calendrier
        :param csv_filename: Le nom du csv
        """
        try:
            self.logger.info(f"Sauvegarde des événements dans le fichier CSV: {csv_filename}")
            data = {
                "Event Date": [],
                "Event Summary": [],
                "Owner Email": [],
                "Calendar Name": []
            }
            for calendar_id, events in events_data.items():
                for event in events:
                    data["Event Date"].append(event["start"].get("dateTime", event["start"].get("date")))
                    data["Event Summary"].append(event.get("summary", "No Summary"))
                    data["Owner Email"].append(event.get("organizer", {}).get('email', 'No Email Provided'))
                    data["Calendar Name"].append(event.get("organizer", {}).get("displayName", "No Name Provided"))
            df = pl.DataFrame(data)
            df.write_csv(csv_filename)
            self.logger.info(f"Les événements ont été sauvegardés dans {csv_filename}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des événements dans le CSV: {e}")
            raise