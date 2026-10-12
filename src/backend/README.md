# Backend

FastAPI + PostgreSQL backend for CloudWiseAI.

## Setup

```bash
createdb cloudwise
cd src/backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                                  # then edit DATABASE_URL and JWT_SECRET

python ../../dataset/generate_dataset.py              # skip if the CSV already exists
python scripts/load_dataset.py                        # creates tables and loads cost_records
python scripts/run_analysis.py                        # anomalies, recommendations, forecast -> database
```

Re-run `run_analysis.py` whenever `cost_records` changes. It also writes accuracy metrics to `results/`.

## Run

```bash
cd src/backend
uvicorn app.main:app --reload --port 8000
```

- API: http://localhost:8000/api
- Interactive docs: http://localhost:8000/docs
- Frontend: set `VITE_API_URL=http://localhost:8000/api` in `src/frontend/.env`

## Endpoints

All routes except signup, login and health need `Authorization: Bearer <token>`.

| method | path | notes |
|---|---|---|
| POST | /api/auth/signup | `{username, email, password}` -> `{user, token}` |
| POST | /api/auth/login | `{email, password}` -> `{user, token}` |
| GET | /api/auth/me | current user |
| GET | /api/costs/summary | KPI cards. Forecast = next month from the `forecasts` table |
| GET | /api/costs/trend?days=14 | daily total spend, oldest first |
| GET | /api/costs/breakdown | current-month spend by service (top 5 + Other) |
| GET | /api/utilization | CPU for EC2/RDS plus unattached EBS volumes, problems first |
| GET | /api/anomalies | detected events, newest first (costs are per-day averages) |
| GET | /api/recommendations | open recommendations, biggest saving first |
| GET | /api/predictions | last 6 complete months + 3-month forecast |
| GET | /api/health | liveness check |

"Current month" means the billing period of the newest row in `cost_records`, so it works with a dataset that ends before today.

Cost data is shared by all users: it represents one AWS account. Per-user accounts would need an `account_id` on `cost_records`.

## Layout

```
app/
  main.py          app, CORS, router registration
  config.py        env vars
  database.py      Postgres connection pool
  security.py      password hashing, JWT, get_current_user
  schemas.py       request models
  routers/            auth, costs, utilization, anomalies, recommendations, predictions
  services/           anomalies.py, recommendations.py, forecasting.py (pure functions, no DB access)
db/schema.sql        users, cost_records, anomalies, recommendations, forecasts
scripts/load_dataset.py   CSV -> cost_records
scripts/run_analysis.py   runs the three services and stores their results
```

## How the analysis works

- **Anomalies** (`services/anomalies.py`): each resource-day is compared with the median of the same weekday over the previous 8 weeks (robust z-score, MAD-based). Flagged days are merged into events. Severity depends on dollars above baseline as a share of monthly spend.
- **Recommendations** (`services/recommendations.py`): six rules over the last 30 days. Every savings assumption (50% for right-sizing, 25% Savings Plan, 30% RDS RI, 40% S3 tiering) is listed at the top of the file.
- **Forecast** (`services/forecasting.py`): naive, ridge regression and ridge + XGBoost are compared by rolling-origin backtest, and the best one forecasts the next 3 months. Detected spikes are removed from the training history first.

## Status

- [x] Schema, dataset loader
- [x] Auth
- [x] Costs, utilization, anomalies, recommendations, predictions endpoints
- [x] Anomaly detection, recommendation rules, forecasting
- [ ] /assistant/chat
- [ ] AWS deployment
