from sqlalchemy import Column, Integer, String
from app.database import Base


class DBVenueEvent(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(50))

    def __repr__(self):
        return "<DBVenueEvent(event_id='%s')>" % (self.event_id)


class DBArtistEvent(Base):
    __tablename__ = "artists"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(50))
    artist_name = Column(String(50))

    def __repr__(self):
        return "<DBArtistEvent(event_id='%s', artist_name='%s')>" % (
            self.event_id,
            self.artist_name,
        )
