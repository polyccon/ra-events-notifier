from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()

from app.models import DBVenueEvent
from app.models import DBArtistEvent


class Database:
    def __init__(self, session):
        self.session = session

    def in_venues_database(self, event_id):
        if (
            self.session.query(DBVenueEvent).filter_by(event_id=event_id).first()
            is None
        ):
            return False
        return True

    def in_artists_database(self, event_id, artist_name):
        if (
            self.session.query(DBArtistEvent)
            .filter_by(event_id=event_id, artist_name=artist_name)
            .first()
            is None
        ):
            return False
        return True

    def add_venue_event(self, event_id):
        event = DBVenueEvent(event_id=event_id)
        self.session.add(event)

    def add_artist_event(self, event_id, artist_name):
        event = DBArtistEvent(event_id=event_id, artist_name=artist_name)
        self.session.add(event)

    def commit(self):
        self.session.commit()

    @classmethod
    def from_url(cls, database_url):
        engine = create_engine(database_url, echo=False)
        Session = sessionmaker(bind=engine)
        session = Session()
        return cls(session)

    @classmethod
    def init_db(cls, database_url):
        create_database(database_url)
        engine = create_engine(database_url, echo=True)
        Base.metadata.create_all(engine)
