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

from app.artist_event import ArtistEvent
from app.database import Database
from app.event import Event
from app.person import Person


class App:
    DEBUG = True

    CREDENTIALS_PATH = "/Users/sarunasnejus/Documents/cred/personal_credentials.json"
    MAPPING_PATH = "mapping.json"
    INTERESTS_PATH = "interests.json"

    if DEBUG:
        DATABASE_URL = "sqlite:///allevents_testing.db"
    else:
        DATABASE_URL = "sqlite:///allevents.db"

    VENUE_URL_PRE = "https://www.residentadvisor.net/club.aspx?id="
    ARTIST_URL_PRE = "https://www.residentadvisor.net/dj/"

    def main(self):
        venues_map, artists_map = self.get_mapping(self.MAPPING_PATH)
        people, all_venues, all_artists = self.get_interests(self.INTERESTS_PATH)

        if not database_exists(self.DATABASE_URL):
            Database.init_db(self.DATABASE_URL)

        db = Database.from_url(self.DATABASE_URL)

        # go through venues
        number_of_new_events = 0
        for venue_name in all_venues:
            print(f"Checking {venue_name} venue...")

            venue_id = venues_map[venue_name]

            url = self.VENUE_URL_PRE + venue_id

            html = requests.get(url)
            html.encoding = "utf-8"

            soup = BeautifulSoup(html.text, "html.parser")

            html_events = soup.find_all("article", class_="event-item")

            for html_event in html_events:
                event = Event.from_html(html_event)

                if event.event_id is not None:
                    if not db.in_venues_database(event.event_id):
                        print(
                            f"NEW EVENT WITH ID {event.event_id} WILL BE ADDED TO THE DATABASE"
                        )
                        db.add_venue_event(event.event_id)
                        number_of_new_events += 1

                        message = f"<p> New event at <b>{venue_name}</b> \
                        named <i>{event.name}</i> \
                        with a lineup of <b>{event.lineup}</b> \
                        on {event.date} has been added here: {event.event_url}<br><br>"
                        self.add_venue_notification(venue_name, message, people)
        print(
            f"{number_of_new_events} NEW EVENTS FOUND AT {str(datetime.datetime.now())}"
        )

        # go through artists
        number_of_new_artist_events = 0
        for artist_name in all_artists:
            print(f"Checking {artist_name} artist...")

            artist_id = artists_map[artist_name]

            url = self.ARTIST_URL_PRE + artist_id

            html = requests.get(url)
            html.encoding = "utf-8"

            soup = BeautifulSoup(html.text, "html.parser")

            html_events = soup.find_all("article", class_="event-item")

            for html_event in html_events:
                event = ArtistEvent.from_html(html_event)

                if event.event_id is not None:
                    if not db.in_artists_database(event.event_id, artist_name):
                        print(
                            f"NEW EVENT WITH ID {event.event_id} WILL BE ADDED TO THE DATABASE"
                        )
                        db.add_artist_event(event.event_id, artist_name)
                        number_of_new_artist_events += 1

                        message = f"<p>New event: <b>{artist_name}</b> \
                        is playing at <b>{event.venue}</b> on {event.date} \
                        at the night called <i>{event.name}</i>. \
                        Find it here: {event.event_url}<br><br>"
                        self.add_artist_notification(artist_name, message, people)
        db.commit()
        self.send_emails(people)
        print(
            f"{number_of_new_artist_events} NEW ARTIST EVENTS FOUND AT {str(datetime.datetime.now())}"
        )

    def get_mapping(self, mapping_path):
        with open(mapping_path) as f:
            mapping = json.load(f)
        return mapping["venues"], mapping["artists"]

    def get_interests(self, interests_path):
        with open(interests_path) as f:
            data = json.load(f)
        people = []
        all_venues = []
        all_artists = []
        for person_data in data.items():
            person = person_data[1]
            people.append(
                Person(
                    person["name"], person["email"], person["venues"], person["artists"]
                )
            )
            all_venues.extend(person["venues"])
            all_artists.extend(person["artists"])

        # remove duplicates and return
        all_venues = list(dict.fromkeys(all_venues))
        all_artists = list(dict.fromkeys(all_artists))

        return people, all_venues, all_artists

    def add_venue_notification(self, venue, message, people):
        for person in people:
            if venue in person.venues:
                person.add_to_email(message)

    def add_artist_notification(self, artist_name, message, people):
        for person in people:
            if artist_name in person.artists:
                person.add_to_email(message)

    def make_credentials(self):
        with open(self.CREDENTIALS_PATH) as f:
            data = json.load(f)

        return Credentials(
            None,
            refresh_token=data["refresh_token"],
            client_id=data["installed"]["client_id"],
            client_secret=data["installed"]["client_secret"],
            token_uri=data["installed"]["token_uri"],
        )

    def send_emails(self, people):
        service = discovery.build("gmail", "v1", credentials=self.make_credentials())

        if self.DEBUG:
            people = people[0:1]  # only email me
        for person in people:
            if person.email_body == "":
                return
            person.add_email_ending()
            print(f"Emailing {person.email}")
            message = MIMEMultipart()
            message["From"] = "me"
            message["Subject"] = "New events on RA"
            message["To"] = person.email
            message.attach(MIMEText(person.email_body, "html"))
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {"raw": raw_message}
            self.send_email_request(service, body)
        return

    @backoff.on_exception(backoff.expo, HttpError, max_tries=4)
    def send_email_request(self, service, body):
        service.users().messages().send(userId="me", body=body).execute()
