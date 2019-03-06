class ArtistEvent:
    def __init__(self, name, venue, date, event_id, event_url):
        self.name = name
        self.venue = venue
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

        return cls(name, venue, date, event_id, event_url)
