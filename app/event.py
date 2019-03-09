import requests
from bs4 import BeautifulSoup


class Event:
    def __init__(self, name, lineup, date, event_id, event_url):
        self.name = name
        self.lineup = lineup
        self.date = date
        self.event_id = event_id
        self.event_url = event_url

    @classmethod
    def from_html(cls, event_html):
        EVENT_URL_PREFIX = "https://www.residentadvisor.net/events/"

        link = event_html.find("a")
        name = event_html.find("span", class_="title").get_text()
        date = event_html.find("div", class_="bbox").find("h1").get_text()
        event_id = link.get("href")[-7:]
        event_url = EVENT_URL_PREFIX + event_id
        try:
            lineup = event_html.find("div", class_="event-lineup").get_text()
        except:
            lineup = ""

        return cls(name, lineup, date, event_id, event_url)
