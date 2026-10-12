"""
Anomaly detection for daily cost per resource.

Method (weekday-aware robust z-score):
  For each resource and day, the baseline is the MEDIAN cost on the same weekday over the
  previous 8 weeks. Comparing like with like matters: dev instances legitimately cost less
  on weekends, so a plain rolling average would flag every Monday. The spread is the MAD
  (median absolute deviation, robust to past spikes) with a floor of 3% of the baseline.

  A day is flagged when ALL of these hold:
    - robust z-score > Z_THRESHOLD
    - cost is at least MIN_RATIO x the baseline
    - at least MIN_WEEKS weeks of history exist

  Flagged days of the same resource (gaps of up to 1 day allowed) are merged into one event.

Functions here are pure (DataFrame in, results out). Database access lives in scripts/run_analysis.py.
"""

import warnings

import numpy as np
import pandas as pd

LOOKBACK_WEEKS = 8
MIN_WEEKS = 4
Z_THRESHOLD = 4.0
MIN_RATIO = 1.4
MIN_SCALE_PCT = 0.03
MERGE_GAP_DAYS = 2   # consecutive flagged dates at most 2 days apart belong to the same event

# Severity is based on dollars above baseline, as a share of typical monthly spend.
SEVERITY_SHARES = [("Critical", 0.015), ("High", 0.006), ("Medium", 0.003)]


def _wide(df):
    wide = df.pivot(index="date", columns="resource_id", values="cost").sort_index()
    full_index = pd.date_range(wide.index.min(), wide.index.max(), freq="D")
    return wide.reindex(full_index)


def detect_anomaly_days(df):
    """Return one row per flagged resource-day: date, resource_id, expected, actual, z."""
    wide = _wide(df)
    values = wide.to_numpy(dtype=float)

    lags = []
    for k in range(1, LOOKBACK_WEEKS + 1):
        shifted = np.full_like(values, np.nan)
        shifted[7 * k:] = values[:-7 * k]
        lags.append(shifted)
    stack = np.stack(lags)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)  # all-NaN slices at the start
        baseline = np.nanmedian(stack, axis=0)
        mad = np.nanmedian(np.abs(stack - baseline), axis=0) * 1.4826
    history = np.sum(~np.isnan(stack), axis=0)

    scale = np.maximum(mad, MIN_SCALE_PCT * baseline)
    with np.errstate(invalid="ignore", divide="ignore"):
        z = (values - baseline) / scale
        ratio = values / baseline
    flagged = (z > Z_THRESHOLD) & (ratio >= MIN_RATIO) & (history >= MIN_WEEKS)

    rows, cols = np.where(flagged)
    return pd.DataFrame({
        "date": wide.index[rows],
        "resource_id": wide.columns[cols],
        "expected": baseline[rows, cols],
        "actual": values[rows, cols],
        "z": z[rows, cols],
    }).sort_values(["resource_id", "date"]).reset_index(drop=True)


def severity_for(excess_total, monthly_reference):
    for name, share in SEVERITY_SHARES:
        if excess_total >= share * monthly_reference:
            return name
    return "Low"


def group_into_events(flagged_days, df):
    """Merge consecutive flagged days per resource into events with severity and a note."""
    if flagged_days.empty:
        return []

    meta = df.drop_duplicates("resource_id").set_index("resource_id")[["service", "region"]]
    monthly_reference = df.groupby("date")["cost"].sum().mean() * 30

    events = []
    for resource_id, days in flagged_days.groupby("resource_id"):
        days = days.sort_values("date")
        current = [days.iloc[0]]
        groups = []
        for _, row in days.iloc[1:].iterrows():
            if (row["date"] - current[-1]["date"]).days <= MERGE_GAP_DAYS:
                current.append(row)
            else:
                groups.append(current)
                current = [row]
        groups.append(current)

        for group in groups:
            g = pd.DataFrame(group)
            expected_avg = float(g["expected"].mean())
            actual_avg = float(g["actual"].mean())
            excess = float((g["actual"] - g["expected"]).sum())
            n_days = len(g)
            service = meta.loc[resource_id, "service"]
            region = meta.loc[resource_id, "region"]
            events.append({
                "resource_id": resource_id,
                "service": service,
                "region": region,
                "start_date": g["date"].min().date(),
                "end_date": g["date"].max().date(),
                "days": n_days,
                "expected_cost": round(expected_avg, 2),
                "actual_cost": round(actual_avg, 2),
                "deviation": round((actual_avg / expected_avg - 1) * 100, 1),
                "excess_total": round(excess, 2),
                "severity": severity_for(excess, monthly_reference),
                "note": (f"{resource_id} ({region}) averaged ${actual_avg:,.0f}/day vs ${expected_avg:,.0f}/day expected "
                         f"for {n_days} day{'s' if n_days > 1 else ''} - about ${excess:,.0f} above baseline."),
            })

    return sorted(events, key=lambda e: e["start_date"], reverse=True)


# ---------------------------------------------------------------- evaluation

def _label_events(labels):
    """Group the ground-truth label rows into events (same resource, consecutive days)."""
    events = []
    for resource_id, days in labels.groupby("resource_id"):
        dates = sorted(pd.to_datetime(days["date"]))
        start = prev = dates[0]
        for d in dates[1:]:
            if (d - prev).days > 1:
                events.append((resource_id, start, prev))
                start = d
            prev = d
        events.append((resource_id, start, prev))
    return events


def _prf(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def evaluate(flagged_days, labels):
    """Score flagged days against the injected ground truth, at day level and event level."""
    truth_days = set(zip(pd.to_datetime(labels["date"]), labels["resource_id"]))
    pred_days = set(zip(flagged_days["date"], flagged_days["resource_id"]))

    tp = len(truth_days & pred_days)
    fp = len(pred_days - truth_days)
    fn = len(truth_days - pred_days)
    day_level = {"true_positives": tp, "false_positives": fp, "false_negatives": fn, **_prf(tp, fp, fn)}

    truth_events = _label_events(labels)
    pred_events = []
    if not flagged_days.empty:
        pred_df = flagged_days.rename(columns={})[["date", "resource_id"]].copy()
        pred_df["date"] = pred_df["date"].dt.strftime("%Y-%m-%d")
        pred_events = _label_events(pred_df)

    def overlaps(a, b):
        return a[0] == b[0] and a[1] <= b[2] + pd.Timedelta(days=1) and b[1] <= a[2] + pd.Timedelta(days=1)

    detected = sum(1 for t in truth_events if any(overlaps(t, p) for p in pred_events))
    matched_pred = sum(1 for p in pred_events if any(overlaps(p, t) for t in truth_events))
    event_level = {
        "labeled_events": len(truth_events),
        "detected_events": len(pred_events),
        "labeled_events_found": detected,
        "false_alarm_events": len(pred_events) - matched_pred,
        **_prf(detected, len(pred_events) - matched_pred, len(truth_events) - detected),
    }
    return {"day_level": day_level, "event_level": event_level}


def naive_baseline_flags(df, window=28, z_threshold=3.0):
    """Comparison method: plain rolling mean +/- 3 sigma over the last 28 days (not weekday-aware)."""
    wide = _wide(df)
    mean = wide.shift(1).rolling(window, min_periods=window).mean()
    std = wide.shift(1).rolling(window, min_periods=window).std()
    z = (wide - mean) / std
    rows, cols = np.where((z > z_threshold).to_numpy())
    return pd.DataFrame({"date": wide.index[rows], "resource_id": wide.columns[cols]})
