"""
analytics.py: MongoDB Aggregation Pipelines Module.

Contains pre-configured aggregation pipelines demonstrating core MongoDB
features required for class assessment:
1. $group with accumulators ($sum, $avg)
2. Conditional logic ($cond, $eq)
3. Calculated projections ($project, $multiply, $divide, $round, $subtract)
4. Multi-faceted aggregation ($facet)
5. $match filtering and sorting ($sort)
"""

from config import get_database

HOTSPOTS_PIPELINE = [
    {
        "$group": {
            "_id": "$campus_location",
            "total_items": {"$sum": 1},
            "lost_count": {"$sum": {"$cond": [{"$eq": ["$type", "Lost"]}, 1, 0]}},
            "found_count": {"$sum": {"$cond": [{"$eq": ["$type", "Found"]}, 1, 0]}},
            "claimed_count": {"$sum": {"$cond": [{"$eq": ["$status", "Claimed"]}, 1, 0]}}
        }
    },
    {
        "$project": {
            "location": "$_id",
            "_id": 0,
            "total_items": 1,
            "lost_count": 1,
            "found_count": 1,
            "claimed_count": 1,
            "recovery_rate": {
                "$round": [
                    {
                        "$multiply": [
                            {"$divide": ["$claimed_count", {"$max": [1, "$total_items"]}]},
                            100
                        ]
                    },
                    1
                ]
            }
        }
    },
    {"$sort": {"total_items": -1}}
]

CATEGORY_RESOLUTION_PIPELINE = [
    {
        "$group": {
            "_id": "$category",
            "total_reported": {"$sum": 1},
            "claimed": {"$sum": {"$cond": [{"$eq": ["$status", "Claimed"]}, 1, 0]}},
            "open": {"$sum": {"$cond": [{"$eq": ["$status", "Open"]}, 1, 0]}},
            "under_review": {"$sum": {"$cond": [{"$eq": ["$status", "Under Review"]}, 1, 0]}},
            "lost_count": {"$sum": {"$cond": [{"$eq": ["$type", "Lost"]}, 1, 0]}},
            "found_count": {"$sum": {"$cond": [{"$eq": ["$type", "Found"]}, 1, 0]}}
        }
    },
    {
        "$project": {
            "category": "$_id",
            "_id": 0,
            "total_reported": 1,
            "claimed": 1,
            "open": 1,
            "under_review": 1,
            "lost_count": 1,
            "found_count": 1,
            "claim_percentage": {
                "$round": [
                    {
                        "$multiply": [
                            {"$divide": ["$claimed", {"$max": [1, "$total_reported"]}]},
                            100
                        ]
                    },
                    1
                ]
            }
        }
    },
    {"$sort": {"total_reported": -1}}
]

KPI_FACET_PIPELINE = [
    {
        "$facet": {
            "summary": [
                {
                    "$group": {
                        "_id": None,
                        "total_items": {"$sum": 1},
                        "total_lost": {"$sum": {"$cond": [{"$eq": ["$type", "Lost"]}, 1, 0]}},
                        "total_found": {"$sum": {"$cond": [{"$eq": ["$type", "Found"]}, 1, 0]}},
                        "total_claimed": {"$sum": {"$cond": [{"$eq": ["$status", "Claimed"]}, 1, 0]}},
                        "total_open": {"$sum": {"$cond": [{"$eq": ["$status", "Open"]}, 1, 0]}}
                    }
                }
            ],
            "by_status": [
                {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ],
            "by_reporter_role": [
                {"$group": {"_id": "$reporter.role", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
        }
    }
]

TURNAROUND_TIME_PIPELINE = [
    {
        "$match": {
            "status": "Claimed",
            "claim_details.claimed_date": {"$exists": True, "$ne": None}
        }
    },
    {
        "$project": {
            "category": 1,
            "campus_location": 1,
            "days_to_claim": {
                "$max": [
                    0,
                    {
                        "$round": [
                            {
                                "$divide": [
                                    {"$subtract": ["$claim_details.claimed_date", "$date_reported"]},
                                    1000 * 60 * 60 * 24
                                ]
                            },
                            1
                        ]
                    }
                ]
            }
        }
    },
    {
        "$group": {
            "_id": "$category",
            "avg_days_to_claim": {"$avg": "$days_to_claim"},
            "items_resolved": {"$sum": 1}
        }
    },
    {
        "$project": {
            "category": "$_id",
            "_id": 0,
            "avg_days_to_claim": {"$round": ["$avg_days_to_claim", 1]},
            "items_resolved": 1
        }
    },
    {"$sort": {"avg_days_to_claim": 1}}
]


def run_hotspots_aggregation(db=None):
    if db is None:
        db = get_database()
    return list(db.items.aggregate(HOTSPOTS_PIPELINE))


def run_category_resolution_aggregation(db=None):
    if db is None:
        db = get_database()
    return list(db.items.aggregate(CATEGORY_RESOLUTION_PIPELINE))


def run_kpi_facet_aggregation(db=None):
    if db is None:
        db = get_database()
    results = list(db.items.aggregate(KPI_FACET_PIPELINE))
    if not results:
        return {
            "summary": {"total_items": 0, "total_lost": 0, "total_found": 0, "total_claimed": 0, "total_open": 0, "recovery_rate": 0.0},
            "by_status": [],
            "by_reporter_role": []
        }

    raw = results[0]
    summary_list = raw.get("summary", [])
    if summary_list:
        summary = summary_list[0]
        summary.pop("_id", None)
        total = summary.get("total_items", 0)
        claimed = summary.get("total_claimed", 0)
        summary["recovery_rate"] = round((claimed / max(1, total)) * 100, 1)
    else:
        summary = {
            "total_items": 0,
            "total_lost": 0,
            "total_found": 0,
            "total_claimed": 0,
            "total_open": 0,
            "recovery_rate": 0.0
        }

    return {
        "summary": summary,
        "by_status": [{"status": item["_id"], "count": item["count"]} for item in raw.get("by_status", [])],
        "by_reporter_role": [{"role": item["_id"], "count": item["count"]} for item in raw.get("by_reporter_role", [])]
    }


def run_turnaround_aggregation(db=None):
    if db is None:
        db = get_database()
    return list(db.items.aggregate(TURNAROUND_TIME_PIPELINE))
