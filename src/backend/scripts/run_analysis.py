"""
Runs the analysis pipeline over cost_records and stores the results.

  1. Anomaly detection      -> anomalies table      + results/anomaly_detection_metrics.json
  2. Recommendations        -> recommendations table
  3. Forecasting            -> forecasts table      + results/forecast_metrics.json

Re-run it whenever cost_records changes. Each run replaces the previous results.

Usage (from src/backend):
  export DATABASE_URL=postgresql://user:password@localhost:5432/cloudwise
  python scripts/run_analysis.py
"""

import json
import os
import sys

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services import anomalies as anomaly_service          # noqa: E402
from app.services import forecasting as forecast_service        # noqa: E402
from app.services.recommendations import generate_recommendations  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "schema.sql")
LABELS_PATH = os.path.join(ROOT, "dataset", "raw", "anomaly_labels.csv")
RESULTS_DIR = os.path.join(ROOT, "results")


def load_costs(cur):
    cur.execute("""SELECT date, service, region, resource_id, usage_hours, storage_gb,
                          avg_cpu_utilization, cost FROM cost_records ORDER BY date""")
    df = pd.DataFrame(cur.fetchall())
    if df.empty:
        sys.exit("cost_records is empty - run scripts/load_dataset.py first.")
    df["date"] = pd.to_datetime(df["date"])
    for col in ["usage_hours", "storage_gb", "avg_cpu_utilization", "cost"]:
        df[col] = df[col].astype(float)
    return df


def save_json(name, payload):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return path


def run_anomalies(cur, df):
    flagged = anomaly_service.detect_anomaly_days(df)
    events = anomaly_service.group_into_events(flagged, df)

    cur.execute("TRUNCATE anomalies RESTART IDENTITY")
    if events:
        execute_values(cur,
            "INSERT INTO anomalies (service, resource_id, date, expected_cost, actual_cost, deviation, severity, note) VALUES %s",
            [(e["service"], e["resource_id"], e["start_date"], e["expected_cost"], e["actual_cost"],
              e["deviation"], e["severity"], e["note"]) for e in events])

    print(f"Anomalies: {len(flagged)} flagged resource-days -> {len(events)} events")

    metrics = {
        "method": "weekday-aware robust z-score",
        "parameters": {"lookback_weeks": anomaly_service.LOOKBACK_WEEKS, "z_threshold": anomaly_service.Z_THRESHOLD,
                       "min_ratio": anomaly_service.MIN_RATIO},
        "events_detected": len(events),
    }
    if os.path.exists(LABELS_PATH):
        labels = pd.read_csv(LABELS_PATH)
        metrics["this_method"] = anomaly_service.evaluate(flagged, labels)
        metrics["naive_rolling_3_sigma_baseline"] = anomaly_service.evaluate(
            anomaly_service.naive_baseline_flags(df), labels)
        m = metrics["this_method"]
        n = metrics["naive_rolling_3_sigma_baseline"]
        print(f"  vs labels (day level):  precision {m['day_level']['precision']}  recall {m['day_level']['recall']}  "
              f"(naive baseline: precision {n['day_level']['precision']}  recall {n['day_level']['recall']})")
    else:
        print("  (no anomaly_labels.csv found - skipping evaluation)")

    save_json("anomaly_detection_metrics.json", metrics)
    return flagged


def run_recommendations(cur, df):
    recs = generate_recommendations(df)
    cur.execute("DELETE FROM recommendations WHERE status = 'open'")
    if recs:
        execute_values(cur,
            "INSERT INTO recommendations (title, service, category, description, potential_savings, effort) VALUES %s",
            [(r["title"], r["service"], r["category"], r["description"], r["potential_savings"], r["effort"]) for r in recs])
    total = sum(r["potential_savings"] for r in recs)
    print(f"Recommendations: {len(recs)} generated, ${total:,.2f}/month potential savings")


def run_forecast(cur, df, flagged):
    daily = df.groupby("date")["cost"].sum()

    # Train on "normal" spend: take each flagged spike out of the history so the model doesn't learn it.
    if not flagged.empty:
        excess = (flagged["actual"] - flagged["expected"]).groupby(flagged["date"]).sum()
        daily = daily.sub(excess, fill_value=0).clip(lower=0)

    # Only use complete months, so the forecast starts on the 1st of a month.
    last = daily.index.max()
    if last != last + pd.offsets.MonthEnd(0):
        daily = daily[daily.index <= last - pd.offsets.MonthEnd(1)]

    result = forecast_service.forecast(daily)

    cur.execute("TRUNCATE forecasts")
    execute_values(cur,
        "INSERT INTO forecasts (month, cost, confidence, model) VALUES %s",
        [(f["month"], f["cost"], f["confidence"], result["model"]) for f in result["forecasts"]])

    print(f"Forecast: model = {result['model']}")
    for f in result["forecasts"]:
        print(f"  {f['month']}  ${f['cost']:,.2f}  (confidence {f['confidence']:.0%})")
    for name, m in result["metrics"].get("models", {}).items():
        print(f"  backtest {name:<15} monthly MAPE {m['monthly_mape_mean']:.1%}   daily MAE ${m['daily_mae']:,.2f}")

    save_json("forecast_metrics.json", {**result["metrics"], "forecasts": result["forecasts"]})


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        sys.exit("Set DATABASE_URL first, e.g. postgresql://user:password@localhost:5432/cloudwise")

    conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    try:
        with conn, conn.cursor() as cur:
            with open(SCHEMA_PATH, encoding="utf-8") as f:
                cur.execute(f.read())
            df = load_costs(cur)
            print(f"Loaded {len(df):,} rows ({df['date'].min().date()} -> {df['date'].max().date()})")
            flagged = run_anomalies(cur, df)
            run_recommendations(cur, df)
            run_forecast(cur, df, flagged)
        print(f"Metrics saved to {os.path.abspath(RESULTS_DIR)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
