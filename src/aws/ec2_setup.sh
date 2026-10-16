#!/usr/bin/env bash
#
# CloudWiseAI - one-shot backend setup for an EC2 instance (Amazon Linux 2023 or Ubuntu).
#
# What it does (safe to run again):
#   1. installs git, Python and a swap file
#   2. downloads the project to /opt/cloudwise
#   3. creates a virtualenv and installs src/backend/requirements.txt
#   4. writes src/backend/.env (DATABASE_URL, JWT_SECRET, CORS_ORIGINS, ...)
#   5. creates the database if needed, loads the dataset, runs the ML analysis
#   6. runs the API as a systemd service called "cloudwise" on port 8000
#
# First run:
#   sudo DB_HOST=<rds-endpoint> CORS_ORIGINS=http://localhost:5173 bash ec2_setup.sh
#   (it asks for the database password; or pass DB_PASSWORD=... instead)
#
# Later, e.g. to add the CloudFront URL to CORS (everything else is remembered from .env):
#   sudo CORS_ORIGINS=https://dxxxx.cloudfront.net,http://localhost:5173 SKIP_DATA=1 bash ec2_setup.sh
#
# Settings (environment variables):
#   DB_HOST        RDS endpoint (required on the first run)
#   DB_PASSWORD    RDS master password (asked for if missing)
#   DB_USER        default postgres
#   DB_NAME        default cloudwise (created if it does not exist)
#   DB_PORT        default 5432
#   DB_SSLMODE     default require (RDS supports SSL)
#   CORS_ORIGINS   comma separated list of frontend URLs allowed to call the API
#   JWT_SECRET     generated on the first run and kept in .env
#   LLM_PROVIDER / LLM_API_KEY / LLM_MODEL   assistant settings; with no key the assistant stays off
#   REPO_URL, BRANCH, APP_DIR, SERVICE_USER, PORT
#   SKIP_DATA=1    do not reload the dataset / rerun the analysis
#   SKIP_OS=1      skip package, swap and systemd steps (for testing outside a real server)

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/rahulg1310/CloudWiseAI_Cloud_Project_2026.git}"
BRANCH="${BRANCH:-main}"
APP_DIR="${APP_DIR:-/opt/cloudwise}"
SERVICE_USER="${SERVICE_USER:-cloudwise}"
PORT="${PORT:-8000}"
SKIP_DATA="${SKIP_DATA:-0}"
SKIP_OS="${SKIP_OS:-0}"

BACKEND_DIR="$APP_DIR/src/backend"
ENV_FILE="$BACKEND_DIR/.env"
VENV="$APP_DIR/venv"

say() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run this with sudo."

# ---------------------------------------------------------------- 1. packages
PYTHON=""
if [ "$SKIP_OS" != "1" ]; then
  say "Installing packages"
  if command -v dnf >/dev/null 2>&1; then
    dnf install -y git libgomp python3.12 python3.12-pip || dnf install -y git libgomp python3.11 python3.11-pip
  elif command -v apt-get >/dev/null 2>&1; then
    apt-get update -y
    DEBIAN_FRONTEND=noninteractive apt-get install -y git curl python3 python3-venv python3-pip libgomp1
  else
    die "Neither dnf nor apt-get found. Use Amazon Linux 2023 or Ubuntu."
  fi

  # pandas + scikit-learn + xgboost can run a 1 GB instance out of memory, so make sure there is swap
  if [ "$(swapon --show --noheadings | wc -l)" -eq 0 ]; then
    say "Creating a 2 GB swap file"
    dd if=/dev/zero of=/swapfile bs=1M count=2048 status=none
    chmod 600 /swapfile
    mkswap /swapfile >/dev/null
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  fi
fi

for candidate in python3.12 python3.11 python3; do
  if command -v "$candidate" >/dev/null 2>&1; then PYTHON="$candidate"; break; fi
done
[ -n "$PYTHON" ] || die "No Python 3 found."

# ---------------------------------------------------------------- 2. code
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  say "Creating user $SERVICE_USER"
  useradd --system --home-dir "$APP_DIR" --shell /sbin/nologin "$SERVICE_USER"
fi

if [ -d "$APP_DIR/.git" ]; then
  say "Updating code"
  # the folder is owned by $SERVICE_USER, so tell git that running it as root here is fine
  GIT="git -c safe.directory=$APP_DIR -C $APP_DIR"
  $GIT fetch --quiet origin "$BRANCH"
  # results/*.json are rewritten by run_analysis.py, so discard local edits instead of failing the pull
  $GIT reset --hard "origin/$BRANCH" --quiet
else
  say "Downloading code"
  mkdir -p "$APP_DIR"
  git clone --quiet --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi

# ---------------------------------------------------------------- 3. python deps
say "Installing Python packages (a few minutes the first time)"
[ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$BACKEND_DIR/requirements.txt"

# ---------------------------------------------------------------- 4. .env
if [ ! -f "$ENV_FILE" ] && [ -z "${DB_HOST:-}" ]; then
  die "First run: set DB_HOST to your RDS endpoint, e.g.  sudo DB_HOST=xxxx.rds.amazonaws.com bash ec2_setup.sh"
fi
say "Writing $ENV_FILE"
if [ -n "${DB_HOST:-}" ] && [ -z "${DB_PASSWORD:-}" ]; then
  read -rsp "Database password for ${DB_USER:-postgres}: " DB_PASSWORD
  echo
  export DB_PASSWORD
fi

# Python does the writing so special characters in the password are URL-encoded properly.
ENV_FILE="$ENV_FILE" "$VENV/bin/python" - <<'PY'
import os
import secrets
from urllib.parse import quote

path = os.environ["ENV_FILE"]
values = {}
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                values[key] = value

host = os.environ.get("DB_HOST")
if host:
    user = quote(os.environ.get("DB_USER", "postgres"), safe="")
    password = quote(os.environ["DB_PASSWORD"], safe="")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "cloudwise")
    sslmode = os.environ.get("DB_SSLMODE", "require")
    values["DATABASE_URL"] = f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode={sslmode}"

values.setdefault("JWT_SECRET", secrets.token_hex(32))
values.setdefault("CORS_ORIGINS", "http://localhost:5173")
values.setdefault("LLM_PROVIDER", "anthropic")  # with an empty LLM_API_KEY the assistant is switched off
values.setdefault("LLM_API_KEY", "")

for key in ("CORS_ORIGINS", "LLM_PROVIDER", "LLM_API_KEY", "LLM_MODEL"):
    if os.environ.get(key):
        values[key] = os.environ[key]
if os.environ.get("JWT_SECRET"):
    values["JWT_SECRET"] = os.environ["JWT_SECRET"]

with open(path, "w", encoding="utf-8") as f:
    for key, value in values.items():
        f.write(f"{key}={value}\n")
os.chmod(path, 0o600)
PY

# ---------------------------------------------------------------- 5. database + data
if [ "$SKIP_DATA" != "1" ]; then
  say "Making sure the database exists"
  ENV_FILE="$ENV_FILE" "$VENV/bin/python" - <<'PY'
import os
from urllib.parse import urlsplit, urlunsplit

import psycopg2
from psycopg2 import sql

values = {}
with open(os.environ["ENV_FILE"], encoding="utf-8") as f:
    for line in f:
        if "=" in line and not line.startswith("#"):
            key, _, value = line.rstrip("\n").partition("=")
            values[key] = value

url = urlsplit(values["DATABASE_URL"])
database = url.path.lstrip("/")
admin_url = urlunsplit(url._replace(path="/postgres"))

conn = psycopg2.connect(admin_url, connect_timeout=15)
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database,))
    if cur.fetchone():
        print(f"database {database} already exists")
    else:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        print(f"created database {database}")
conn.close()
PY

  chown -R "$SERVICE_USER" "$APP_DIR"

  say "Loading the dataset"
  (cd "$BACKEND_DIR" && runuser -u "$SERVICE_USER" -- "$VENV/bin/python" scripts/load_dataset.py)

  say "Running anomaly detection, recommendations and forecasting"
  (cd "$BACKEND_DIR" && runuser -u "$SERVICE_USER" -- "$VENV/bin/python" scripts/run_analysis.py)
fi

chown -R "$SERVICE_USER" "$APP_DIR"

# ---------------------------------------------------------------- 6. service
START_CMD="$VENV/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT"

if [ "$SKIP_OS" != "1" ] && [ -d /run/systemd/system ]; then
  say "Installing the systemd service"
  cat > /etc/systemd/system/cloudwise.service <<EOF
[Unit]
Description=CloudWiseAI FastAPI backend
After=network-online.target
Wants=network-online.target

[Service]
User=$SERVICE_USER
WorkingDirectory=$BACKEND_DIR
# One worker on purpose: the assistant's rate limiter lives in memory.
ExecStart=$START_CMD
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable cloudwise >/dev/null 2>&1
  systemctl restart cloudwise

  say "Waiting for the API"
  ok=0
  for _ in $(seq 1 30); do
    if curl -fsS "http://127.0.0.1:$PORT/api/health" >/dev/null 2>&1; then ok=1; break; fi
    sleep 1
  done
  if [ "$ok" -ne 1 ]; then
    journalctl -u cloudwise -n 40 --no-pager || true
    die "The API did not come up. The log above says why."
  fi
else
  say "Not starting a systemd service. Start the API by hand with:"
  echo "  cd $BACKEND_DIR && runuser -u $SERVICE_USER -- $START_CMD"
  exit 0
fi

# ---------------------------------------------------------------- done
TOKEN="$(curl -fsS -m 3 -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' 2>/dev/null || true)"
PUBLIC_DNS=""
if [ -n "$TOKEN" ]; then
  PUBLIC_DNS="$(curl -fsS -m 3 -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null || true)"
fi

say "Done. The API is running."
echo "  Health check : curl http://127.0.0.1:$PORT/api/health"
echo "  Logs         : sudo journalctl -u cloudwise -f"
if [ -n "$PUBLIC_DNS" ]; then
  echo "  API Gateway integration URL: http://$PUBLIC_DNS:$PORT/api/{proxy}"
fi
