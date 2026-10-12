from datetime import timedelta

from fastapi import APIRouter, Depends, Query

from app.common import money, latest_date
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/costs", tags=["costs"], dependencies=[Depends(get_current_user)])

# Colors the frontend uses for the service breakdown bars
SERVICE_COLORS = {
    "EC2": "#22d3ee",
    "S3": "#3b82f6",
    "RDS": "#8b5cf6",
    "Lambda": "#10b981",
    "CloudFront": "#f59e0b",
}
OTHER_COLOR = "#4b5768"
TOP_SERVICES = 5


def previous_period(period):
    year, month = int(period[:4]), int(period[5:7])
    month -= 1
    if month == 0:
        year, month = year - 1, 12
    return f"{year:04d}-{month:02d}"


@router.get("/summary")
def summary(conn=Depends(get_db)):
    """Headline numbers for the dashboard KPI cards.

    'Current month' = the billing period of the newest row in cost_records,
    so it still works with a dataset that ends before today.
    """
    with conn.cursor() as cur:
        latest = latest_date(cur)
        if latest is None:
            return {"totalCost": 0, "forecastedCost": 0, "potentialSavings": 0,
                    "anomalyCount": 0, "monthOverMonthChange": 0}

        period = latest.strftime("%Y-%m")

        cur.execute("SELECT COALESCE(SUM(cost), 0) AS total FROM cost_records WHERE billing_period = %s", (period,))
        total = float(cur.fetchone()["total"])

        cur.execute("SELECT COALESCE(SUM(cost), 0) AS total FROM cost_records WHERE billing_period = %s",
                    (previous_period(period),))
        previous_total = float(cur.fetchone()["total"])
        change = round((total - previous_total) / previous_total * 100, 1) if previous_total else 0

        # Next month's forecast from the model (written by scripts/run_analysis.py).
        # Falls back to a naive estimate (last-30-day average x 30) if it hasn't been run yet.
        cur.execute("SELECT cost FROM forecasts ORDER BY month LIMIT 1")
        forecast_row = cur.fetchone()
        if forecast_row:
            forecast = float(forecast_row["cost"])
        else:
            cur.execute(
                """SELECT COALESCE(SUM(cost) / NULLIF(COUNT(DISTINCT date), 0), 0) AS daily
                   FROM cost_records WHERE date > %s""",
                (latest - timedelta(days=30),),
            )
            forecast = float(cur.fetchone()["daily"]) * 30

        cur.execute("SELECT COALESCE(SUM(potential_savings), 0) AS s FROM recommendations WHERE status = 'open'")
        savings = float(cur.fetchone()["s"])

        cur.execute("SELECT COUNT(*) AS c FROM anomalies WHERE date > %s", (latest - timedelta(days=90),))
        anomaly_count = cur.fetchone()["c"]

    return {
        "totalCost": money(total),
        "forecastedCost": money(forecast),
        "potentialSavings": money(savings),
        "anomalyCount": anomaly_count,
        "monthOverMonthChange": change,
    }


@router.get("/trend")
def trend(days: int = Query(14, ge=2, le=730), conn=Depends(get_db)):
    """Total spend per day for the most recent `days` days, oldest first."""
    with conn.cursor() as cur:
        latest = latest_date(cur)
        if latest is None:
            return []
        cur.execute(
            """SELECT date, SUM(cost) AS cost FROM cost_records
               WHERE date > %s GROUP BY date ORDER BY date""",
            (latest - timedelta(days=days),),
        )
        rows = cur.fetchall()

    return [{"date": r["date"].isoformat(), "cost": money(r["cost"])} for r in rows]


@router.get("/breakdown")
def breakdown(conn=Depends(get_db)):
    """Current-month spend by service: top 5 services plus an 'Other' bucket."""
    with conn.cursor() as cur:
        latest = latest_date(cur)
        if latest is None:
            return []
        cur.execute(
            """SELECT service, SUM(cost) AS cost FROM cost_records
               WHERE billing_period = %s GROUP BY service ORDER BY cost DESC""",
            (latest.strftime("%Y-%m"),),
        )
        rows = cur.fetchall()

    total = sum(float(r["cost"]) for r in rows) or 1
    top, rest = rows[:TOP_SERVICES], rows[TOP_SERVICES:]

    result = [
        {
            "service": r["service"],
            "cost": money(r["cost"]),
            "percent": round(float(r["cost"]) / total * 100),
            "color": SERVICE_COLORS.get(r["service"], OTHER_COLOR),
        }
        for r in top
    ]
    if rest:
        other = sum(float(r["cost"]) for r in rest)
        result.append({"service": "Other", "cost": money(other),
                       "percent": round(other / total * 100), "color": OTHER_COLOR})
    return result
