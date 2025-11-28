import re
import json
import os
from datetime import datetime
from typing import List, Dict, Union
from langchain_core.tools import tool  
from langchain_tavily import TavilySearch
from dotenv import load_dotenv
load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

BASE_DIR = os.path.dirname(__file__)
ROOMS_FILE = os.path.join(BASE_DIR, "rooms.json")
BOOKINGS_FILE = os.path.join(BASE_DIR, "bookings.json")
RESORT_DATA_FILE = os.path.join(BASE_DIR, "data", "resort_data.json")


def _load(filename: str):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def _save(filename: str, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def parse_date(date_str: str) -> Union[datetime, None]:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return None


def is_available(room_no: int, check_in: str, check_out: str, bookings: List[Dict]) -> bool:
    ci = parse_date(check_in)
    co = parse_date(check_out)
    for b in bookings:
        if b["room_no"] == room_no:
            b_ci = parse_date(b["check_in"])
            b_co = parse_date(b["check_out"])
            if not (co <= b_ci or ci >= b_co):
                return False
    return True


def view_rooms() -> List[Dict]:
    return _load(ROOMS_FILE)


def view_bookings() -> List[Dict]:
    return _load(BOOKINGS_FILE)


def add_booking(name: str, room_type: str, check_in: str, check_out: str) -> str:
    rooms = _load(ROOMS_FILE)
    bookings = _load(BOOKINGS_FILE)

    ci = parse_date(check_in)
    co = parse_date(check_out)
    if not ci or not co:
        return "Invalid date format. Please use YYYY-MM-DD or DD/MM/YYYY."

    room_type_lower = room_type.lower()
    matching_rooms = [r for r in rooms if r["type"].lower() == room_type_lower]

    for room in matching_rooms:
        if is_available(room["room_no"], check_in, check_out, bookings):
            new_booking = {
                "name": name,
                "room_no": room["room_no"],
                "room_type": room["type"],
                "check_in": ci.strftime("%Y-%m-%d"),
                "check_out": co.strftime("%Y-%m-%d")
            }
            bookings.append(new_booking)
            _save(BOOKINGS_FILE, bookings)
            return f"Room {room['room_no']} booked successfully for {name}."
    return f"No rooms available for {room_type} from {ci.strftime('%Y-%m-%d')} to {co.strftime('%Y-%m-%d')}."


def cancel_booking(name: str) -> str:
    bookings = _load(BOOKINGS_FILE)
    updated_bookings = [b for b in bookings if b["name"].lower() != name.lower()]
    if len(updated_bookings) == len(bookings):
        return f"No booking found for {name}."
    _save(BOOKINGS_FILE, updated_bookings)
    return f"Booking for {name} has been cancelled."


def generate_bill(name: str) -> Union[str, Dict]:
    rooms = _load(ROOMS_FILE)
    bookings = _load(BOOKINGS_FILE)
    booking = next((b for b in bookings if b["name"].lower() == name.lower()), None)
    if not booking:
        return f"No booking found for {name}."
    room = next((r for r in rooms if r["room_no"] == booking["room_no"]), None)
    if not room:
        return "Room data missing."
    d1 = parse_date(booking["check_in"])
    d2 = parse_date(booking["check_out"])
    days = (d2 - d1).days
    total = days * room["price"]
    return {
        "name": booking["name"],
        "room_no": room["room_no"],
        "days": days,
        "price_per_day": room["price"],
        "total_bill": total
    }


# parsers & helpers
def parse_date_from_text(text):
    patterns = [
        r"(\d{2}/\d{2}/\d{4})",
        r"(\d{2}-\d{2}-\d{4})",
        r"(\d{4}/\d{2}/\d{2})",
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{2}/\d{2}/\d{2})",
        r"(\d{2}-\d{2}-\d{2})"
    ]
    for pat in patterns:
        match = re.search(pat, text)
        if match:
            date_str = match.group(1)
            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d", "%d/%m/%y", "%d-%m-%y"):
                try:
                    return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
                except:
                    continue
    return None


def parse_room_type(text):
    text_lower = text.lower()
    for room in ["deluxe", "suite", "standard"]:
        if room in text_lower:
            return room.capitalize()
    return None


def parse_name(text):
    match = re.search(r"for (\w+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).capitalize()
    match = re.search(r"\b([A-Z][a-z]+)\b", text)
    if match:
        return match.group(1)
    return None


def get_resort_info(query):
    try:
        with open(RESORT_DATA_FILE, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return "Resort data file is missing /invalid."

    query_lower = query.lower().strip()
    if not query_lower:
        return "Query cannot be empty"

    results = []
    for item in data:
        title = item.get("title", "").lower()
        desc = item.get("description", "").lower()
        if any(word in title or word in desc for word in query_lower.split()):
            results.append(item)

    if not results:
        return "No matching resort information  found"

    formatted = []
    for r in results:
        formatted.append(f"**{r.get('title','No Title')}**\n{r.get('description','No Description')}")
    return "\n\n".join(formatted)


def format_rooms(rooms):
    if not rooms:
        return "No rooms data available."
    return "\n".join([f"Room {r['room_no']}: {r['type']} - ${r['price']}/day" for r in rooms])


def format_bookings(bookings):
    if not bookings:
        return "No bookings yet."
    return "\n".join([f"{b['name']} -> Room {b['room_no']} ({b['room_type']}), {b['check_in']} to {b['check_out']}" for b in bookings])


def format_bill(bill):
    if isinstance(bill, dict):
        return (f"{bill['name']} booked Room {bill['room_no']} for {bill['days']} days.\n"
                f"Price per day: ${bill['price_per_day']}\n"
                f"Total bill: ${bill['total_bill']}")
    return bill



# LangChain tools

@tool
def view_rooms_tool(_query: str = "") -> str:
    """Return a formatted list of available rooms. Input ignored."""
    return format_rooms(view_rooms())


@tool
def view_bookings_tool(_query: str = "") -> str:
    """Return a formatted list of current bookings. Input ignored."""
    return format_bookings(view_bookings())


@tool
def add_booking_tool(text: str) -> str:
    """Create a booking from a natural language string (expects name, room type, check-in, check-out)."""
    name = parse_name(text)
    room_type = parse_room_type(text)
    dates = re.findall(r"(\d{2}[-/]\d{2}[-/]\d{2,4}|\d{4}[-/]\d{2}[-/]\d{2})", text)
    check_in = parse_date_from_text(dates[0]) if len(dates) > 0 else None
    check_out = parse_date_from_text(dates[1]) if len(dates) > 1 else None
    if not (name and room_type and check_in and check_out):
        return ("Missing details. Please provide name, room type, check-in and check-out dates "
                "(e.g, 'Book Deluxe room for Rahul from 26/11/2025 to 27/11/2025').")
    return add_booking(name, room_type, check_in, check_out)


@tool
def cancel_booking_tool(name: str) -> str:
    """Cancel a booking by customer name."""
    return cancel_booking(name)


@tool
def generate_bill_tool(name: str) -> str:
    """Generate bill for a customer by name."""
    return format_bill(generate_bill(name))


@tool
def resort_info_tool(query: str) -> str:
    """Search resort information (amenities, dining, activities)."""
    return get_resort_info(query)



tavily_tool = TavilySearch(
    api_key=os.getenv("TAVILY_API_KEY"),
    max_results=5
)


# all tools list
all_tools = [
    view_rooms_tool,
    view_bookings_tool,
    add_booking_tool,
    cancel_booking_tool,
    generate_bill_tool,
    resort_info_tool,
    tavily_tool,
]
