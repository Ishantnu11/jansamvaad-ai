from fastapi import APIRouter
from app.services.call_service import get_analytics_summary, list_calls

router = APIRouter()


@router.get("/summary")
async def analytics_summary():
    """Get aggregated analytics across all calls."""
    return await get_analytics_summary()


@router.get("/recent")
async def recent_calls(limit: int = 10):
    """Get the most recent completed calls."""
    return await list_calls(limit=limit, status="completed")


@router.get("/issues")
async def issue_breakdown():
    """Get categorized issue breakdown from call feedback."""
    from app.core.database import get_db
    db = get_db()
    if db is None:
        return []
    pipeline = [
        {"$match": {"feedback": {"$ne": None}}},
        {
            "$group": {
                "_id": {
                    "category": "$feedback.category",
                    "severity": "$feedback.severity",
                },
                "count": {"$sum": 1},
                "avg_duration": {"$avg": "$duration_seconds"},
            }
        },
        {"$sort": {"count": -1}},
    ]
    try:
        results = await db["calls"].aggregate(pipeline).to_list(50)
        return [
            {
                "category": r["_id"]["category"],
                "severity": r["_id"]["severity"],
                "count": r["count"],
                "avg_duration_seconds": r.get("avg_duration"),
            }
            for r in results
        ]
    except Exception:
        return []
