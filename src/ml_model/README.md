# Machine Learning

The ML code is part of the backend so that the API and the analysis share one codebase:

| Task | Code |
|---|---|
| Anomaly detection (weekday-aware robust z-score) | `src/backend/app/services/anomalies.py` |
| Cost forecasting (seasonal-naive, ridge, ridge+XGBoost, rolling-origin backtest) | `src/backend/app/services/forecasting.py` |
| Cost-saving recommendations (six rule families) | `src/backend/app/services/recommendations.py` |
| Runner that writes results to PostgreSQL and `results/` | `src/backend/scripts/run_analysis.py` |

Run it with `python src/backend/scripts/run_analysis.py` after loading the dataset. Headline results are in `results/README.md`.
