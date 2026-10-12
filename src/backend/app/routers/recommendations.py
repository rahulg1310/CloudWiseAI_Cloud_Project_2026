from fastapi import APIRouter, Depends

from app.common import money
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/recommendations", tags=["recommendations"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_recommendations(conn=Depends(get_db)):
    """Open recommendations, biggest estimated monthly saving first."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, title, service, category, description, potential_savings, effort
               FROM recommendations WHERE status = 'open' ORDER BY potential_savings DESC"""
        )
        rows = cur.fetchall()

    return [
        {
            "id": r["id"],
            "title": r["title"],
            "service": r["service"],
            "category": r["category"],
            "description": r["description"],
            "potentialSavings": money(r["potential_savings"]),
            "effort": r["effort"],
        }
        for r in rows
    ]
