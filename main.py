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

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

from bs4 import BeautifulSoup

CREDENTIALS_PATH = "credentials.json"
INTERESTS_PATH = "interests.json"

DATABASE_URL = "sqlite:///events.db"
TABLE_NAME = "events"

URL_PRE = "https://www.residentadvisor.net/club.aspx?id="
EVENT_URL_PRE = "https://www.residentadvisor.net/events/"

with open(INTERESTS_PATH) as f:
    interests_data = json.load(f)

venues = interests_data["venues"]
emails = interests_data["emails"]


def main():
    Base = declarative_base()

    class Event(Base):
        __tablename__ = TABLE_NAME

        id = Column(Integer, primary_key=True)
        event_id = Column(String(50))

        def __repr__(self):
            return "<Event(event_id='%s')>" % (self.event_id)

    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)
        engine = create_engine(DATABASE_URL, echo=True)
        Base.metadata.create_all(engine)

    engine = create_engine(DATABASE_URL, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    email_body = ""
    number_of_new_events = 0

    for venue_name, venue_id in venues.items():
        print(f"Checking {venue_name} venue...")

        url = URL_PRE + venue_id

        html = requests.get(url)
        html.encoding = "utf-8"

        soup = BeautifulSoup(html.text, "html.parser")

        events = soup.find_all("article", class_="event-item")

        for event in events:
            link = event.find("a")
            name = event.find("span", class_="title").get_text()
            lineup = event.find("div", class_="event-lineup").get_text()
            date = event.find("div", class_="bbox").find("h1").get_text()

            if link is not None:
                event_id = link.get("href")[-7:]
                event_object = Event(event_id=event_id)
                if session.query(Event).filter_by(event_id=event_id).first() is None:
                    print(f"NEW EVENT WITH ID {event_id} WILL BE ADDED TO THE DATABASE")
                    session.add(event_object)
                    event_url = EVENT_URL_PRE + event_id
                    number_of_new_events += 1
                    email_body += f"<p> New event at <b>{venue_name}</b> named <i>{name}</i> with a lineup of <b>{lineup}</b> on {date} has been added here: {event_url}<br><br>"
    session.commit()
    if number_of_new_events > 0:
        send_emails(email_body)
    print(f"{number_of_new_events} NEW EVENTS FOUND AT {str(datetime.datetime.now())}")


def make_credentials():
    with open(CREDENTIALS_PATH) as f:
        data = json.load(f)

    return Credentials(
        None,
        refresh_token=data["refresh_token"],
        client_id=data["installed"]["client_id"],
        client_secret=data["installed"]["client_secret"],
        token_uri=data["installed"]["token_uri"],
    )


def send_emails(email_body):
    service = discovery.build("gmail", "v1", credentials=make_credentials())

    # loop over email addresses and send them separately so that the list stays hidden
    for email in emails:
        print(f"Emailing {email}")
        message = MIMEMultipart()
        message["From"] = "me"
        message["Subject"] = "New events on RA"
        message["To"] = email
        message.attach(MIMEText(email_body, "html"))
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {"raw": raw_message}
        send_email_request(service, body)
    return


@backoff.on_exception(backoff.expo, HttpError, max_tries=4)
def send_email_request(service, body):
    service.users().messages().send(userId="me", body=body).execute()


main()
