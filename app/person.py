class Person:
    def __init__(self, name, email, venues, artists):
        self.name = name
        self.email = email
        self.venues = venues
        self.artists = artists
        self.email_body = ""

    def add_to_email(self, message):
        if self.email_body == "":
            self.email_body += f"Hi <b>{self.name},</b> <br><br><br>"
        self.email_body += message

    def add_email_ending(self):
        venues_list = ", ".join(self.venues)
        artists_list = ", ".join(self.artists)
        emoji = "\u2764"
        message = f"Your venues: <br> \
                <b>{venues_list}</b> <br><br>Your artists: <br> \
                <b>{artists_list}</b> <br><br> \
                If you want anything removed from or added to this list, \
                reply to this email. {emoji}"
        self.email_body += message
