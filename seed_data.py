"""
seed_data.py: Database Seeding Script.

Populates the MongoDB 'items' collection with realistic campus lost & found
items across multiple categories, locations, and workflow statuses.
Run standalone with: python seed_data.py
Or call via the UI seed button.
"""

from datetime import datetime, timedelta, timezone
from config import get_database
from db_validator import setup_database_schema

SAMPLE_ITEMS = [
    {
        "title": "Midnight Blue Hydro Flask Water Bottle (32oz)",
        "description": "Insulated stainless steel bottle with subtle scratches on the bottom and a NASA sticker on the side.",
        "type": "Lost",
        "category": "Personal Accessories",
        "campus_location": "Central Library",
        "specific_spot": "2nd Floor Quiet Study Cubicle #14",
        "days_ago_reported": 12,
        "days_ago_incident": 12,
        "reporter": {
            "name": "Aarav Sharma",
            "email": "aarav.sharma@campus.edu",
            "phone": "+1-555-0192",
            "role": "Student"
        },
        "status": "Claimed",
        "tags": ["hydroflask", "bottle", "blue", "sticker"],
        "claimed_after_days": 3,
        "claim_verification_notes": "Student verified sticker placement and demonstrated ownership matching student ID."
    },
    {
        "title": "Apple AirPods Pro (2nd Gen) in White Magsafe Case",
        "description": "Found on the bench right outside the computer vision lab. Case has a small green silicon sleeve.",
        "type": "Found",
        "category": "Electronics",
        "campus_location": "Science & Engineering Block",
        "specific_spot": "3rd Floor Lab corridor bench",
        "days_ago_reported": 8,
        "days_ago_incident": 8,
        "reporter": {
            "name": "Prof. David Miller",
            "email": "d.miller@campus.edu",
            "phone": "+1-555-0143",
            "role": "Faculty"
        },
        "status": "Open",
        "tags": ["airpods", "apple", "headphones", "electronics"]
    },
    {
        "title": "Campus RFID Student Identity Card",
        "description": "Student ID card belonging to Computer Science senior. Found next to the cash register.",
        "type": "Found",
        "category": "Student ID / Cards",
        "campus_location": "Main Cafeteria",
        "specific_spot": "Cash Register Counter 2",
        "days_ago_reported": 5,
        "days_ago_incident": 5,
        "reporter": {
            "name": "Maria Gonzalez",
            "email": "maria.cafeteria@campus.edu",
            "phone": "+1-555-0129",
            "role": "Staff"
        },
        "status": "Claimed",
        "tags": ["id card", "student card", "rfid"],
        "claimed_after_days": 1,
        "claim_verification_notes": "Claimant presented government driving license matching the name and photo on the student ID."
    },
    {
        "title": "Dell XPS 15 USB-C Power Adapter & Braided Cable",
        "description": "Left behind plugged into wall socket behind the big seminar presentation podium.",
        "type": "Found",
        "category": "Electronics",
        "campus_location": "Auditorium Complex",
        "specific_spot": "Main Stage podium wall outlet",
        "days_ago_reported": 14,
        "days_ago_incident": 14,
        "reporter": {
            "name": "Tech Support Desk",
            "email": "av.support@campus.edu",
            "phone": "+1-555-0180",
            "role": "Staff"
        },
        "status": "Under Review",
        "tags": ["dell", "charger", "laptop", "usb-c"]
    },
    {
        "title": "Set of 3 Dorm Room Keys with Red Brass Carabiner",
        "description": "Lost my room and lab keys while jogging around the outer track lawn yesterday afternoon.",
        "type": "Lost",
        "category": "Keys & Badges",
        "campus_location": "North Quad Lawn",
        "specific_spot": "Near the outdoor fitness pull-up bars",
        "days_ago_reported": 3,
        "days_ago_incident": 3,
        "reporter": {
            "name": "Chloe Vance",
            "email": "chloe.vance@campus.edu",
            "phone": "+1-555-0118",
            "role": "Student"
        },
        "status": "Open",
        "tags": ["keys", "dorm", "carabiner", "red"]
    },
    {
        "title": "Calculus: Early Transcendentals Hardcover Textbook (9th Ed)",
        "description": "Stewart Calculus textbook with yellow sticky notes throughout chapter 7 on integrals.",
        "type": "Lost",
        "category": "Books & Stationery",
        "campus_location": "Central Library",
        "specific_spot": "1st Floor Group Study Table 8",
        "days_ago_reported": 10,
        "days_ago_incident": 10,
        "reporter": {
            "name": "Liam Chen",
            "email": "l.chen@campus.edu",
            "phone": "+1-555-0155",
            "role": "Student"
        },
        "status": "Claimed",
        "tags": ["textbook", "calculus", "math", "book"],
        "claimed_after_days": 2,
        "claim_verification_notes": "Student showed their course syllabus and highlighted notes inside the book."
    },
    {
        "title": "Black Leather Bi-fold Wallet with Metro Transit Pass",
        "description": "Contains driver license, transit card, and some local currency. Turned in to security front desk.",
        "type": "Found",
        "category": "Bags & Wallets",
        "campus_location": "Student Center & Gym",
        "specific_spot": "Locker Room Bench Area",
        "days_ago_reported": 6,
        "days_ago_incident": 6,
        "reporter": {
            "name": "Security Officer Jenkins",
            "email": "security.desk@campus.edu",
            "phone": "+1-555-0100",
            "role": "Staff"
        },
        "status": "Claimed",
        "tags": ["wallet", "leather", "transit pass", "id"],
        "claimed_after_days": 1,
        "claim_verification_notes": "Claimant verified by cross-referencing university security log and fingerprint/ID card."
    },
    {
        "title": "Ray-Ban Polarized Wayfarer Sunglasses in Brown Leather Case",
        "description": "Tortoise shell frame sunglasses left on dining table during lunch rush.",
        "type": "Lost",
        "category": "Personal Accessories",
        "campus_location": "Main Cafeteria",
        "specific_spot": "Booth 6 near the salad bar",
        "days_ago_reported": 4,
        "days_ago_incident": 4,
        "reporter": {
            "name": "Samantha Wright",
            "email": "sam.wright@campus.edu",
            "phone": "+1-555-0133",
            "role": "Student"
        },
        "status": "Open",
        "tags": ["sunglasses", "rayban", "eyewear"]
    },
    {
        "title": "Grey North Face Hooded Rain Jacket (Size M)",
        "description": "Left on the auditorium seat row G after the freshman orientation seminar.",
        "type": "Found",
        "category": "Clothing & Gear",
        "campus_location": "Auditorium Complex",
        "specific_spot": "Auditorium Row G, Seat 12",
        "days_ago_reported": 15,
        "days_ago_incident": 15,
        "reporter": {
            "name": "Custodial Staff Robert",
            "email": "robert.facilities@campus.edu",
            "role": "Staff"
        },
        "status": "Open",
        "tags": ["jacket", "north face", "rain jacket", "clothes"]
    },
    {
        "title": "Logitech MX Master 3S Wireless Mouse (Graphite)",
        "description": "Ergonomic Bluetooth mouse left beside iMac #12 in the digital media lab.",
        "type": "Found",
        "category": "Electronics",
        "campus_location": "Science & Engineering Block",
        "specific_spot": "Digital Media Lab room 204",
        "days_ago_reported": 9,
        "days_ago_incident": 9,
        "reporter": {
            "name": "Dr. Sarah Adams",
            "email": "sadams@campus.edu",
            "phone": "+1-555-0162",
            "role": "Faculty"
        },
        "status": "Claimed",
        "tags": ["mouse", "logitech", "bluetooth", "hardware"],
        "claimed_after_days": 2,
        "claim_verification_notes": "Owner connected to laptop via Bluetooth instantly pairing with their device name."
    },
    {
        "title": "Blue Spiral Bound Chemistry Lab Notebook",
        "description": "Contains organic chemistry reaction notes and lab measurement graphs from experiment 4-7.",
        "type": "Lost",
        "category": "Books & Stationery",
        "campus_location": "Science & Engineering Block",
        "specific_spot": "Chemistry Lab 301 bench top",
        "days_ago_reported": 2,
        "days_ago_incident": 2,
        "reporter": {
            "name": "Ethan Patel",
            "email": "ethan.p@campus.edu",
            "phone": "+1-555-0177",
            "role": "Student"
        },
        "status": "Under Review",
        "tags": ["notebook", "chemistry", "lab notebook"]
    },
    {
        "title": "Smart FitBit Charge 5 Fitness Tracker with Black Band",
        "description": "Found on the treadmill console after morning cardio workout.",
        "type": "Found",
        "category": "Electronics",
        "campus_location": "Student Center & Gym",
        "specific_spot": "Cardio Deck Treadmill #4",
        "days_ago_reported": 7,
        "days_ago_incident": 7,
        "reporter": {
            "name": "Gym Attendant Jordan",
            "email": "jordan.gym@campus.edu",
            "role": "Staff"
        },
        "status": "Claimed",
        "tags": ["fitbit", "smartwatch", "fitness", "watch"],
        "claimed_after_days": 3,
        "claim_verification_notes": "Verified synced account on user phone with the tracker PIN."
    },
    {
        "title": "Toyota Car Key with Black Leather Remote Fob",
        "description": "Found on asphalt in the visitor parking slot B-14.",
        "type": "Found",
        "category": "Keys & Badges",
        "campus_location": "Parking Lot A",
        "specific_spot": "Parking bay slot B-14",
        "days_ago_reported": 11,
        "days_ago_incident": 11,
        "reporter": {
            "name": "Campus Parking Control",
            "email": "parking@campus.edu",
            "phone": "+1-555-0110",
            "role": "Staff"
        },
        "status": "Claimed",
        "tags": ["toyota", "car key", "key fob", "parking"],
        "claimed_after_days": 1,
        "claim_verification_notes": "Visitor showed vehicle registration documents matching vehicle parked in Lot A."
    },
    {
        "title": "Black Patagonia Atom Sling Backpack (8L)",
        "description": "Accidentally left in the administrative lobby waiting area while submitting graduation forms.",
        "type": "Lost",
        "category": "Bags & Wallets",
        "campus_location": "Administrative Building",
        "specific_spot": "Registrar waiting lounge sofa",
        "days_ago_reported": 1,
        "days_ago_incident": 1,
        "reporter": {
            "name": "Lucas Meyer",
            "email": "lucas.m@campus.edu",
            "phone": "+1-555-0188",
            "role": "Student"
        },
        "status": "Open",
        "tags": ["patagonia", "bag", "backpack", "sling"]
    },
    {
        "title": "Texas Instruments TI-84 Plus CE Graphing Calculator",
        "description": "Mint green graphing calculator with student name sticker faded on the back cover.",
        "type": "Lost",
        "category": "Electronics",
        "campus_location": "Central Library",
        "specific_spot": "3rd Floor Math Reference Section",
        "days_ago_reported": 16,
        "days_ago_incident": 16,
        "reporter": {
            "name": "Nina Joshi",
            "email": "nina.j@campus.edu",
            "phone": "+1-555-0149",
            "role": "Student"
        },
        "status": "Archived",
        "tags": ["calculator", "ti-84", "texas instruments", "math"]
    }
]

def seed_database(db=None, drop_existing=True):
    """
    Seeds the MongoDB database with initial sample data.
    """
    if db is None:
        db = get_database()

    setup_database_schema(db)
    items_col = db["items"]

    if drop_existing:
        deleted_count = items_col.delete_many({}).deleted_count
        print(f"[*] Cleared {deleted_count} existing documents.")

    now = datetime.now(timezone.utc)
    documents = []

    for item_data in SAMPLE_ITEMS:
        days_reported = item_data.get("days_ago_reported", 0)
        days_incident = item_data.get("days_ago_incident", days_reported)
        reported_dt = now - timedelta(days=days_reported)
        incident_dt = now - timedelta(days=days_incident)

        doc = {
            "title": item_data["title"],
            "description": item_data["description"],
            "type": item_data["type"],
            "category": item_data["category"],
            "campus_location": item_data["campus_location"],
            "specific_spot": item_data.get("specific_spot", ""),
            "reporter": item_data["reporter"],
            "status": item_data["status"],
            "tags": item_data.get("tags", []),
            "date_reported": reported_dt,
            "date_incident": incident_dt,
            "created_at": reported_dt,
            "updated_at": reported_dt
        }

        # If claimed, compute claimed_date and attach claim_details
        if item_data.get("status") == "Claimed":
            claimed_after = item_data.get("claimed_after_days", 1)
            claimed_dt = reported_dt + timedelta(days=claimed_after)
            doc["claim_details"] = {
                "claimed_by_name": item_data.get("reporter", {}).get("name", "Verified Owner"),
                "claimed_date": claimed_dt,
                "verification_notes": item_data.get("claim_verification_notes", "Verified via student ID.")
            }
            doc["updated_at"] = claimed_dt

        documents.append(doc)

    result = items_col.insert_many(documents)
    print(f"[OK] Seeded {len(result.inserted_ids)} items into 'items' collection.")
    return len(result.inserted_ids)

if __name__ == "__main__":
    seed_database()
