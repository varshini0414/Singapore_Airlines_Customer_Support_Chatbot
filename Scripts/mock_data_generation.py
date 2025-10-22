import random
import string
from datetime import datetime, timedelta

def random_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

names = [
    "Aarav Kumar", "Vihaan Sharma", "Aditya Patel", "Arjun Reddy", "Sai Nair",
    "Riya Singh", "Ananya Das", "Diya Iyer", "Ishaan Gupta", "Meera Pillai",
    "Liam Tan", "Sophia Lim", "Benjamin Ong", "Ethan Lee", "Charlotte Goh",
    "Lucas Chua", "Ava Koh", "Noah Chan", "Olivia Ng", "Emma Toh"
]

airports = [
    ("SIN", "Singapore Changi Airport"),
    ("LHR", "London Heathrow"),
    ("SYD", "Sydney Kingsford Smith"),
    ("SFO", "San Francisco International"),
    ("NRT", "Tokyo Narita"),
    ("JFK", "New York JFK"),
    ("DXB", "Dubai International"),
    ("FRA", "Frankfurt"),
    ("CDG", "Paris Charles de Gaulle"),
    ("HKG", "Hong Kong International")
]

fare_classes = ["Economy", "Premium Economy", "Business", "First"]
check_in_statuses = ["Checked-In", "Not Checked-In", "Boarded", "Cancelled"]

records = []

for _ in range(100):
    id_ = random_id()
    passenger_name = random.choice(names)
    flight_number = f"SQ{random.randint(100, 999)}"
    seat_number = f"{random.randint(1, 60)}{random.choice(['A','B','C','D','E','F'])}"
    fare_class = random.choice(fare_classes)
    dep, arr = random.sample(airports, 2)
    departure, arrival = dep[0], arr[0]

    dep_date = datetime.now() + timedelta(days=random.randint(1, 90))
    arr_date = dep_date + timedelta(hours=random.randint(6, 14))

    check_in_status = random.choice(check_in_statuses)
    baggage_count = random.randint(0, 3)

    record = f"INSERT INTO bookings VALUES ('{id_}', '{passenger_name}', '{flight_number}', '{seat_number}', '{fare_class}', '{departure}', '{arrival}', '{dep_date.strftime('%Y-%m-%d %H:%M')}', '{arr_date.strftime('%Y-%m-%d %H:%M')}', '{check_in_status}', {baggage_count});"
    records.append(record)

with open("singapore_airlines_bookings.sql", "w") as f:
    f.write("\n".join(records))

print("Generated singapore_airlines_bookings.sql with 100 records (6-digit alphanumeric IDs).")

