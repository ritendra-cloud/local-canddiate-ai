#!/bin/zsh
set -euo pipefail
pidfile=logs/backend.pid
if [[ -f $pidfile ]] && kill -0 $(<$pidfile) 2>/dev/null; then print 'Backend already running.'; exit 1; fi
ollama list >/dev/null 2>&1 || { print 'Ollama unavailable. Start it with: ollama serve'; exit 1; }
ollama list | awk 'NR > 1 && $1 == "qwen2.5-coder:7b" { found=1 } END { exit !found }' || { print 'Configured model is missing.'; exit 1; }
[[ -f frontend/dist/index.html ]] || { print 'Frontend build missing. Run scripts/build.sh.'; exit 1; }
backend/.venv/bin/python backend/scripts/init_database.py
nohup backend/.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 >> logs/backend.log 2>&1 < /dev/null & print $! > $pidfile
for i in {1..20}; do curl -fsS http://127.0.0.1:8000/api/health >/dev/null 2>&1 && { open http://127.0.0.1:8000; exit 0; }; sleep .5; done; print 'Backend did not become ready.'; exit 1
