from database import db
from datetime import datetime

class Flight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), unique=True)
    source = db.Column(db.String(50))
    destination = db.Column(db.String(50))
    departure_time = db.Column(db.String(30))
    total_seats = db.Column(db.Integer)
    available_seats = db.Column(db.Integer)
    price = db.Column(db.Float)

    def __init__(self, flight_number, source, destination, departure_time, seats, price):
        self.flight_number = flight_number
        self.source = source
        self.destination = destination
        self.departure_time = departure_time
        self.total_seats = seats
        self.available_seats = seats
        self.price = price


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pnr = db.Column(db.String(10), unique=True)
    passenger_name = db.Column(db.String(100))
    flight_id = db.Column(db.Integer, db.ForeignKey('flight.id'))
    seats_booked = db.Column(db.Integer)
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(20), default='CONFIRMED')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
