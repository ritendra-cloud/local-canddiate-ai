#!/bin/zsh
set -euo pipefail
pidfile=logs/backend.pid; [[ -f $pidfile ]] || { print 'No backend PID file.'; exit 0; }; pid=$(<$pidfile)
command=$(ps -p $pid -o command= 2>/dev/null || true)
[[ "$command" == *'backend/.venv/bin/uvicorn app.main:app'* ]] || { rm -f $pidfile; print 'Removed stale PID file.'; exit 0; }
kill $pid; rm -f $pidfile
for _ in {1..20}; do
  kill -0 $pid 2>/dev/null || { print 'Backend stopped.'; exit 0; }
  [[ "$(ps -p $pid -o stat= 2>/dev/null || true)" == Z* ]] && { print 'Backend stopped.'; exit 0; }
  sleep 0.1
done
print -u2 'Backend did not stop after SIGTERM.'
exit 1
