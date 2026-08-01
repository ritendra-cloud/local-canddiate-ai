#!/bin/zsh
set -euo pipefail
source "${0:A:h}/resolve_python.sh"
print "Selected Python: $PYTHON_BIN ($($PYTHON_BIN --version))"
if [[ -f backend/.venv/pyvenv.cfg ]] && ! grep -q 'version = 3\.1[1-4]\.' backend/.venv/pyvenv.cfg; then
  print 'Replacing invalid backend/.venv only.'; rm -rf backend/.venv
fi
[[ -x backend/.venv/bin/python ]] || "$PYTHON_BIN" -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip setuptools wheel
backend/.venv/bin/pip install -r backend/requirements.txt
command -v node >/dev/null && command -v npm >/dev/null || { print -u2 'Node and npm are required.'; exit 1; }
(cd frontend && npm install)
command -v ollama >/dev/null || { print -u2 'Ollama is required.'; exit 1; }
ollama list >/dev/null 2>&1 || { print -u2 'Ollama unavailable. Start it with: ollama serve'; exit 1; }
ollama list | awk 'NR > 1 && $1 == "qwen2.5-coder:7b" { found=1 } END { exit !found }' || { print -u2 'Missing qwen2.5-coder:7b. Install it manually with: ollama pull qwen2.5-coder:7b'; exit 1; }
backend/.venv/bin/python backend/scripts/init_database.py
backend/.venv/bin/python -m pytest backend/tests
(cd frontend && npm test && npm run build)
print 'Setup complete. Next: make import-resume (after placing data/source/resume.docx), then make start.'
