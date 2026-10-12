import calendar
from datetime import timedelta

from fastapi import APIRouter, Depends

from app.common import money, latest_date
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/predictions", tags=["predictions"], dependencies=[Depends(get_current_user)])

HISTORY_MONTHS = 6


@router.get("")
def predictions(conn=Depends(get_db)):
    """Last 6 complete months of actual spend plus the stored 3-month forecast."""
    with conn.cursor() as cur:
        latest = latest_date(cur)
        if latest is None:
            return {"historical": [], "forecast": []}

        # Only complete months: if the data stops mid-month, leave that month out.
        last_day = calendar.monthrange(latest.year, latest.month)[1]
        cutoff = latest if latest.day == last_day else latest.replace(day=1) - timedelta(days=1)

        cur.execute(
            """SELECT billing_period, SUM(cost) AS cost FROM cost_records
               WHERE date <= %s GROUP BY billing_period ORDER BY billing_period DESC LIMIT %s""",
            (cutoff, HISTORY_MONTHS),
        )
        history = list(reversed(cur.fetchall()))

        cur.execute("SELECT month, cost, confidence, model FROM forecasts ORDER BY month")
        forecast_rows = cur.fetchall()

    def label(period):  # '2026-09' -> 'Sep'
        return calendar.month_abbr[int(period[5:7])]

    return {
        "historical": [{"month": label(r["billing_period"]), "cost": money(r["cost"])} for r in history],
        "forecast": [{"month": label(r["month"]), "cost": money(r["cost"]), "confidence": float(r["confidence"])}
                     for r in forecast_rows],
        "model": forecast_rows[0]["model"] if forecast_rows else None,
    }
