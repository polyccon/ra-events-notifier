# encoding: utf-8

import backoff
import base64
import datetime
import json
import requests

from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from googleapiclient import discovery
from googleapiclient.errors import HttpError

from sqlalchemy_utils import database_exists

from bs4 import BeautifulSoup

from app.database import Database
from app.event import Event
from app.logger import Logger
from app.user import User


class App:
    DEBUG = False

    if DEBUG:
        CONFIG_PATH = "testing_config.json"
    else:
        CONFIG_PATH = "config.json"

    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)

    logger = Logger.get(__name__)

    def main(self):
        if not database_exists(self.CONFIG["database_url"]):
            self.logger.info("Creating new database")
            Database.init_db(self.CONFIG["database_url"])
        self.logger.info("Connecting to the database")
        db = Database.from_url(self.CONFIG["database_url"])

        users = self.update_users_preferences(db)

        venues = db.get_distinctive_items("venue")
        artists = db.get_distinctive_items("artist")
        promoters = db.get_distinctive_items("promoter")

        # go through venues
        new_events = []
        for venue in venues:
            self.logger.info(f"Checking {venue['name']} venue...")

            venue["type"] = "venue"
            venue_events = self.get_events(
                venue, self.CONFIG["venue_url_prefix"] + venue["tag"]
            )
            new_venue_events = self.add_to_database(db, venue_events)
            new_events.extend(new_venue_events)

        for artist in artists:
            self.logger.info(f"Checking {artist['name']} artist...")

            artist["type"] = "artist"
            artist_events = self.get_events(
                artist, self.CONFIG["artist_url_prefix"] + artist["tag"]
            )
            new_artist_events = self.add_to_database(db, artist_events)
            new_events.extend(new_artist_events)

        for promoter in promoters:
            self.logger.info(f"Checking {promoter['name']} promoter...")

            promoter["type"] = "promoter"
            promoter_events = self.get_events(
                promoter, self.CONFIG["promoter_url_prefix"] + promoter["tag"]
            )
            new_promoter_events = self.add_to_database(db, promoter_events)
            new_events.extend(new_promoter_events)

        db.commit()

        for new_event in new_events:
            self.add_event_notifications(new_event, users)
        self.send_emails(users)

    def update_users_preferences(self, db):
        self.logger.info("Downloading users favourites")
        users = self.get_users()
        users = self.download_users_interests(users)

        self.logger.info("Updating users database")
        self.update_database(users, db)

        return users

    def get_users(self):
        with open(self.CONFIG["users_path"]) as f:
            users_json = json.load(f)
        users = []
        for user_data in users_json["users"]:
            users.append(
                User(
                    user_data["name"],
                    user_data["nickname"],
                    user_data["email"],
                    user_data["locations"],
                )
            )
        return users

    def download_users_interests(self, users):
        with requests.Session() as s:
            s.post(self.CONFIG["login_url"], data=self.CONFIG["payload"])

            for user in users:
                self.logger.info(f"Fetching user {user.nickname} preferences")
                url = self.CONFIG["profile_prefix"] + user.nickname + "/favourites"
                html = s.get(url)
                html.encoding = "utf-8"
                soup = BeautifulSoup(html.text, "html.parser")

                html_artists = soup.find_all("div", class_="fav")
                for artist in html_artists:
                    info_tag = artist.find("div", class_="pb2").find("a")
                    artist_name = info_tag.get_text()
                    artist_tag = info_tag.get("href")[4:]
                    user.add_artist(artist_name, artist_tag)

                html_venues = soup.find("ul", class_="list venueListing").find_all(
                    "li", recursive=False
                )
                for venue in html_venues:
                    info_tag = venue.find_all("a")[1]
                    venue_name = info_tag.get_text()
                    venue_tag = info_tag.get("href")[14:]
                    user.add_venue(venue_name, venue_tag)

                html_promoters = soup.find_all("ul", class_="list")[-1].find_all(
                    "li", recursive=False
                )
                for promoter in html_promoters:
                    info_tag = promoter.find_all("a")[1]
                    promoter_name = info_tag.get_text()
                    promoter_tag = info_tag.get("href")[18:]
                    user.add_promoter(promoter_name, promoter_tag)
        return users

    def update_database(self, users, db):
        for user in users:
            db.update_user(user)

    def get_events(self, entity, url):
        html = requests.get(url)
        html.encoding = "utf-8"

        soup = BeautifulSoup(html.text, "html.parser")

        events_html = soup.find_all("article", class_="event-item")

        events = []
        for event_html in events_html:
            try:
                if entity["type"] is "venue":
                    event = Event.from_venue_html(entity["name"], event_html)
                elif entity["type"] is "artist":
                    event = Event.from_artist_html(entity["name"], event_html)
                elif entity["type"] is "promoter":
                    event = Event.from_promoter_html(entity["name"], event_html)
            except:
                self.logger.warning(
                    f"Could not generate event from the following html: {event_html.get_text()}"
                )
            events.append(event)
        return events

    def add_to_database(self, db, events):
        new_events = []
        for event in events:
            event_in_database = db.fetch_from_database(event.event_id, event.event_type)

            if event_in_database is not None and event_in_database.tickets_available:
                continue

            event.tickets = self.get_tickets(event.event_url)
            tickets_available = (True, False)[not event.tickets]

            # If event is not in db, add
            if event_in_database is None:
                db.add_event(event.event_id, event.event_type, tickets_available)
                self.logger.info(
                    f"NEW EVENT WITH URL {event.event_url} IS ADDED TO THE DATABASE. TICKETS: {tickets_available}"
                )
                new_events.append(event)
            # The event was in database but didn't have tickets
            else:
                if tickets_available:
                    db.update_event(event.event_id, event.event_type, tickets_available)
                    self.logger.info(
                        f"EVENT WITH URL {event.event_url} WAS UPDATED WITH TICKETS"
                    )
                    new_events.append(event)
        return new_events

    def get_tickets(self, event_url):
        html = requests.get(event_url)
        html.encoding = "utf-8"
        soup = BeautifulSoup(html.text, "html.parser")

        tickets = []
        try:
            html_tickets = soup.find_all("li", class_="onsale but")
            for html_ticket in html_tickets:
                p = html_ticket.find("p")
                tickets.append(
                    {
                        "name": p.find(text=True, recursive=False),
                        "price": p.find("span").get_text(),
                    }
                )
        except:
            self.logger.warning(f"some problem getting tickets for {event_url}")
        return tickets

    def add_event_notifications(self, event, users):
        for user in users:
            user.add_to_email(event)

    def send_emails(self, users):
        service = discovery.build("gmail", "v1", credentials=self.make_credentials())

        for user in users:
            if user.number_of_new_events == 0:
                continue
            user.add_email_ending()
            self.logger.info(f"Emailing {user.email}")
            message = MIMEMultipart()
            message["From"] = "me"
            message["Subject"] = "New events on RA"
            message["To"] = user.email
            message.attach(MIMEText(user.email_body.get(), "html"))
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {"raw": raw_message}
            self.send_email_request(service, body)
        return

    def make_credentials(self):
        with open(self.CONFIG["credentials_path"]) as f:
            data = json.load(f)

        return Credentials(
            None,
            refresh_token=data["refresh_token"],
            client_id=data["installed"]["client_id"],
            client_secret=data["installed"]["client_secret"],
            token_uri=data["installed"]["token_uri"],
        )

    @backoff.on_exception(backoff.expo, HttpError, max_tries=4)
    def send_email_request(self, service, body):
        service.users().messages().send(userId="me", body=body).execute()
