from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base


class DBUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    nickname = Column(String(50))
    email = Column(String(50))
    locations = relationship("DBLocation", backref="user")
    artists = relationship("DBArtist", backref="user")
    venues = relationship("DBVenue", backref="user")
    promoters = relationship("DBPromoter", backref="user")

    def __repr__(self):
        return f"<DBUser(name={self.name}, nickname={self.nickname}, email={self.email}, locations={self.locations}, artists={self.artists}, venues={self.venues}, promoters={self.promoters})>"


class DBLocation(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<DBLocation(name={self.name}, user_id={self.user_id})>"


class DBArtist(Base):
    __tablename__ = "artists"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    tag = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<DBArtist(name={self.name}, tag={self.tag}, user_id={self.user_id})>"


class DBVenue(Base):
    __tablename__ = "venues"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    tag = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<DBVenue(name={self.name}, tag={self.tag}, user_id={self.user_id})>"


class DBPromoter(Base):
    __tablename__ = "promoters"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    tag = Column(String(50))
    user_id = Column(Integer, ForeignKey("users.id"))

    def __repr__(self):
        return f"<DBPromoter(name={self.name}, tag={self.tag}, user_id={self.user_id})>"


class DBEvent(Base):
    __tablename__ = "venueevents"

    id = Column(Integer, primary_key=True)
    event_id = Column(String(50))
    event_type = Column(String(10))
    tickets_available = Column(Boolean)

    def __repr__(self):
        return f"<DBEvent(event_id={self.event_id}, \
                event_type={self.event_type}, \
                tickets_available={self.tickets_available})>"
