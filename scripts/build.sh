#!/bin/zsh
set -euo pipefail
backend/.venv/bin/python -m pytest backend/tests
(cd frontend && npm test && npm run build)
