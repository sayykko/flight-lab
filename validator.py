import math
import re
from datetime import datetime

def load_airports(path: str) -> set[str]:
    airports = set()
    with open(path, encoding="utf-8") as file:
        for line in file:
            code = line.strip()
            if code and not code.startswith("#"):
                airports.add(code)
    return airports

def parse_datetime(value: str) -> datetime | None:
    pattern = r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}"
    if re.fullmatch(pattern, value) is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        return None

def validate_row(fields: list[str], airports: set[str]) -> str | None:
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"
    fields = [field.strip() for field in fields]
    if any(field == "" for field in fields):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure, arrival, price = fields
    if re.fullmatch(r"[A-Za-z0-9]{2,8}", flight_id) is None:
        return "INVALID_FLIGHT_ID"
    if re.fullmatch(r"[A-Z]{3}", origin) is None or origin not in airports:
        return "INVALID_ORIGIN"
    if (
        re.fullmatch(r"[A-Z]{3}", destination) is None
        or destination not in airports
    ):
        return "INVALID_DESTINATION"
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    departure_time = parse_datetime(departure)
    if departure_time is None:
        return "INVALID_DEPARTURE"
    arrival_time = parse_datetime(arrival)
    if arrival_time is None:
        return "INVALID_ARRIVAL"
    if arrival_time <= departure_time:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    try:
        price_value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(price_value):
        return "INVALID_PRICE"
    if price_value <= 0:
        return "NON_POSITIVE_PRICE"
    return None

def to_record(fields: list[str]) -> dict:
    fields = [field.strip() for field in fields]
    return {
        "flight_id": fields[0],
        "origin": fields[1],
        "destination": fields[2],
        "departure_datetime": fields[3],
        "arrival_datetime": fields[4],
        "price": float(fields[5]),
    }
