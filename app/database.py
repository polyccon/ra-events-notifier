from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import database_exists, create_database

Base = declarative_base()

from app.models import DBEvent
from app.models import DBUser
from app.models import DBLocation
from app.models import DBArtist
from app.models import DBVenue
from app.models import DBPromoter
from app.logger import Logger


class Database:
    def __init__(self, session):
        self.session = session
        self.logger = Logger.get(__name__)

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

    def update_user(self, user):
        db_user = self.session.query(DBUser).filter_by(nickname=user.nickname).first()
        if db_user is None:
            self.logger.info(f"Adding new user {user.nickname} to the database")
            db_user = DBUser(name=user.name, nickname=user.nickname, email=user.email)
            self.session.add(db_user)
            self.session.flush()
        self.session.query(DBVenue).filter_by(user_id=db_user.id).delete()
        self.session.query(DBArtist).filter_by(user_id=db_user.id).delete()
        self.session.query(DBPromoter).filter_by(user_id=db_user.id).delete()

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
                    name=artist["name"], tag=artist["tag"], user_id=db_user.id
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
                    name=venue["name"], tag=venue["tag"], user_id=db_user.id
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
                    name=promoter["name"], tag=promoter["tag"], user_id=db_user.id
                )
                self.session.add(db_promoter)
        self.session.commit()

    def get_distinctive_items(self, item_name):
        self.logger.info(f"Getting {item_name} items from the database")
        if item_name is "artist":
            item_object = DBArtist
        elif item_name is "venue":
            item_object = DBVenue
        elif item_name is "promoter":
            item_object = DBPromoter

        items = []
        for item in self.session.query(item_object.name, item_object.tag).distinct():
            items.append({"name": item[0], "tag": item[1]})
        return items

    def fetch_from_database(self, event_id, event_type):
        return (
            self.session.query(DBEvent)
            .filter_by(event_id=event_id, event_type=event_type)
            .first()
        )

    def add_event(self, event_id, event_type, tickets_available):
        event = DBEvent(
            event_id=event_id,
            event_type=event_type,
            tickets_available=tickets_available,
        )
        self.session.add(event)

    def update_event(self, event_id, event_type, tickets_available):
        event = (
            self.session.query(DBEvent)
            .filter_by(event_id=event_id, event_type=event_type)
            .first()
        )
        event.tickets_available = tickets_available

    def commit(self):
        self.session.commit()
