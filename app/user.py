class User:
    def __init__(self, name, nickname, email, locations):
        self.name = name
        self.nickname = nickname
        self.email = email
        self.locations = locations
        self.artists = []
        self.venues = []
        self.promoters = []
        self.email_body = ""

    def add_artist(self, artist_name, artist_id):
        self.artists.append({"name": artist_name, "id": artist_id})

    def add_venue(self, venue_name, venue_id):
        self.venues.append({"name": venue_name, "id": venue_id})

    def add_promoter(self, promoter_name, promoter_id):
        self.promoters.append({"name": promoter_name, "id": promoter_id})

    def add_to_email(self, message):
        if self.email_body == "":
            self.email_body += f"Hi <b>{self.name},</b> <br><br><br>"
        self.email_body += message

    def add_email_ending(self):
        venues_list = ", ".join(self.venues)
        artists_list = ", ".join(self.artists)
        if not self.locations:
            locations_list = "Worldwide"
        else:
            locations_list = ", ".join(self.locations)
        emoji = "\u2764"
        message = f"Your venues: <br> \
                <b>{venues_list}</b> <br><br>Your artists: <br> \
                <b>{artists_list}</b> <br><br> \
                Your new artist events locations: <br> \
                <b>{locations_list}</b> <br><br> \
                If you want anything removed from or added to this list, \
                reply to this email. {emoji}"
        self.email_body += message
