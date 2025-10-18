"""
Flight Search API (FastAPI) - single-file implementation
Features implemented:
1. Retrieve all flights
2. Search by origin, destination, date
3. Input validation and sorting (price or duration)
4. Simulated external airline schedule APIs
5. Dynamic pricing logic (remaining seats, time until departure, demand)
6. Integrate dynamic pricing into search results
7. Background process to simulate demand/availability changes
8. Optional fare history storage (enabled by config flag)

How to run:
1. python -m venv venv
2. source venv/bin/activate   # (on Windows: venv\Scripts\activate)
3. pip install fastapi uvicorn sqlmodel[sqlite] pydantic
4. uvicorn flight_search_api_fastapi:app --reload

Endpoints (examples):
- GET /flights
- GET /search?origin=DEL&destination=BOM&date=2025-10-20&sort_by=price&order=asc
- POST /external/fetch (simulate fetching schedules from external airlines)
- GET /external/airline/{airline}

"""
from datetime import datetime, timedelta, date
import threading
import time
import random
import uuid
from typing import Optional, List, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, conint
from sqlmodel import SQLModel, Field as ORMField, create_engine, Session, select

# -------------------------------
# Configuration
# -------------------------------
DB_FILE = "sqlite:///./flights.db"
ENABLE_FARE_HISTORY = True  # set False to skip storing history
BACKGROUND_UPDATE_INTERVAL_SEC = 10  # how often background simulation runs (seconds)

# -------------------------------
# Database models
# -------------------------------
class Flight(SQLModel, table=True):
    id: Optional[int] = ORMField(default=None, primary_key=True)
    flight_code: str = ORMField(index=True)
    airline: str
    origin: str = ORMField(index=True)
    destination: str = ORMField(index=True)
    departure: datetime = ORMField(index=True)
    arrival: datetime
    duration_mins: int
    seats_total: int
    seats_available: int
    base_fare: float
    current_fare: float
    demand_level: int  # 0..100

class FareHistory(SQLModel, table=True):
    id: Optional[int] = ORMField(default=None, primary_key=True)
    flight_id: int = ORMField(index=True)
    timestamp: datetime
    fare: float

# -------------------------------
# Pydantic models (responses / requests)
# -------------------------------
class FlightOut(BaseModel):
    flight_code: str
    airline: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    duration_mins: int
    seats_total: int
    seats_available: int
    base_fare: float
    current_fare: float
    demand_level: int

class ExternalFlightRequest(BaseModel):
    airlines: List[str] = Field(default_factory=lambda: ["AirFast", "SkyLine", "CloudAir"])
    routes: List[List[str]] = Field(default_factory=lambda: [["DEL","BOM"],["DEL","BLR"],["BLR","BOM"]])
    travel_date: date = Field(default_factory=lambda: date.today())

# -------------------------------
# App and DB init
# -------------------------------
app = FastAPI(title="Flight Search & Dynamic Pricing API")
engine = create_engine(DB_FILE, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

create_db_and_tables()

# -------------------------------
# Utility: dynamic pricing engine
# -------------------------------

def compute_dynamic_fare(base_fare: float, seats_total: int, seats_available: int, time_until_departure_hours: float, demand_level: int) -> float:
    """Compute dynamic fare based on heuristics:
    - remaining seat percentage: higher price when seats low
    - time until departure: price increases as departure nears
    - demand_level: simulated demand (0-100)
    - base fare and simple tier multipliers
    Returns a fare rounded to 2 decimals (minimum base_fare * 0.5 floor)
    """
    # safety checks
    if seats_total <= 0:
        seats_total = 1
    remaining_pct = seats_available / seats_total  # 0..1

    # Base multiplier: starts at 1.0
    mult = 1.0

    # Remaining seats effect: exponential-ish
    if remaining_pct < 0.05:
        mult += 1.0  # +100%
    elif remaining_pct < 0.15:
        mult += 0.5  # +50%
    elif remaining_pct < 0.33:
        mult += 0.25
    elif remaining_pct < 0.5:
        mult += 0.1

    # Time to departure effect
    if time_until_departure_hours < 2:
        mult += 0.75
    elif time_until_departure_hours < 12:
        mult += 0.35
    elif time_until_departure_hours < 48:
        mult += 0.1

    # Demand level effect (normalized between 0 and 1)
    demand_factor = max(0.0, min(1.0, demand_level / 100.0))
    mult += demand_factor * 0.8  # up to +80%

    # Pricing tiers (small customers may get discounts)
    # We'll impose a minimum price floor to avoid negative or tiny fares
    raw = base_fare * mult

    # Add small randomness to simulate market volatility
    volatility = random.uniform(-0.02, 0.03)  # -2% .. +3%
    raw *= (1.0 + volatility)

    floor = max(1.0, base_fare * 0.5)
    fare = max(floor, round(raw, 2))
    return fare

# -------------------------------
# Seed helper / external simulation
# -------------------------------

def generate_sample_flight(airline: str, origin: str, destination: str, dep_date: date) -> Flight:
    dep_time = datetime.combine(dep_date, datetime.min.time()) + timedelta(hours=random.randint(6,22), minutes=random.choice([0,15,30,45]))
    duration_mins = random.randint(60, 300)
    arr_time = dep_time + timedelta(minutes=duration_mins)
    seats_total = random.choice([120,150,180,200])
    seats_available = random.randint(0, seats_total)
    base_fare = round(random.uniform(2000, 15000), 2)
    demand_level = random.randint(0,100)
    flight = Flight(
        flight_code=f"{airline[:2].upper()}{random.randint(100,999)}",
        airline=airline,
        origin=origin,
        destination=destination,
        departure=dep_time,
        arrival=arr_time,
        duration_mins=duration_mins,
        seats_total=seats_total,
        seats_available=seats_available,
        base_fare=base_fare,
        current_fare=base_fare,
        demand_level=demand_level,
    )
    # compute initial fare
    hours = (flight.departure - datetime.utcnow()).total_seconds() / 3600
    flight.current_fare = compute_dynamic_fare(flight.base_fare, flight.seats_total, flight.seats_available, max(0.1, hours), flight.demand_level)
    return flight

# -------------------------------
# API: External simulated endpoints
# -------------------------------
@app.post("/external/fetch", response_model=List[FlightOut])
def fetch_external_schedules(req: ExternalFlightRequest):
    """Simulate fetching flight schedules from external airline APIs and save them into DB.
    Returns the newly created flights (as a simple simulation).
    """
    created = []
    with Session(engine) as session:
        for airline in req.airlines:
            for route in req.routes:
                origin, dest = route[0], route[1]
                f = generate_sample_flight(airline, origin, dest, req.date)
                session.add(f)
                session.commit()
                session.refresh(f)
                if ENABLE_FARE_HISTORY:
                    session.add(FareHistory(flight_id=f.id, timestamp=datetime.utcnow(), fare=f.current_fare))
                created.append(f)
        session.commit()
    return [FlightOut(**c.dict()) for c in created]

@app.get("/external/airline/{airline}")
def get_external_airline_schedule(airline: str, date_param: Optional[date] = None):
    """Return generated schedule for viewing (not persisted) to simulate external API response."""
    d = date_param or date.today()
    schedules = []
    for _ in range(3):
        f = generate_sample_flight(airline, random.choice(["DEL","BOM","BLR","MAA","HYD"]), random.choice(["DEL","BOM","BLR","MAA","HYD"]), d)
        schedules.append(FlightOut(**f.dict()))
    return schedules

# -------------------------------
# API: Flight retrieval and search
# -------------------------------
@app.get("/flights", response_model=List[FlightOut])
def get_all_flights(limit: int = Query(100, ge=1, le=1000)):
    with Session(engine) as session:
        statement = select(Flight).limit(limit)
        results = session.exec(statement).all()
    return [FlightOut(**r.dict()) for r in results]

@app.get("/search", response_model=List[FlightOut])
def search_flights(
    origin: Optional[str] = Query(None, min_length=3, max_length=5),
    destination: Optional[str] = Query(None, min_length=3, max_length=5),
    date_param: Optional[date] = Query(None, alias="date"),
    sort_by: Optional[Literal['price', 'duration']] = Query('price'),
    order: Optional[Literal['asc', 'desc']] = Query('asc'),
    limit: int = Query(50, ge=1, le=500)
):
    """Search flights by origin, destination, and date.
    Sorting can be done by price or duration. Price refers to dynamic current_fare.
    """
    with Session(engine) as session:
        stmt = select(Flight)
        if origin:
            stmt = stmt.where(Flight.origin == origin.upper())
        if destination:
            stmt = stmt.where(Flight.destination == destination.upper())
        if date_param:
            # match departure date (UTC)
            start_dt = datetime.combine(date_param, datetime.min.time())
            end_dt = start_dt + timedelta(days=1)
            stmt = stmt.where(Flight.departure >= start_dt, Flight.departure < end_dt)

        results = session.exec(stmt).all()

        # Recompute dynamic fares at search time for each result
        adjusted = []
        for f in results:
            hours = (f.departure - datetime.utcnow()).total_seconds() / 3600
            new_fare = compute_dynamic_fare(f.base_fare, f.seats_total, f.seats_available, max(0.1, hours), f.demand_level)
            f.current_fare = new_fare
            if ENABLE_FARE_HISTORY:
                session.add(FareHistory(flight_id=f.id, timestamp=datetime.utcnow(), fare=new_fare))
            adjusted.append(f)
        session.commit()

    # Sorting
    reverse = (order == 'desc')
    if sort_by == 'price':
        adjusted.sort(key=lambda x: x.current_fare, reverse=reverse)
    else:
        adjusted.sort(key=lambda x: x.duration_mins, reverse=reverse)

    return [FlightOut(**f.dict()) for f in adjusted[:limit]]

# -------------------------------
# Background simulation: demand and availability changes
# -------------------------------
stop_background = False

def background_worker():
    """Runs in a separate thread. Periodically updates demand levels, seat availability and prices."""
    global stop_background
    print("[Background] Worker started")
    while not stop_background:
        try:
            with Session(engine) as session:
                flights = session.exec(select(Flight)).all()
                for f in flights:
                    # Simulate demand: small random walk
                    delta = random.randint(-5, 8)
                    f.demand_level = max(0, min(100, f.demand_level + delta))

                    # Simulate seats booking/cancellation
                    change = random.choices([0, -1, -2, 1], weights=[70,15,5,10])[0]
                    f.seats_available = max(0, min(f.seats_total, f.seats_available + change))

                    # Recompute fare
                    hours = (f.departure - datetime.utcnow()).total_seconds() / 3600
                    f.current_fare = compute_dynamic_fare(f.base_fare, f.seats_total, f.seats_available, max(0.1, hours), f.demand_level)

                    if ENABLE_FARE_HISTORY:
                        session.add(FareHistory(flight_id=f.id, timestamp=datetime.utcnow(), fare=f.current_fare))

                session.commit()
        except Exception as e:
            print("[Background] Exception:", e)
        time.sleep(BACKGROUND_UPDATE_INTERVAL_SEC)
    print("[Background] Worker stopped")

bg_thread = threading.Thread(target=background_worker, daemon=True)

@app.on_event("startup")
def startup_event():
    # Seed DB with some flights if empty
    with Session(engine) as session:
        count = session.exec(select(Flight)).count()
        if count == 0:
            print("Seeding sample flights...")
            today = date.today()
            for airline in ["AirFast","SkyLine","CloudAir"]:
                for route in [["DEL","BOM"],["DEL","BLR"],["BLR","BOM"]]:
                    f = generate_sample_flight(airline, route[0], route[1], today + timedelta(days=random.randint(0,5)))
                    session.add(f)
            session.commit()
    # start background worker
    if not bg_thread.is_alive():
        bg_thread.start()

@app.on_event("shutdown")
def shutdown_event():
    global stop_background
    stop_background = True
    bg_thread.join(timeout=2)

# -------------------------------
# Utility: Optional endpoints for admin actions
# -------------------------------
@app.get("/fare-history/{flight_id}", response_model=List[dict])
def get_fare_history(flight_id: int, limit: int = Query(100, ge=1, le=1000)):
    if not ENABLE_FARE_HISTORY:
        raise HTTPException(status_code=404, detail="Fare history disabled")
    with Session(engine) as session:
        rows = session.exec(select(FareHistory).where(FareHistory.flight_id == flight_id).order_by(FareHistory.timestamp.desc()).limit(limit)).all()
    return [{"timestamp": r.timestamp, "fare": r.fare} for r in rows]

# -------------------------------
# Small helper: admin endpoint to trigger immediate external fetch
# -------------------------------
@app.post("/admin/trigger-fetch", response_model=dict)
def admin_trigger_fetch(airlines: Optional[List[str]] = None):
    req = ExternalFlightRequest()
    if airlines:
        req.airlines = airlines
    created = fetch_external_schedules(req)
    return {"added": len(created)}

# -------------------------------
# If run as script
# -------------------------------
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("flight_search_api_fastapi:app", host="127.0.0.1", port=8000, reload=True)
