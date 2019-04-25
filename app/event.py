import requests
from bs4 import BeautifulSoup


class Event:
    def __init__(
        self,
        name,
        venue,
        lineup,
        date,
        promoter,
        artist,
        event_id,
        event_url,
        event_type,
    ):
        self.name = name
        self.venue = venue
        self.lineup = lineup
        self.date = date
        self.promoter = promoter
        self.artist = artist
        self.event_id = event_id
        self.event_url = event_url
        self.event_type = event_type

    @classmethod
    def from_venue_html(cls, venue, event_html):
        EVENT_URL_PREFIX = "https://www.residentadvisor.net/events/"

        link = event_html.find("a")
        name = event_html.find("span", class_="title").get_text()
        date = event_html.find("div", class_="bbox").find("h1").get_text()
        promoter = ""
        artist = ""
        event_id = link.get("href")[-7:]
        event_url = EVENT_URL_PREFIX + event_id
        event_type = "venue"
        try:
            lineup = event_html.find("div", class_="event-lineup").get_text()
        except:
            lineup = ""

        return cls(
            name, venue, lineup, date, promoter, artist, event_id, event_url, event_type
        )

    @classmethod
    def from_artist_html(cls, artist, event_html):
        EVENT_URL_PREFIX = "https://www.residentadvisor.net/events/"

        link = event_html.find("a")
        name = event_html.find("span", class_="title").get_text()
        venue_html = (
            event_html.find("div", class_="bbox")
            .find("h1", class_="title")
            .find_all("span")[2]
            .find_all("a")
        )
        venue = ""
        for item in venue_html:
            venue += item.get_text() + ", "
        venue = venue[:-2]
        lineup = ""
        date = event_html.find("div", class_="bbox").find("h1").get_text()
        promoter = ""
        event_id = link.get("href")[-7:]
        event_url = EVENT_URL_PREFIX + event_id
        event_type = "artist"

        return cls(
            name, venue, lineup, date, promoter, artist, event_id, event_url, event_type
        )

    @classmethod
    def from_promoter_html(cls, promoter, event_html):
        EVENT_URL_PREFIX = "https://www.residentadvisor.net/events/"

        link = event_html.find("a")
        name = event_html.find("span", class_="title").get_text()
        venue_html = (
            event_html.find("div", class_="bbox")
            .find("h1", class_="title")
            .find_all("span")[2]
            .find_all("a")
        )
        venue = ""
        for item in venue_html:
            venue += item.get_text() + ", "
        venue = venue[:-2]

        date = event_html.find("div", class_="bbox").find("h1").get_text()
        artist = ""
        event_id = link.get("href")[-7:]
        event_url = EVENT_URL_PREFIX + event_id
        event_type = "promoter"
        try:
            lineup = event_html.find("div", class_="event-lineup").get_text()
        except:
            lineup = ""

        return cls(
            name, venue, lineup, date, promoter, artist, event_id, event_url, event_type
        )
