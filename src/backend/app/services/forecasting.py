"""
Monthly cloud cost forecasting.

Input is a daily total-cost series. Three candidate models forecast DAILY cost, which is
summed into calendar months:

  seasonal_naive  mean of the last 28 days for each weekday (no trend)
  ridge           linear trend + day-of-week + yearly sine/cosine
  ridge_xgboost   ridge, then XGBoost fitted on the ridge residuals (day of week, day of year, day of month)

The best model is chosen by a rolling-origin backtest: train on the first N months, forecast the
next 3, repeat for every N from 12 months up. Error is MAPE on the MONTHLY total, per horizon.

`confidence` in the output is 1 - backtest MAPE at that horizon for the chosen model. It is a
measured historical accuracy, not a statistical confidence interval.

Pure functions: no database access.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor

HORIZON_MONTHS = 3
MIN_TRAIN_MONTHS = 12


# ---------------------------------------------------------------- features

def _calendar(dates):
    d = pd.DatetimeIndex(dates)
    return d.dayofweek.to_numpy(), d.dayofyear.to_numpy(), d.day.to_numpy()


def _ridge_features(dates, origin):
    d = pd.DatetimeIndex(dates)
    dow, doy, _ = _calendar(d)
    t = (d - origin).days.to_numpy() / 365.0
    angle = doy / 365.25 * 2 * np.pi
    return np.column_stack([t, np.eye(7)[dow][:, 1:], np.sin(angle), np.cos(angle)])


def _tree_features(dates):
    dow, doy, dom = _calendar(dates)
    return np.column_stack([dow, doy, dom])


# ---------------------------------------------------------------- models
# Each takes (train: Series indexed by date, future_dates) and returns an array of daily predictions.

def _seasonal_naive(train, future_dates):
    last = train.iloc[-28:]
    by_weekday = last.groupby(last.index.dayofweek).mean()
    return np.array([by_weekday[d] for d in pd.DatetimeIndex(future_dates).dayofweek])


def _fit_ridge(train):
    origin = train.index[0]
    model = Ridge(alpha=1e-3).fit(_ridge_features(train.index, origin), train.to_numpy())
    return model, origin


def _ridge(train, future_dates):
    model, origin = _fit_ridge(train)
    return model.predict(_ridge_features(future_dates, origin))


def _ridge_xgboost(train, future_dates):
    model, origin = _fit_ridge(train)
    residual = train.to_numpy() - model.predict(_ridge_features(train.index, origin))
    booster = XGBRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, subsample=0.8,
                           random_state=0, verbosity=0)
    booster.fit(_tree_features(train.index), residual)
    return model.predict(_ridge_features(future_dates, origin)) + booster.predict(_tree_features(future_dates))


MODELS = {"seasonal_naive": _seasonal_naive, "ridge": _ridge, "ridge_xgboost": _ridge_xgboost}


# ---------------------------------------------------------------- helpers

def _monthly(daily):
    return daily.groupby(daily.index.to_period("M")).sum()


def _forecast_monthly(model_fn, train, months_ahead):
    """Forecast `months_ahead` calendar months after the last (month-end) training date."""
    start = train.index[-1] + pd.Timedelta(days=1)
    end = start + pd.offsets.MonthEnd(months_ahead)   # start is the 1st, so this is the end of the Nth month
    future = pd.date_range(start, end, freq="D")
    predicted = pd.Series(model_fn(train, future), index=future)
    return _monthly(predicted), predicted


def _backtest(daily):
    months = _monthly(daily).index
    results = {name: {"ape": {h: [] for h in range(1, HORIZON_MONTHS + 1)}, "daily_abs_err": []} for name in MODELS}

    for n_train in range(MIN_TRAIN_MONTHS, len(months) - HORIZON_MONTHS + 1):
        cutoff = months[n_train - 1].to_timestamp(how="end").normalize()
        train = daily[daily.index <= cutoff]
        test = daily[(daily.index > cutoff) & (daily.index <= months[n_train + HORIZON_MONTHS - 1].to_timestamp(how="end"))]
        actual_monthly = _monthly(test)

        for name, fn in MODELS.items():
            predicted_monthly, predicted_daily = _forecast_monthly(fn, train, HORIZON_MONTHS)
            for h, month in enumerate(actual_monthly.index, start=1):
                actual = actual_monthly[month]
                results[name]["ape"][h].append(abs(predicted_monthly[month] - actual) / actual)
            results[name]["daily_abs_err"].extend(np.abs(predicted_daily.reindex(test.index).to_numpy() - test.to_numpy()))

    return results


# ---------------------------------------------------------------- public API

def forecast(daily_total):
    """
    daily_total: Series of total cost per day, indexed by date, ending on a month-end date.
    Returns {"forecasts": [{"month", "cost", "confidence"}], "model": str, "metrics": {...}}.
    """
    daily = daily_total.sort_index().asfreq("D").interpolate()
    n_months = len(_monthly(daily))

    if n_months < MIN_TRAIN_MONTHS + HORIZON_MONTHS:
        # Not enough history to backtest: use the simple model and say so.
        chosen = "seasonal_naive"
        confidence = {h: 0.5 for h in range(1, HORIZON_MONTHS + 1)}
        metrics = {"note": f"Only {n_months} months of data; need {MIN_TRAIN_MONTHS + HORIZON_MONTHS} to backtest."}
    else:
        bt = _backtest(daily)
        summary = {}
        for name, r in bt.items():
            by_h = {h: float(np.mean(r["ape"][h])) for h in r["ape"]}
            summary[name] = {
                "monthly_mape_by_horizon": {f"{h}_month": round(v, 4) for h, v in by_h.items()},
                "monthly_mape_mean": round(float(np.mean(list(by_h.values()))), 4),
                "daily_mae": round(float(np.mean(r["daily_abs_err"])), 2),
            }
        chosen = min(summary, key=lambda n: summary[n]["monthly_mape_mean"])
        confidence = {h: max(0.0, 1 - float(np.mean(bt[chosen]["ape"][h]))) for h in range(1, HORIZON_MONTHS + 1)}
        metrics = {
            "backtest_origins": len(bt[chosen]["ape"][1]),
            "models": summary,
            "selected": chosen,
            "confidence_definition": "1 - backtest monthly MAPE at that horizon",
        }

    predicted_monthly, _ = _forecast_monthly(MODELS[chosen], daily, HORIZON_MONTHS)
    forecasts = [
        {"month": str(period), "cost": round(float(cost), 2), "confidence": round(confidence[h], 2)}
        for h, (period, cost) in enumerate(predicted_monthly.items(), start=1)
    ]
    return {"forecasts": forecasts, "model": chosen, "metrics": metrics}
