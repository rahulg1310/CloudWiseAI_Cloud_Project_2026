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
| POST | /api/assistant/chat | `{message, history?}` -> `{reply}`. Needs `LLM_API_KEY`, see below |
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
  routers/            auth, costs, utilization, anomalies, recommendations, predictions, assistant
  services/           anomalies.py, recommendations.py, forecasting.py, assistant.py (no DB access)
db/schema.sql        users, cost_records, anomalies, recommendations, forecasts
scripts/load_dataset.py   CSV -> cost_records
scripts/run_analysis.py   runs the three services and stores their results
```

## How the analysis works

- **Anomalies** (`services/anomalies.py`): each resource-day is compared with the median of the same weekday over the previous 8 weeks (robust z-score, MAD-based). Flagged days are merged into events. Severity depends on dollars above baseline as a share of monthly spend.
- **Recommendations** (`services/recommendations.py`): six rules over the last 30 days. Every savings assumption (50% for right-sizing, 25% Savings Plan, 30% RDS RI, 40% S3 tiering) is listed at the top of the file.
- **Forecast** (`services/forecasting.py`): naive, ridge regression and ridge + XGBoost are compared by rolling-origin backtest, and the best one forecasts the next 3 months. Detected spikes are removed from the training history first.

## AI assistant

`POST /api/assistant/chat` answers questions about the user's costs ("why did my spend change?", "what should I cut first?").

**Setup with Ollama (local and free, no API key).**

```bash
# install Ollama from https://ollama.com, then download a model once (roughly 5 GB)
ollama pull llama3.1:8b
```

Add to `src/backend/.env` and restart the server (keep Ollama running):

```
LLM_PROVIDER=ollama
# LLM_MODEL=llama3.1:8b              # any model you have pulled
# LLM_BASE_URL=http://localhost:11434
# OLLAMA_NUM_CTX=8192                # context window; see below
```

**Other providers.** For Claude or OpenAI set `LLM_PROVIDER=anthropic` (or `openai`) and `LLM_API_KEY=your-key`. Without a key those two return a 503 telling you so. The rest of the app is unaffected either way.

**How it works.** No fine-tuning. On every question the backend reads the current summary, service breakdown, anomalies, recommendations, utilization problems and forecast from the database, formats them as a ~1,700 token text snapshot, and sends it to the LLM together with the question and the last 10 chat messages. The prompt tells the model to use only that snapshot, say so when the answer isn't in it, treat anomaly notes as "what" rather than "why", and reply in plain text.

**Things to know.**
- The snapshot (aggregated costs and resource IDs) is sent to the LLM provider. Don't point this at real billing data unless that is acceptable for your provider and your data.
- Hosted providers charge per message, so each user is limited to 15 messages per minute (in memory, per server process).
- If the assistant answers "The AI service didn't respond", the cause (wrong key, wrong model name, no quota) is in the server log, not in the browser. For Ollama the chat itself says what to fix: start Ollama, run `ollama pull <model>`, or wait for the model to load.
- **Ollama specifics.** The first question after startup is slow while the model loads into memory (the timeout is 120 s for Ollama). `OLLAMA_NUM_CTX` matters: Ollama's own default window is smaller than the data snapshot and it silently drops the overflow, so the backend asks for 8192 tokens and trims old chat history to fit. Small local models are weaker than Claude or GPT at arithmetic and at following the plain-text rule, so check their numbers against the dashboard.
- **Deployment.** Ollama must run on the same machine as the backend or be reachable at `LLM_BASE_URL`. A CPU-only EC2 instance will answer slowly; for the deployed demo consider a hosted provider and keep Ollama for local development.
- The assistant can only read data. It never changes anything in AWS.

## Status

- [x] Schema, dataset loader
- [x] Auth
- [x] Costs, utilization, anomalies, recommendations, predictions endpoints
- [x] Anomaly detection, recommendation rules, forecasting
- [x] /assistant/chat (AI assistant)
- [ ] AWS deployment
