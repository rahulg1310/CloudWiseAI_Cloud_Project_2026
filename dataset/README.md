# Dataset

Synthetic AWS CUR-style billing data for training and demoing CloudWiseAI.

## Files

```
raw/
  cloudwise_billing.csv   daily cost per resource (15,950 rows, 2025-01-01 -> 2026-09-30)
  anomaly_labels.csv      ground-truth injected anomalies (use for evaluation only, never as a training feature)
processed/                cleaned / feature-engineered data produced by the ML pipeline
generate_dataset.py       regenerates everything above
```

## Columns (`cloudwise_billing.csv`)

| column | description |
|---|---|
| date | day of usage (YYYY-MM-DD) |
| billing_period | month (YYYY-MM) |
| service | EC2, RDS, S3, EBS, Lambda, CloudFront, Data Transfer |
| region | ap-south-1, us-east-1, eu-west-1, global |
| resource_id | 25 resources (instances, DBs, buckets, volumes, functions) |
| usage_hours | hours of usage that day |
| storage_gb | provisioned / stored GB |
| avg_cpu_utilization | average CPU % (0 for non-compute) |
| cost | daily cost in USD |

## What's baked in

- Upward cost trend (~$21k/month early 2025 to ~$26k/month in 2026) with weekly and mild yearly seasonality
- 8 injected anomaly events (20 resource-days) with known cause, listed in `anomaly_labels.csv`
- Recommendation targets: over-provisioned EC2 (CPU under 15%), 3 unattached EBS volumes, large S3 buckets, and steady 24x7 production instances and databases
- The dataset has no S3 access data, so S3 tiering candidates can only be picked by bucket size

## Regenerate

```bash
pip install pandas numpy
python dataset/generate_dataset.py --seed 42
```

This is synthetic data. Say so in the report; swap in real CUR exports later by matching the same columns.
