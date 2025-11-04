from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from database import db
from models import Flight, Booking
from utils import generate_pnr

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


@app.before_first_request
def create_tables():
    db.create_all()
    if Flight.query.count() == 0:
        sample_flights = [
            Flight("AI101", "Delhi", "Mumbai", "2025-11-10 09:00", 100, 4500),
            Flight("AI202", "Chennai", "Delhi", "2025-11-10 14:00", 80, 5200),
            Flight("AI303", "Bangalore", "Kolkata", "2025-11-11 18:30", 60, 6100)
        ]
        db.session.add_all(sample_flights)
        db.session.commit()

# ---------------- FRONTEND ROUTES ----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/booking')
def booking_page():
    return render_template('booking.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

# ---------------- BACKEND API ----------------
@app.route('/api/flights', methods=['GET'])
def get_flights():
    src = request.args.get('source')
    dst = request.args.get('destination')
    query = Flight.query
    if src:
        query = query.filter_by(source=src)
    if dst:
        query = query.filter_by(destination=dst)
    flights = query.all()
    return jsonify([{
        'id': f.id,
        'flight_number': f.flight_number,
        'source': f.source,
        'destination': f.destination,
        'departure_time': f.departure_time,
        'available_seats': f.available_seats,
        'price': f.price
    } for f in flights])

@app.route('/api/book', methods=['POST'])
def book_flight():
    data = request.get_json()
    passenger = data.get('passenger_name')
    flight_id = data.get('flight_id')
    seats = data.get('seats', 1)
    flight = Flight.query.get(flight_id)
    if not flight:
        return jsonify({'error': 'Flight not found'}), 404
    if flight.available_seats < seats:
        return jsonify({'error': 'Not enough seats available'}), 400
    try:
        flight.available_seats -= seats
        pnr = generate_pnr()
        total = flight.price * seats
        booking = Booking(
            pnr=pnr,
            passenger_name=passenger,
            flight_id=flight.id,
            seats_booked=seats,
            total_amount=total,
            status="CONFIRMED"
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify({'message': 'Booking successful', 'pnr': pnr, 'total_amount': total})
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Transaction failed, please retry'}), 500

@app.route('/api/cancel/<pnr>', methods=['POST'])
def cancel_booking(pnr):
    booking = Booking.query.filter_by(pnr=pnr).first()
    if not booking:
        return jsonify({'error': 'Invalid PNR'}), 404
    if booking.status == 'CANCELLED':
        return jsonify({'message': 'Already cancelled'})
    booking.status = 'CANCELLED'
    flight = Flight.query.get(booking.flight_id)
    flight.available_seats += booking.seats_booked
    db.session.commit()
    return jsonify({'message': 'Booking cancelled successfully', 'pnr': pnr})

@app.route('/api/bookings', methods=['GET'])
def booking_history():
    all_bookings = Booking.query.all()
    return jsonify([{
        'pnr': b.pnr,
        'passenger_name': b.passenger_name,
        'flight_id': b.flight_id,
        'seats_booked': b.seats_booked,
        'total_amount': b.total_amount,
        'status': b.status,
        'created_at': b.created_at.strftime('%Y-%m-%d %H:%M')
    } for b in all_bookings])

if __name__ == '__main__':
    app.run(debug=True)
