from fastapi import APIRouter, Depends, Query

from app.common import money
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/anomalies", tags=["anomalies"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_anomalies(limit: int = Query(50, ge=1, le=500), conn=Depends(get_db)):
    """Detected cost anomalies, newest first. Costs are per-day averages over the event."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT id, service, date, expected_cost, actual_cost, deviation, severity, note
               FROM anomalies ORDER BY date DESC, id LIMIT %s""",
            (limit,),
        )
        rows = cur.fetchall()

    return [
        {
            "id": r["id"],
            "service": r["service"],
            "date": r["date"].isoformat(),
            "expectedCost": money(r["expected_cost"]),
            "actualCost": money(r["actual_cost"]),
            "deviation": float(r["deviation"]),
            "severity": r["severity"],
            "note": r["note"],
        }
        for r in rows
    ]
