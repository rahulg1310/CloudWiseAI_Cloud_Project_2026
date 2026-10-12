"""
Generates a synthetic AWS CUR-style billing dataset for CloudWiseAI.

Outputs:
  dataset/raw/cloudwise_billing.csv       - daily cost per resource (what models train on)
  dataset/raw/anomaly_labels.csv          - ground-truth injected anomalies (for evaluation only)

Usage:
  python generate_dataset.py                       # defaults
  python generate_dataset.py --seed 7 --start 2025-01-01 --end 2026-09-30
"""

import argparse
import os
import numpy as np
import pandas as pd

# (resource_id, service, region, base_daily_cost, usage_hours/day, storage_gb, mean_cpu, weekend_factor, yearly_growth)
RESOURCES = [
    # EC2 - production fleet, some deliberately over-provisioned
    ("i-prod-web-01",   "EC2", "ap-south-1", 38.0, 24, 0,    62, 1.00, 0.25),
    ("i-prod-web-02",   "EC2", "ap-south-1", 38.0, 24, 0,    58, 1.00, 0.25),
    ("i-prod-api-01",   "EC2", "ap-south-1", 55.0, 24, 0,    71, 1.00, 0.30),
    ("i-prod-batch-01", "EC2", "us-east-1",  92.0, 24, 0,    11, 1.00, 0.05),   # over-provisioned
    ("i-prod-batch-02", "EC2", "us-east-1",  92.0, 24, 0,    9,  1.00, 0.05),   # over-provisioned
    ("i-dev-01",        "EC2", "us-east-1",  22.0, 24, 0,    14, 0.35, 0.00),   # idle on weekends
    ("i-dev-02",        "EC2", "us-east-1",  22.0, 24, 0,    12, 0.35, 0.00),
    ("i-analytics-01",  "EC2", "eu-west-1",  64.0, 24, 0,    46, 0.80, 0.20),
    # RDS
    ("db-orders-prod",  "RDS", "ap-south-1", 41.0, 24, 500,  64, 1.00, 0.22),
    ("db-users-prod",   "RDS", "ap-south-1", 33.0, 24, 300,  48, 1.00, 0.18),
    ("db-reports-stg",  "RDS", "us-east-1",  18.0, 24, 200,  15, 0.60, 0.05),
    # S3 - cost grows with storage
    ("s3-app-assets",   "S3",  "ap-south-1", 14.0, 24, 2200, 0,  1.00, 0.35),
    ("s3-logs-archive", "S3",  "us-east-1",  27.0, 24, 9000, 0,  1.00, 0.50),   # cold, tiering candidate
    ("s3-ml-datasets",  "S3",  "eu-west-1",  19.0, 24, 4100, 0,  1.00, 0.30),
    ("s3-backups-old",  "S3",  "us-east-1",  21.0, 24, 6500, 0,  1.00, 0.10),   # cold, tiering candidate
    # EBS
    ("vol-web-root-01", "EBS", "ap-south-1", 3.2,  24, 100,  0,  1.00, 0.00),
    ("vol-db-data-01",  "EBS", "ap-south-1", 9.5,  24, 500,  0,  1.00, 0.15),
    ("vol-orphan-01",   "EBS", "us-east-1",  4.1,  0,  500,  0,  1.00, 0.00),   # unattached
    ("vol-orphan-02",   "EBS", "us-east-1",  4.1,  0,  500,  0,  1.00, 0.00),   # unattached
    ("vol-orphan-03",   "EBS", "eu-west-1",  2.4,  0,  300,  0,  1.00, 0.00),   # unattached
    # Lambda
    ("fn-image-resize", "Lambda", "ap-south-1", 7.5,  3.0, 0, 0, 1.00, 0.40),
    ("fn-order-events", "Lambda", "ap-south-1", 11.0, 5.0, 0, 0, 1.00, 0.35),
    ("fn-nightly-etl",  "Lambda", "us-east-1",  5.2,  1.5, 0, 0, 1.00, 0.10),
    # CloudFront / Data transfer
    ("cf-main-cdn",     "CloudFront",    "global",     24.0, 24, 0, 0, 1.00, 0.45),
    ("dt-inter-region", "Data Transfer", "us-east-1",  13.0, 24, 0, 0, 0.90, 0.30),
]

# Anomalies to inject: (resource_id, start_offset_fraction, duration_days, multiplier, reason)
ANOMALY_SPECS = [
    ("i-prod-batch-01", 0.18, 3, 2.8, "runaway batch job - on-demand hours spike"),
    ("dt-inter-region", 0.30, 2, 4.0, "cross-region transfer misconfiguration"),
    ("db-orders-prod",  0.42, 2, 2.2, "storage auto-scaling loop"),
    ("fn-order-events", 0.52, 4, 3.5, "retry storm - invocation count surge"),
    ("cf-main-cdn",     0.63, 2, 3.0, "traffic spike / cache miss storm"),
    ("i-analytics-01",  0.74, 3, 2.5, "unplanned large analytics run"),
    ("s3-ml-datasets",  0.83, 2, 2.6, "bulk request / retrieval surge"),
    ("i-prod-api-01",   0.93, 2, 2.4, "autoscaling over-provision after deploy"),
]


def build(start, end, seed):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, end, freq="D")
    n = len(dates)
    t = np.arange(n) / 365.0  # years elapsed

    rows = []
    for rid, svc, region, base, hours, storage, cpu, wk, growth in RESOURCES:
        weekly = np.where(dates.dayofweek >= 5, wk, 1.0)
        trend = 1.0 + growth * t
        # mild yearly seasonality (e.g. end-of-quarter load)
        season = 1.0 + 0.04 * np.sin(2 * np.pi * (dates.dayofyear.values / 365.0))
        noise = rng.normal(1.0, 0.035, n)
        cost = base * trend * weekly * season * noise
        cost = np.clip(cost, 0.01, None)

        for i, d in enumerate(dates):
            rows.append({
                "date": d.strftime("%Y-%m-%d"),
                "billing_period": d.strftime("%Y-%m"),
                "service": svc,
                "region": region,
                "resource_id": rid,
                "usage_hours": round(hours * (weekly[i] if svc == "EC2" else 1.0), 2),
                "storage_gb": round(storage * (1 + growth * t[i]) if svc == "S3" else storage, 1),
                "avg_cpu_utilization": round(max(0.0, cpu * rng.normal(1.0, 0.08) * weekly[i]), 1) if cpu > 0 else 0.0,
                "cost": round(float(cost[i]), 4),
            })

    df = pd.DataFrame(rows)

    # inject anomalies
    labels = []
    for rid, frac, dur, mult, reason in ANOMALY_SPECS:
        start_i = int(frac * n)
        for k in range(dur):
            day = dates[start_i + k].strftime("%Y-%m-%d")
            mask = (df["resource_id"] == rid) & (df["date"] == day)
            normal_cost = float(df.loc[mask, "cost"].iloc[0])
            df.loc[mask, "cost"] = round(normal_cost * mult, 4)
            df.loc[mask, "usage_hours"] = round(float(df.loc[mask, "usage_hours"].iloc[0]) * min(mult, 1.0), 2)
            service = df.loc[mask, "service"].iloc[0]
            labels.append({
                "date": day, "resource_id": rid, "service": service,
                "expected_cost": round(normal_cost, 4), "actual_cost": round(normal_cost * mult, 4),
                "multiplier": mult, "reason": reason,
            })

    return df, pd.DataFrame(labels)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2025-01-01")
    p.add_argument("--end", default="2026-09-30")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "raw"))
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    df, labels = build(args.start, args.end, args.seed)
    df.to_csv(os.path.join(args.out, "cloudwise_billing.csv"), index=False)
    labels.to_csv(os.path.join(args.out, "anomaly_labels.csv"), index=False)

    print(f"billing rows: {len(df):,}  ({df['date'].min()} -> {df['date'].max()})")
    print(f"resources: {df['resource_id'].nunique()}  services: {df['service'].nunique()}")
    print(f"injected anomaly resource-days: {len(labels)}")
    print(f"total cost: ${df['cost'].sum():,.2f}")


if __name__ == "__main__":
    main()
