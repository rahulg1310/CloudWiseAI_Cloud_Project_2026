# Backend

FastAPI + PostgreSQL backend for CloudWiseAI.

Responsibilities:

- Authentication
- REST APIs
- Dataset processing
- Database management
- AI model integration

## Database setup

```bash
createdb cloudwise
export DATABASE_URL=postgresql://user:password@localhost:5432/cloudwise

pip install -r src/backend/requirements.txt
python dataset/generate_dataset.py                 # skip if the CSV already exists
python src/backend/scripts/load_dataset.py         # creates tables and loads cost_records
```

`load_dataset.py` is safe to re-run; add `--reset` to wipe `cost_records` first.

## Layout

```
db/schema.sql            tables: users, cost_records, anomalies, recommendations
scripts/load_dataset.py  CSV -> cost_records
requirements.txt
```

## Status

- [x] Schema
- [x] Dataset loader
- [ ] FastAPI app: auth + /costs/summary, /costs/trend, /costs/breakdown
- [ ] /predictions, /anomalies, /recommendations, /utilization
- [ ] /assistant/chat
