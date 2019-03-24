from app.email_body import EmailBody


class User:
    def __init__(self, name, nickname, email, locations):
        self.name = name
        self.nickname = nickname
        self.email = email
        self.locations = locations
        self.artists = []
        self.venues = []
        self.promoters = []
        self.email_body = EmailBody(name)
        self.number_of_new_events = 0

    def add_artist(self, artist_name, artist_tag):
        self.artists.append({"name": artist_name, "tag": artist_tag})

    def add_venue(self, venue_name, venue_tag):
        self.venues.append({"name": venue_name, "tag": venue_tag})

    def add_promoter(self, promoter_name, promoter_tag):
        self.promoters.append({"name": promoter_name, "tag": promoter_tag})

    def add_to_email(self, event):
        if event.event_type == "venue":
            if any(venue["name"] == event.venue for venue in self.venues):
                self.email_body.add_venue_event(event)
                self.email_body.add_tickets(event.tickets)
                self.number_of_new_events += 1
        elif event.event_type == "artist":
            if any(artist["name"] == event.artist for artist in self.artists):
                if not self.locations:  # notify if no location preference specified
                    self.email_body.add_artist_event(event)
                    self.email_body.add_tickets(event.tickets)
                    self.number_of_new_events += 1
                    return
                for location in self.locations:  # notify if location preference matches
                    if location in event.venue:
                        self.email_body.add_artist_event(event)
                        self.email_body.add_tickets(event.tickets)
                        self.number_of_new_events += 1
        elif event.event_type == "promoter":
            if any(promoter["name"] == event.promoter for promoter in self.promoters):
                self.email_body.add_promoter_event(event)
                self.number_of_new_events += 1

    def add_email_ending(self):
        venues_list = ", ".join(venue["name"] for venue in self.venues)
        artists_list = ", ".join(artist["name"] for artist in self.artists)
        promoters_list = ", ".join(promoter["name"] for promoter in self.promoters)
        if not self.locations:
            locations_list = "Worldwide"
        else:
            locations_list = ", ".join(self.locations)
        self.email_body.add_ending(
            venues_list, artists_list, promoters_list, locations_list
        )
