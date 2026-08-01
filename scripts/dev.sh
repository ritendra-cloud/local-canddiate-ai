#!/bin/zsh
set -euo pipefail
backend/.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 & backend_pid=$!
(cd frontend && npm run dev) & frontend_pid=$!
trap 'kill $backend_pid $frontend_pid 2>/dev/null || true' INT TERM EXIT
wait
