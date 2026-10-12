"""
Rule-based cost optimization recommendations.

Every rule works on the most recent 30 days of data and documents its savings assumption:

  EC2 right-sizing       avg CPU < 20%                      -> assume one size down halves the price (50%)
  RDS right-sizing       avg CPU < 20%                      -> same assumption (50%)
  EC2 Savings Plan       24x7, steady cost, not right-sized -> 25% off on-demand (1-year, no upfront)
  RDS Reserved Instance  24x7, steady cost, CPU >= 20%      -> 30% off on-demand (1-year, no upfront)
  Unattached EBS         0 usage hours in the last 30 days  -> 100% of the volume cost
  S3 lifecycle           bucket >= 5 TB                     -> 40% (Standard -> Standard-IA)

Limits worth stating in the report:
  - The dataset has no S3 access data, so S3 candidates are chosen by size only.
  - Savings Plan / RI discounts are typical list-price figures, not account-specific quotes.
  - Right-sized instances are excluded from commitment recommendations so savings aren't double counted.

Monthly cost = 30 x the MEDIAN daily cost over the last 30 days (robust to one-off spikes).
Pure functions: DataFrame in, list of recommendation dicts out.
"""

import pandas as pd

WINDOW_DAYS = 30
STEADY_WINDOW_DAYS = 90

UNDERUTILIZED_CPU = 20          # percent, also used by the /utilization endpoint
RIGHTSIZE_SAVINGS = 0.50
SAVINGS_PLAN_DISCOUNT = 0.25
RDS_RI_DISCOUNT = 0.30
S3_TIERING_SAVINGS = 0.40
S3_MIN_GB = 5000
STEADY_MAX_VARIATION = 0.10     # robust coefficient of variation of daily cost
ALWAYS_ON_SHARE = 0.95          # share of days running a full 24 hours


def _names(resource_ids, limit=4):
    ids = list(resource_ids)
    text = ", ".join(ids[:limit])
    return text + (f" and {len(ids) - limit} more" if len(ids) > limit else "")


def _resource_stats(df):
    latest = df["date"].max()
    recent = df[df["date"] > latest - pd.Timedelta(days=WINDOW_DAYS)]
    long = df[df["date"] > latest - pd.Timedelta(days=STEADY_WINDOW_DAYS)]

    stats = recent.groupby("resource_id").agg(
        service=("service", "first"),
        region=("region", "first"),
        cpu=("avg_cpu_utilization", "mean"),
        hours=("usage_hours", "sum"),
        storage_gb=("storage_gb", "max"),
        daily_cost=("cost", "median"),
    )
    stats["monthly_cost"] = stats["daily_cost"] * 30

    def robust_cv(series):
        median = series.median()
        mad = (series - median).abs().median() * 1.4826
        return mad / median if median else 0.0

    stats["variation"] = long.groupby("resource_id")["cost"].apply(robust_cv)
    stats["always_on"] = long.groupby("resource_id")["usage_hours"].apply(lambda s: (s >= 23).mean())
    return stats


def generate_recommendations(df):
    stats = _resource_stats(df)
    recs = []

    # ---- right-sizing (EC2, RDS)
    rightsized = set()
    for service, label in [("EC2", "EC2 instances"), ("RDS", "RDS databases")]:
        low = stats[(stats["service"] == service) & (stats["cpu"] < UNDERUTILIZED_CPU)]
        if low.empty:
            continue
        rightsized |= set(low.index) if service == "EC2" else set()
        savings = float(low["monthly_cost"].sum() * RIGHTSIZE_SAVINGS)
        cpu_range = f"{low['cpu'].min():.0f}-{low['cpu'].max():.0f}%" if len(low) > 1 else f"{low['cpu'].iloc[0]:.0f}%"
        recs.append({
            "title": f"Right-size {len(low)} over-provisioned {label}",
            "service": service,
            "category": "Right-sizing",
            "description": (f"Average CPU was {cpu_range} over the last {WINDOW_DAYS} days on {_names(low.index)}. "
                            f"Moving down one instance size is assumed to halve their cost."),
            "potential_savings": round(savings, 2),
            "effort": "Medium",
        })

    # ---- EC2 Savings Plan on steady, always-on, not-right-sized instances
    ec2 = stats[(stats["service"] == "EC2")]
    steady = ec2[(ec2["variation"] <= STEADY_MAX_VARIATION) & (ec2["always_on"] >= ALWAYS_ON_SHARE)
                 & (~ec2.index.isin(rightsized))]
    if not steady.empty:
        base = float(steady["monthly_cost"].sum())
        recs.append({
            "title": "Purchase a Compute Savings Plan for steady-state EC2",
            "service": "EC2",
            "category": "Commitment",
            "description": (f"{_names(steady.index)} run 24x7 with stable cost (about ${base:,.0f}/month combined). "
                            f"A 1-year no-upfront Savings Plan is assumed to save {SAVINGS_PLAN_DISCOUNT:.0%}. "
                            f"Right-sizing candidates are excluded."),
            "potential_savings": round(base * SAVINGS_PLAN_DISCOUNT, 2),
            "effort": "Medium",
        })

    # ---- RDS Reserved Instances on steady, healthy databases
    rds = stats[(stats["service"] == "RDS")]
    steady_db = rds[(rds["variation"] <= STEADY_MAX_VARIATION) & (rds["always_on"] >= ALWAYS_ON_SHARE)
                    & (rds["cpu"] >= UNDERUTILIZED_CPU)]
    if not steady_db.empty:
        base = float(steady_db["monthly_cost"].sum())
        recs.append({
            "title": "Reserve capacity for steady production databases",
            "service": "RDS",
            "category": "Commitment",
            "description": (f"{_names(steady_db.index)} run 24x7 with stable cost (about ${base:,.0f}/month combined). "
                            f"1-year Reserved Instances are assumed to save {RDS_RI_DISCOUNT:.0%}."),
            "potential_savings": round(base * RDS_RI_DISCOUNT, 2),
            "effort": "Medium",
        })

    # ---- unattached EBS volumes
    ebs = stats[(stats["service"] == "EBS") & (stats["hours"] == 0)]
    if not ebs.empty:
        recs.append({
            "title": f"Delete {len(ebs)} unattached EBS volumes",
            "service": "EBS",
            "category": "Cleanup",
            "description": (f"{_names(ebs.index)} had no attached instance in the last {WINDOW_DAYS} days "
                            f"but still bill for {ebs['storage_gb'].sum():,.0f} GB. Snapshot first if the data might be needed."),
            "potential_savings": round(float(ebs["monthly_cost"].sum()), 2),
            "effort": "Low",
        })

    # ---- large S3 buckets -> lifecycle rules
    s3 = stats[(stats["service"] == "S3") & (stats["storage_gb"] >= S3_MIN_GB)]
    if not s3.empty:
        recs.append({
            "title": f"Add lifecycle rules to {len(s3)} large S3 buckets",
            "service": "S3",
            "category": "Storage tiering",
            "description": (f"{_names(s3.index)} hold {s3['storage_gb'].sum() / 1000:,.1f} TB. Transitioning older objects to "
                            f"Standard-IA is assumed to save {S3_TIERING_SAVINGS:.0%}. Confirm access patterns in S3 Storage Lens first."),
            "potential_savings": round(float(s3["monthly_cost"].sum() * S3_TIERING_SAVINGS), 2),
            "effort": "Low",
        })

    return sorted(recs, key=lambda r: r["potential_savings"], reverse=True)
