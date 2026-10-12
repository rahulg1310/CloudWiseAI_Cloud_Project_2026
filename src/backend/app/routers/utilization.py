from datetime import timedelta

from fastapi import APIRouter, Depends

from app.common import money, latest_date
from app.database import get_db
from app.security import get_current_user
from app.services.recommendations import UNDERUTILIZED_CPU, WINDOW_DAYS

router = APIRouter(prefix="/utilization", tags=["utilization"], dependencies=[Depends(get_current_user)])

STATUS_ORDER = {"Unattached": 0, "Underutilized": 1, "Healthy": 2}


@router.get("")
def utilization(conn=Depends(get_db)):
    """Utilization over the last 30 days: CPU for EC2/RDS, plus any unattached EBS volumes.

    Attached EBS volumes are left out because disks have no CPU figure to show.
    Problem resources come first (unattached, then underutilized), then by cost.
    """
    with conn.cursor() as cur:
        latest = latest_date(cur)
        if latest is None:
            return []
        cur.execute(
            """SELECT resource_id, service, region,
                      AVG(avg_cpu_utilization) AS cpu, SUM(usage_hours) AS hours, SUM(cost) AS cost
               FROM cost_records
               WHERE date > %s AND service IN ('EC2', 'RDS', 'EBS')
               GROUP BY resource_id, service, region""",
            (latest - timedelta(days=WINDOW_DAYS),),
        )
        rows = cur.fetchall()

    result = []
    for r in rows:
        cpu = float(r["cpu"])
        if r["service"] == "EBS":
            if float(r["hours"]) > 0:
                continue
            status, utilization_pct = "Unattached", 0
        elif cpu < UNDERUTILIZED_CPU:
            status, utilization_pct = "Underutilized", round(cpu)
        else:
            status, utilization_pct = "Healthy", round(cpu)
        result.append({
            "resource": r["resource_id"],
            "type": f"{r['service']} · {r['region']}",
            "utilization": utilization_pct,
            "status": status,
            "cost": money(r["cost"]),
        })

    return sorted(result, key=lambda x: (STATUS_ORDER[x["status"]], -x["cost"]))
