from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()

from app.models import DBVenueEvent
from app.models import DBArtistEvent
from app.models import DBPromoterEvent
from app.models import DBUser
from app.models import DBLocation
from app.models import DBArtist
from app.models import DBVenue
from app.models import DBPromoter


class Database:
    def __init__(self, session):
        self.session = session

    def update_user(self, user):
        db_user = self.session.query(DBUser).filter_by(nickname=user.nickname).first()
        if db_user is None:
            print(f"Adding new user {user.nickname} to the database")
            db_user = DBUser(name=user.name, nickname=user.nickname, email=user.email)
            self.session.add(db_user)
            self.session.flush()
        for location in user.locations:
            if (
                self.session.query(DBLocation)
                .filter_by(name=location, user_id=db_user.id)
                .first()
                is None
            ):
                db_location = DBLocation(name=location, user_id=db_user.id)
                self.session.add(db_location)
        for artist in user.artists:
            if (
                self.session.query(DBArtist)
                .filter_by(name=artist["name"], user_id=db_user.id)
                .first()
                is None
            ):
                db_artist = DBArtist(
                    name=artist["name"], artist_id=artist["id"], user_id=db_user.id
                )
                self.session.add(db_artist)
        for venue in user.venues:
            if (
                self.session.query(DBVenue)
                .filter_by(name=venue["name"], user_id=db_user.id)
                .first()
                is None
            ):
                db_venue = DBVenue(
                    name=venue["name"], venue_id=venue["id"], user_id=db_user.id
                )
                self.session.add(db_venue)
        for promoter in user.promoters:
            if (
                self.session.query(DBPromoter)
                .filter_by(name=promoter["name"], user_id=db_user.id)
                .first()
                is None
            ):
                db_promoter = DBPromoter(
                    name=promoter["name"],
                    promoter_id=promoter["id"],
                    user_id=db_user.id,
                )
                self.session.add(db_promoter)
        self.session.commit()

    def get_distinctive_items(self, item_name):
        if item_name is "artist":
            item_object = DBArtist
        elif item_name is "venue":
            item_object = DBVenue
        elif item_name is "promoter":
            item_object = DBPromoter

        items = []
        for item in self.session.query(
            item_object.name, item_object.artist_id
        ).distinct():
            items.append({"name": item[0], "id": item[1]})
        return items

    def in_venues_database(self, event_id):
        if (
            self.session.query(DBVenueEvent).filter_by(event_id=event_id).first()
            is None
        ):
            return False
        return True

    def in_artists_database(self, event_id):
        if (
            self.session.query(DBArtistEvent).filter_by(event_id=event_id).first()
            is None
        ):
            return False
        return True

    def in_promoters_database(self, event_id):
        if (
            self.session.query(DBPromoterEvent).filter_by(event_id=event_id).first()
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
