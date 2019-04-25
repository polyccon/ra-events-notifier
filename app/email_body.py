class EmailBody:
    def __init__(self, name):
        self.message = f"Hi <b>{name},</b> <br><br><br>"

    def add_venue_event(self, event):
        self.message += f"<p> New event at <b>{event.venue}</b> \
        named <i>{event.name}</i> \
        with a lineup of <b>{event.lineup}</b> \
        on {event.date} has been added here: {event.event_url}<br>"

    def add_artist_event(self, event):
        self.message += f"<p>New event: <b>{event.artist}</b> \
        is playing at <b>{event.venue}</b> on {event.date} \
        at the night called <i>{event.name}</i>. \
        Find it here: {event.event_url}<br>"

    def add_promoter_event(self, event):
        self.message += f"<p> New promoter <b>{event.promoter}</b> event at \
        <b>{event.venue}</b> named <i>{event.name}</i> \
        with a lineup of <b>{event.lineup}</b> \
        on {event.date} has been added here: {event.event_url}<br>"

    def add_tickets(self, tickets):
        tickets_message = ""
        if tickets:
            tickets_message += "<b>Tickets currently on sale:</b><br>"
            for ticket in tickets:
                name = ticket["name"]
                price = ticket["price"]
                tickets_message += f"    <u>{name}</u>: {price}<br>"
        tickets_message += "<br>"
        self.message += tickets_message

    def add_ending(self, venues_list, artists_list, promoters_list, locations_list):
        emoji = "\u2764"
        ending = f"<br><br>Your venues: <br> <b>{venues_list}</b> <br><br> \
                Your promoters: <br> <b>{promoters_list}</b> <br><br> \
                Your artists: <br> <b>{artists_list}</b> <br><br> \
                Your new artist events locations: <br> \
                <b>{locations_list}</b> <br><br> \
                Thanks for supporting this tech. {emoji}"
        self.message += ending

    def get(self):
        return self.message
