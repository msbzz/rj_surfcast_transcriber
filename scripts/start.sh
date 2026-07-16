#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
. .venv/bin/activate
set -a; [ -f .env ] && . ./.env; set +a
exec uvicorn app:app --host 127.0.0.1 --port 9001 --workers 1
