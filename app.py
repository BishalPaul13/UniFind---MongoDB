"""
app.py: Flask Web Server with PyMongo & MongoDB Atlas/Local Integration.

Provides:
- Web dashboard interface
- Complete RESTful CRUD API with PyMongo
- Native MongoDB Schema Validation handling
- Advanced Aggregation Pipelines for analytics
- On-demand database seeding and schema inspector
"""

import os
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from flask import Flask, jsonify, render_template, request
from pymongo.errors import OperationFailure, PyMongoError, WriteError

from analytics import (
    CATEGORY_RESOLUTION_PIPELINE,
    HOTSPOTS_PIPELINE,
    KPI_FACET_PIPELINE,
    TURNAROUND_TIME_PIPELINE,
    run_category_resolution_aggregation,
    run_hotspots_aggregation,
    run_kpi_facet_aggregation,
    run_turnaround_aggregation,
)
from config import PORT, SECRET_KEY, get_database
from db_validator import ITEMS_SCHEMA, setup_database_schema
from seed_data import seed_database

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

# Ensure database schema & indexes are ready
db = get_database()
setup_database_schema(db)


# =========================================================================
# 🎓 TEACHER / VIVA QUERY CONTROLLER:
# Modify these queries directly in this file as requested by your teacher!
# Flask auto-reloads on save (Ctrl+S), so refreshing your browser will
# instantly show the updated data!
# =========================================================================

# --- [1] MAIN ITEMS QUERY (Modify this dict to filter items shown on UI) ---
# Examples for teacher viva:
#   TEACHER_ITEMS_FILTER = {}                                      # Show all items (Default)
#   TEACHER_ITEMS_FILTER = {"type": "Lost"}                        # Show only Lost items
#   TEACHER_ITEMS_FILTER = {"type": "Found"}                       # Show only Found items
#   TEACHER_ITEMS_FILTER = {"campus_location": "Central Library"} # Show only Library items
#   TEACHER_ITEMS_FILTER = {"category": "Electronics"}            # Show only Electronics
#   TEACHER_ITEMS_FILTER = {"status": "Open"}                     # Show only Unclaimed items
#   TEACHER_ITEMS_FILTER = {"reporter.role": "Student"}           # Show items reported by Students
#   TEACHER_ITEMS_FILTER = {"tags": "apple"}                      # Show items with tag 'apple'
TEACHER_ITEMS_FILTER = {}

# --- [2] ITEMS SORT ORDER (Modify this list to change ordering) ---
# Examples:
#   TEACHER_ITEMS_SORT = [("date_reported", -1)]                  # Newest first (Default)
#   TEACHER_ITEMS_SORT = [("date_reported", 1)]                   # Oldest first
#   TEACHER_ITEMS_SORT = [("title", 1)]                           # Alphabetical (A to Z)
TEACHER_ITEMS_SORT = [("date_reported", -1)]


def serialize_item(doc):
    """
    Serializes a MongoDB item document into a JSON-friendly dictionary.
    Converts ObjectId and datetime objects to ISO strings.
    """
    if not doc:
        return None
    item = dict(doc)
    item["_id"] = str(item["_id"])
    for dt_key in ["date_reported", "date_incident", "created_at", "updated_at"]:
        if item.get(dt_key) and isinstance(item[dt_key], datetime):
            item[dt_key] = item[dt_key].isoformat()
    if item.get("claim_details") and isinstance(item["claim_details"].get("claimed_date"), datetime):
        item["claim_details"]["claimed_date"] = item["claim_details"]["claimed_date"].isoformat()
    return item


@app.route("/")
def index():
    """Renders the main dashboard UI."""
    return render_template("index.html")


# ==========================================
# CRUD Operations: Items API
# ==========================================

@app.route("/api/items", methods=["GET"])
def get_items():
    """
    READ (List with search and filters).
    Starts with TEACHER_ITEMS_FILTER from Python code, allowing live viva modifications!
    """
    try:
        # Start with Teacher's filter defined in python code above
        query = dict(TEACHER_ITEMS_FILTER)

        item_type = request.args.get("type", "").strip()
        category = request.args.get("category", "").strip()
        location = request.args.get("location", "").strip()
        status = request.args.get("status", "").strip()
        search_query = request.args.get("search", "").strip()
        sort_by = request.args.get("sort", "").strip()

        if item_type and "type" not in query:
            query["type"] = item_type
        if category and "category" not in query:
            query["category"] = category
        if location and "campus_location" not in query:
            query["campus_location"] = location
        if status and "status" not in query:
            query["status"] = status

        if search_query:
            query["$or"] = [
                {"title": {"$regex": search_query, "$options": "i"}},
                {"description": {"$regex": search_query, "$options": "i"}},
                {"specific_spot": {"$regex": search_query, "$options": "i"}},
                {"tags": {"$regex": search_query, "$options": "i"}}
            ]

        # Sorting logic: Default to TEACHER_ITEMS_SORT
        sort_field = TEACHER_ITEMS_SORT
        if sort_by == "date_asc":
            sort_field = [("date_reported", 1)]
        elif sort_by == "title_asc":
            sort_field = [("title", 1)]

        cursor = db.items.find(query).sort(sort_field).limit(100)
        items = [serialize_item(doc) for doc in cursor]

        return jsonify({
            "success": True,
            "count": len(items),
            "teacher_filter_active": bool(TEACHER_ITEMS_FILTER),
            "active_code_filter": TEACHER_ITEMS_FILTER,
            "items": items
        })
    except PyMongoError as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500


@app.route("/api/items/<item_id>", methods=["GET"])
def get_item(item_id):
    """READ (Single Item by ObjectId)."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return jsonify({"success": False, "error": "Invalid item ID format"}), 400

    try:
        doc = db.items.find_one({"_id": oid})
        if not doc:
            return jsonify({"success": False, "error": "Item not found"}), 404
        return jsonify({"success": True, "item": serialize_item(doc)})
    except PyMongoError as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500


@app.route("/api/items", methods=["POST"])
def create_item():
    """
    CREATE (Report New Item).
    Validates input and inserts into MongoDB.
    Triggered MongoDB schema validation errors are caught and returned clearly.
    """
    data = request.get_json() or {}
    now = datetime.now(timezone.utc)

    # Basic parsing & date conversion
    try:
        date_incident = None
        if data.get("date_incident"):
            try:
                date_incident = datetime.fromisoformat(data["date_incident"].replace("Z", "+00:00"))
            except ValueError:
                date_incident = now

        tags_raw = data.get("tags", [])
        if isinstance(tags_raw, str):
            tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
        elif isinstance(tags_raw, list):
            tags = [str(t).strip().lower() for t in tags_raw if str(t).strip()]
        else:
            tags = []

        new_doc = {
            "title": str(data.get("title", "")).strip(),
            "description": str(data.get("description", "")).strip(),
            "type": data.get("type"),
            "category": data.get("category"),
            "campus_location": data.get("campus_location"),
            "specific_spot": str(data.get("specific_spot", "")).strip(),
            "reporter": {
                "name": str(data.get("reporter_name", "")).strip(),
                "email": str(data.get("reporter_email", "")).strip(),
                "phone": str(data.get("reporter_phone", "")).strip(),
                "role": data.get("reporter_role", "Student")
            },
            "status": "Open",
            "tags": tags,
            "date_reported": now,
            "date_incident": date_incident or now,
            "created_at": now,
            "updated_at": now
        }

        # MongoDB insert with PyMongo
        result = db.items.insert_one(new_doc)
        created_doc = db.items.find_one({"_id": result.inserted_id})

        return jsonify({
            "success": True,
            "message": f"Successfully reported {new_doc['type']} item!",
            "item": serialize_item(created_doc)
        }), 201

    except WriteError as we:
        # Caught when MongoDB $jsonSchema rejects the document
        return jsonify({
            "success": False,
            "error": "MongoDB Schema Validation Error: The document failed collection validator constraints.",
            "details": str(we)
        }), 422
    except PyMongoError as pe:
        return jsonify({"success": False, "error": f"Database write error: {str(pe)}"}), 500
    except Exception as ex:
        return jsonify({"success": False, "error": f"Unexpected error: {str(ex)}"}), 400


@app.route("/api/items/<item_id>", methods=["PUT"])
def update_item(item_id):
    """
    UPDATE (Modify Item Details).
    """
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return jsonify({"success": False, "error": "Invalid item ID format"}), 400

    data = request.get_json() or {}
    now = datetime.now(timezone.utc)

    update_fields = {"updated_at": now}

    if "title" in data:
        update_fields["title"] = str(data["title"]).strip()
    if "description" in data:
        update_fields["description"] = str(data["description"]).strip()
    if "category" in data:
        update_fields["category"] = data["category"]
    if "campus_location" in data:
        update_fields["campus_location"] = data["campus_location"]
    if "specific_spot" in data:
        update_fields["specific_spot"] = str(data["specific_spot"]).strip()
    if "status" in data:
        update_fields["status"] = data["status"]
    if "tags" in data:
        if isinstance(data["tags"], list):
            update_fields["tags"] = [str(t).strip().lower() for t in data["tags"]]
        elif isinstance(data["tags"], str):
            update_fields["tags"] = [t.strip().lower() for t in data["tags"].split(",") if t.strip()]

    try:
        result = db.items.update_one({"_id": oid}, {"$set": update_fields})
        if result.matched_count == 0:
            return jsonify({"success": False, "error": "Item not found"}), 404

        updated_doc = db.items.find_one({"_id": oid})
        return jsonify({
            "success": True,
            "message": "Item updated successfully",
            "item": serialize_item(updated_doc)
        })
    except WriteError as we:
        return jsonify({
            "success": False,
            "error": "MongoDB Schema Validation Error: Update violates schema constraints.",
            "details": str(we)
        }), 422
    except PyMongoError as pe:
        return jsonify({"success": False, "error": f"Database error: {str(pe)}"}), 500


@app.route("/api/items/<item_id>/claim", methods=["PATCH"])
def claim_item(item_id):
    """
    UPDATE action: Resolve and mark item as Claimed with claimant details.
    """
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return jsonify({"success": False, "error": "Invalid item ID format"}), 400

    data = request.get_json() or {}
    claimant_name = str(data.get("claimant_name", "Verified Student")).strip()
    notes = str(data.get("verification_notes", "Verified ownership on campus.")).strip()
    now = datetime.now(timezone.utc)

    update_payload = {
        "$set": {
            "status": "Claimed",
            "claim_details": {
                "claimed_by_name": claimant_name,
                "claimed_date": now,
                "verification_notes": notes
            },
            "updated_at": now
        }
    }

    try:
        result = db.items.update_one({"_id": oid}, update_payload)
        if result.matched_count == 0:
            return jsonify({"success": False, "error": "Item not found"}), 404

        updated_doc = db.items.find_one({"_id": oid})
        return jsonify({
            "success": True,
            "message": f"Item marked as claimed by '{claimant_name}'!",
            "item": serialize_item(updated_doc)
        })
    except PyMongoError as pe:
        return jsonify({"success": False, "error": f"Database error: {str(pe)}"}), 500


@app.route("/api/items/<item_id>", methods=["DELETE"])
def delete_item(item_id):
    """
    DELETE (Remove Item by ObjectId).
    """
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        return jsonify({"success": False, "error": "Invalid item ID format"}), 400

    try:
        result = db.items.delete_one({"_id": oid})
        if result.deleted_count == 0:
            return jsonify({"success": False, "error": "Item not found"}), 404
        return jsonify({"success": True, "message": "Item deleted permanently from MongoDB"})
    except PyMongoError as pe:
        return jsonify({"success": False, "error": f"Database error: {str(pe)}"}), 500


# ==========================================
# MongoDB Aggregation Pipelines API
# ==========================================

@app.route("/api/analytics/summary", methods=["GET"])
def get_analytics_summary():
    """Runs Pipeline 3: Multi-facet KPI Overview ($facet)."""
    try:
        data = run_kpi_facet_aggregation(db)
        return jsonify({
            "success": True,
            "data": data,
            "pipeline": KPI_FACET_PIPELINE
        })
    except PyMongoError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analytics/hotspots", methods=["GET"])
def get_analytics_hotspots():
    """Runs Pipeline 1: Campus Hotspots ($group, $project, $sort)."""
    try:
        data = run_hotspots_aggregation(db)
        return jsonify({
            "success": True,
            "data": data,
            "pipeline": HOTSPOTS_PIPELINE
        })
    except PyMongoError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analytics/categories", methods=["GET"])
def get_analytics_categories():
    """Runs Pipeline 2: Category Recovery Resolution Rate ($group, $cond, $project)."""
    try:
        data = run_category_resolution_aggregation(db)
        return jsonify({
            "success": True,
            "data": data,
            "pipeline": CATEGORY_RESOLUTION_PIPELINE
        })
    except PyMongoError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analytics/turnaround", methods=["GET"])
def get_analytics_turnaround():
    """Runs Pipeline 4: Average Resolution Turnaround Time ($match, $project, $group)."""
    try:
        data = run_turnaround_aggregation(db)
        return jsonify({
            "success": True,
            "data": data,
            "pipeline": TURNAROUND_TIME_PIPELINE
        })
    except PyMongoError as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# Schema & Presentation Utilities
# ==========================================

@app.route("/api/schema", methods=["GET"])
def get_schema():
    """Returns the MongoDB JSON Schema for the inspector tab."""
    return jsonify({
        "success": True,
        "collection": "items",
        "schema": ITEMS_SCHEMA
    })


@app.route("/api/seed", methods=["POST"])
def trigger_seed():
    """Re-seeds database with sample campus items."""
    try:
        count = seed_database(db, drop_existing=True)
        return jsonify({
            "success": True,
            "message": f"Successfully re-seeded {count} sample items into MongoDB."
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/test-validation", methods=["POST"])
def test_validation():
    """
    Demonstration endpoint:
    Attempts to insert an intentionally invalid document into MongoDB
    to prove $jsonSchema enforcement to the professor.
    """
    # Missing required 'reporter' object, invalid email, illegal category enum
    invalid_doc = {
        "title": "AB",  # Fails minLength 3
        "description": "Tiny",  # Fails minLength 5
        "type": "NotAValidType",  # Fails enum
        "category": "InvalidCategoryName",  # Fails enum
        "campus_location": "InvalidBuildingName",
        "date_reported": "not-a-date",  # Fails bsonType date
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }

    try:
        db.items.insert_one(invalid_doc)
        return jsonify({
            "success": True,
            "message": "Warning: MongoDB accepted document unexpectedly."
        })
    except WriteError as we:
        return jsonify({
            "success": False,
            "validation_caught": True,
            "message": "MongoDB successfully rejected the invalid document as expected via $jsonSchema!",
            "rejection_details": str(we)
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "validation_caught": True,
            "message": "Operation rejected by database.",
            "rejection_details": str(e)
        }), 200


@app.route("/health", methods=["GET"])

def health_check():
    """Render and deployment health check endpoint."""
    try:
        db.command("ping")
        return jsonify({"status": "healthy", "mongodb": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


if __name__ == "__main__":
    print(f"[*] Starting UniFind Web Server on http://127.0.0.1:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
