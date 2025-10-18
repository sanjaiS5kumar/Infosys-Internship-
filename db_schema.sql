CREATE DATABASE flight_booking;
USE flight_booking CREATE TABLE flights(
    id INT AUTO_INCREMENT PRIMARY KEY,
    flight_no VARCHAR(10),
    ORIGIN VARCHAR(50),
    DESTINATION VARCHAR(50),
    deaptaure DATETIME,
    arrival DATETIME,
    base_fare DECIMAL(10, 2),
    TOTAL_SEATS INT,
    SEATS_AVAILABLE INT AIRLINES_NAME VARCHAR(20)
)
INSERT INTO flights (
        id,
        flight_no,
        origin,
        destination,
        depature,
        arrival,
        base_fare,
        total_seats,
        seats_available
    )
Values (
        1,
        'AI1',
        'Delhi',
        'Mumbai',
        '2025-03-01 10.00.00',
        '2025-03-01 12.00.00',
        8000.00,
        200,
        150
    ),
    (
        2,
        'AI2',
        'Mumbai',
        'Delhi',
        '2025-03-01 15.00.00',
        '2025-03-01 17.00.00',
        8000.00,
        200,
        200
    ),
    (
        3,
        'AI3',
        'Delhi',
        'Chennai',
        '2025-03-01 09.00.00',
        '2025-03-01 11.30.00',
        9000.00,
        200,
        180
    ),
    (
        4,
        'AI4',
        'Chennai',
        'Delhi',
        '2025-03-01 13.00.00',
        '2025-03-01 15.30.00',
        9000.00,
        200,
        200
    ),
    (
        5,
        'AI5',
        'Mumbai',
        'Chennai',
        '2025-03-01 12.00.00',
        '2025-03-01 14.30.00',
        6000.00,
        200,
        160
    ),
    (
        6,
        'AI6',
        'Chennai',
        'Mumbai',
        '2025-03-01 16.00.00',
        '2025-03-01 18.30.00',
        7000.00,
        200,
        200
    );
SELECT *
FROM flights;
SELECT id,
    flight_no,
    origin,
    destination,
    base_fare
FROM flights;
UPDATE
Update flights
Set seats_available = 300
where id = 6;
DELETE
Delete From flights
where id = 3
ORDER BY
SELECT flight_no,
    base_fare
FROM flights
ORDER BY base_fare ASC;
Select flight_no,
    depature
from flights
order by depature DESC;
WHERE
SELECT *
FROM flights
WHERE ORIGIN = 'mumbai'
SELECT flight_no,
    base_fare
FROM flights
where base_fare > 8000;
LIMIT
SELECT flight_no,
    base_fare
FROM flights
ORDER BY base_fare ASC;
LIMIT 3;
AGGREGATE FUNCTIONS
SELECT COUNT(*) AS total_flights
FROM flights
SELECT AVG(base_fare) AS avg_fare
FROM flights
WHERE origin = "MUMBAI"
GROUP BY
SELECT origin,
    AVG(base_fare) AS avg_fare
FROM flights
GROUP BY origin SELCT origin,
    AVG(base_fare) AS avg_fare
FROM flights
GROUP BY origin
HAVING AVG(base_fare) < 8000 Alter
ALTER TABLE flights
ADD airline_name VARCHAR(20)
ALTER TABLE flights CHANGE dept deaptaure DATETIME CREATE TABLE flights(
        id INT AUTO_INCREMENT PRIMARY KEY,
        flight_no VARCHAR(10),
        ORIGIN VARCHAR(50),
        DESTINATION VARCHAR(50),
        dept,
        arrival DATETIME,
        base_fare DECIMAL(10, 2),
        TOTAL_SEATS INT,
        SEATS_AVAILABLE INT AIRLINES_NAME VARCHAR(20)
    ) Joins - combine the data for 2
    or more tables on the same related column.- 4 types of
    join Table - flights - id,
    flight_no,
    origin,
    dest,
    base_fare,
.....TABLE - bookings - booking_id,
    trans_id,
    flight_no,
    origin,
    dest,
    passenger full name,
    passenger contact details - phone / mail id,
    seat_no Table - passenger - passenger_id,
    passenger_full name,
    passenger_contact details,
    passenger_city flight_no,
    origin,
    dest passenger_full name,
    passenger_contact details Create table bookings(
        booking_id INT Auto - increment primary KEY,
        trans_id INT,
        flight_no INT,
        origin VARCHAR(20),
        dest VARCHAR(20),
        passenger_full name VARCHAR(50),
        passenger_contact INT seat_no INT
    )
INsert into bookings(
        booking_id,
        trans_id,
        flight_no,
        passenger_full name,
        passenger_contact,
        seat_no
    )
Values (1, 'IC145', 'AI1', 'Alice', 123456789, 12),
    (2, 'AB123', 'AI2', 'Bob', 456740894, 06),
    (3, 'TC078', 'AI3', 'Jack', 54690246979, 24);
1.
inner join: returns only matching records / vales in both the tables
SELECT b.passenger_fullname,
    f.flight_no,
    f.origin,
    f.destination
From booking b
    INNER JOIN flights f on b.flight_id = f.id;
2.
Left join returns all the records
from the left table + matching records
from the right table (NULL if no match) AI1 - booked AI2 - NULL AI3 - booked Ai2 - leave empty,
    because i dont have any bookings - which in turn relates the there is a no passenegr details
Select f.flight_no,
    f.origin,
    f.destination,
    b.passenger_fullname
from flight f
    Left JOin bookings b on f.id = b.flight_no;
3.
Right Join opposite of the
left join AI1 - booked AI2 - NULL AI3 - booked
Select f.flight_no,
    b.passenger_name
from flight f
    right join booking b on f.id = b.flight_no 4.
    Full outer join - mysql doesnt have this type of
    join,
    full outer join - but we can use this using a
UNION
returns all the records
from all the tables that related - filling NUlls
where there is no match exists
select f.flight_no,
    b.passenger_full name
from flights f
    left join bookings b on f.id = b.flight_id
UNION
select f.flight_no,
    b.passenger_fullname
from flghts f
    right join booking b on f.id = b.flight_id;
Transactions: this command,
ensures that all the sql commands execute together - outcomes - can be a success
or can also be a failure certain commands: Start transactions / begin - start the action commit - apply the chnages rollback - undo if there is an error Start Transaction;
1.check the seat availability
select seats_available
from flight
where id = 1;
2.
update the seat availability:
update flights
Set seats_available = seats_available - 1
where id = 1;
3.
Insert booking:
Insert into bookings (flight_id, pasasenger_fullname, seat_no)
values (1, 'David', 22) Commit;
rollback;
Constraints - maintaining the data integrity common constraints: primary KEY - unique identiofier for that particukar table - id INT PRIMARY KEY foreign key - Ensure relationship betweeen the both tables - flight_id INT,
Foreign KEY (flight_id) NOt NULL - Column must have
values - passenegr_name Varchar(50) NOT NULL Unique - column must be a unique one - seat_no INT UNIQUE check -
values that need to be restrict - CHECK (SEATS_AVAILABLE >= 0) default - default value if none given - base_fare DECIMAL(10, 2) DEafult 5000