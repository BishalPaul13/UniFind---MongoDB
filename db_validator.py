"""
db_validator.py: MongoDB Collection-Level Schema Validation & Indexes Setup.

This module defines the MongoDB JSON Schema ($jsonSchema) for the 'items' collection
in accordance with class project requirements for database-level validation.
It enforces strict types, required fields, and acceptable enum values directly inside MongoDB.
"""

from pymongo.errors import CollectionInvalid, OperationFailure
from config import get_database

ITEMS_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "title",
            "description",
            "type",
            "category",
            "campus_location",
            "reporter",
            "status",
            "date_reported",
            "created_at",
            "updated_at"
        ],
        "properties": {
            "title": {
                "bsonType": "string",
                "minLength": 3,
                "maxLength": 100,
                "description": "Item title must be a string between 3 and 100 chars (required)."
            },
            "description": {
                "bsonType": "string",
                "minLength": 5,
                "maxLength": 600,
                "description": "Detailed description between 5 and 600 chars (required)."
            },
            "type": {
                "enum": ["Lost", "Found"],
                "description": "Type must be either 'Lost' or 'Found' (required)."
            },
            "category": {
                "enum": [
                    "Electronics",
                    "Student ID / Cards",
                    "Keys & Badges",
                    "Books & Stationery",
                    "Bags & Wallets",
                    "Personal Accessories",
                    "Clothing & Gear",
                    "Others"
                ],
                "description": "Item category must be one of the pre-defined options (required)."
            },
            "campus_location": {
                "enum": [
                    "Central Library",
                    "Main Cafeteria",
                    "Science & Engineering Block",
                    "Auditorium Complex",
                    "Student Center & Gym",
                    "North Quad Lawn",
                    "Parking Lot A",
                    "Administrative Building"
                ],
                "description": "Campus location must be one of the official campus zones (required)."
            },
            "specific_spot": {
                "bsonType": "string",
                "maxLength": 150,
                "description": "Optional specific spot on campus (e.g. '2nd Floor Quiet Zone Desk 14')."
            },
            "reporter": {
                "bsonType": "object",
                "required": ["name", "email", "role"],
                "properties": {
                    "name": {
                        "bsonType": "string",
                        "minLength": 2,
                        "maxLength": 80,
                        "description": "Reporter full name (required)."
                    },
                    "email": {
                        "bsonType": "string",
                        "pattern": r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
                        "description": "Valid email address of the reporter (required)."
                    },
                    "phone": {
                        "bsonType": "string",
                        "maxLength": 20,
                        "description": "Optional phone contact."
                    },
                    "role": {
                        "enum": ["Student", "Faculty", "Staff", "Visitor"],
                        "description": "Campus role of the reporter (required)."
                    }
                }
            },
            "status": {
                "enum": ["Open", "Under Review", "Claimed", "Archived"],
                "description": "Item workflow status (required)."
            },
            "tags": {
                "bsonType": "array",
                "items": {
                    "bsonType": "string"
                },
                "description": "List of search keywords or descriptive tags."
            },
            "claim_details": {
                "bsonType": "object",
                "properties": {
                    "claimed_by_name": {
                        "bsonType": "string"
                    },
                    "claimed_date": {
                        "bsonType": "date"
                    },
                    "verification_notes": {
                        "bsonType": "string"
                    }
                },
                "description": "Details recorded upon successful verification and claiming."
            },
            "date_reported": {
                "bsonType": "date",
                "description": "Date when the item was reported into the system (required)."
            },
            "date_incident": {
                "bsonType": "date",
                "description": "Approximate date when item was lost or found."
            },
            "created_at": {
                "bsonType": "date",
                "description": "System creation timestamp (required)."
            },
            "updated_at": {
                "bsonType": "date",
                "description": "System last update timestamp (required)."
            }
        }
    }
}

def setup_database_schema(db=None):
    """
    Creates or updates the 'items' collection with $jsonSchema validation
    and configures compound & text indexes.
    """
    if db is None:
        db = get_database()

    print("[*] Initializing MongoDB validation schema for collection 'items'...")

    try:
        # Create collection with validator if it does not exist
        db.create_collection(
            "items",
            validator=ITEMS_SCHEMA,
            validationLevel="strict",
            validationAction="error"
        )
        print("[+] Created collection 'items' with strict $jsonSchema validation.")
    except CollectionInvalid:
        # Collection already exists; apply or update validation schema using collMod
        try:
            db.command({
                "collMod": "items",
                "validator": ITEMS_SCHEMA,
                "validationLevel": "strict",
                "validationAction": "error"
            })
            print("[+] Updated existing 'items' collection with $jsonSchema validator via collMod.")
        except OperationFailure as e:
            print(f"[!] Warning updating validator: {e}")

    # Configure Indexes for high performance
    collection = db["items"]
    
    # 1. Text Index on searchable text fields
    collection.create_index(
        [
            ("title", "text"),
            ("description", "text"),
            ("specific_spot", "text"),
            ("tags", "text")
        ],
        name="item_text_search_idx"
    )

    # 2. Compound and single query indexes for filtering
    collection.create_index([("status", 1), ("type", 1)], name="idx_status_type")
    collection.create_index([("category", 1)], name="idx_category")
    collection.create_index([("campus_location", 1)], name="idx_location")
    collection.create_index([("date_reported", -1)], name="idx_date_reported_desc")

    print("[+] Created indexes: text search index and filter compound indexes.")
    return True

if __name__ == "__main__":
    setup_database_schema()
    print("[OK] Schema setup completed successfully.")
