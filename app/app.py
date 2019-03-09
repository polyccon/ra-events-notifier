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
    DEBUG = False

    if DEBUG:
        CONFIG_PATH = "testing_config.json"
    else:
        CONFIG_PATH = "config.json"

    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)

    def main(self):
        venues_map, artists_map = self.get_mapping(self.CONFIG["mapping_path"])
        people, all_venues, all_artists = self.get_interests(
            self.CONFIG["interests_path"]
        )

        if not database_exists(self.CONFIG["database_url"]):
            Database.init_db(self.CONFIG["database_url"])

        db = Database.from_url(self.CONFIG["database_url"])

        # go through venues
        number_of_new_events = 0
        for venue_name in all_venues:
            print(f"Checking {venue_name} venue...")

            venue_id = venues_map[venue_name]

            url = self.CONFIG["venue_url_prefix"] + venue_id

            html = requests.get(url)
            html.encoding = "utf-8"

            soup = BeautifulSoup(html.text, "html.parser")

            html_events = soup.find_all("article", class_="event-item")

            for html_event in html_events:
                try:
                    event = Event.from_html(html_event)
                except:
                    print(
                        f"Could not generate event from the following html: {html_event.get_text()}"
                    )

                if event.event_id is not None:
                    if not db.in_venues_database(event.event_id):
                        print(
                            f"NEW EVENT WITH ID {event.event_id} WILL BE ADDED TO THE DATABASE"
                        )
                        # Add the ticket prices to the event
                        event.tickets = self.get_tickets(event.event_url)
                        db.add_venue_event(event.event_id)
                        number_of_new_events += 1

                        message = self.compose_message(
                            event, name=venue_name, event_type="venue"
                        )
                        self.add_venue_notification(venue_name, message, people)
        print(
            f"{number_of_new_events} NEW EVENTS FOUND AT {str(datetime.datetime.now())}"
        )

        # go through artists
        number_of_new_artist_events = 0
        for artist_name in all_artists:
            print(f"Checking {artist_name} artist...")

            artist_id = artists_map[artist_name]

            url = self.CONFIG["artist_url_prefix"] + artist_id

            html = requests.get(url)
            html.encoding = "utf-8"

            soup = BeautifulSoup(html.text, "html.parser")

            html_events = soup.find_all("article", class_="event-item")

            for html_event in html_events:
                try:
                    event = ArtistEvent.from_html(html_event)
                except:
                    print(
                        f"Could not generate event from the following html: {html_event.get_text()}"
                    )

                if event.event_id is not None:
                    if not db.in_artists_database(event.event_id, artist_name):
                        print(
                            f"NEW EVENT WITH ID {event.event_id} WILL BE ADDED TO THE DATABASE"
                        )
                        # Add the ticket prices to the event
                        event.tickets = self.get_tickets(event.event_url)
                        db.add_artist_event(event.event_id, artist_name)
                        number_of_new_artist_events += 1

                        message = self.compose_message(
                            event, name=artist_name, event_type="artist"
                        )
                        self.add_artist_notification(
                            artist_name, event, message, people
                        )
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
                    person["name"],
                    person["email"],
                    person["venues"],
                    person["artists"],
                    person["locations"],
                )
            )
            all_venues.extend(person["venues"])
            all_artists.extend(person["artists"])

        # remove duplicates and return
        all_venues = list(dict.fromkeys(all_venues))
        all_artists = list(dict.fromkeys(all_artists))

        return people, all_venues, all_artists

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
            print(f"some problem getting tickets for {event_url}")
        return tickets

    def compose_message(self, event, name, event_type):
        message = ""
        if event_type == "venue":
            message += f"<p> New event at <b>{name}</b> \
            named <i>{event.name}</i> \
            with a lineup of <b>{event.lineup}</b> \
            on {event.date} has been added here: {event.event_url}<br>"

        if event_type == "artist":
            message += f"<p>New event: <b>{name}</b> \
            is playing at <b>{event.venue}</b> on {event.date} \
            at the night called <i>{event.name}</i>. \
            Find it here: {event.event_url}<br>"

        if event.tickets:
            message += "<b>Tickets currently on sale:</b><br>"
            for ticket in event.tickets:
                name = ticket["name"]
                price = ticket["price"]
                message += f"    <u>{name}</u>: {price}<br>"
        message += "<br>"

        return message

    def add_venue_notification(self, venue, message, people):
        for person in people:
            if venue in person.venues:
                person.add_to_email(message)

    def add_artist_notification(self, artist_name, event, message, people):
        for person in people:
            if not artist_name in person.artists:
                return
            for location in person.locations:
                if location in event.venue:
                    person.add_to_email(message)

    def send_emails(self, people):
        service = discovery.build("gmail", "v1", credentials=self.make_credentials())

        for person in people:
            if person.email_body == "":
                continue
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
