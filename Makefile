.PHONY: setup import-resume init-db dev test build start stop clean
setup: ; ./scripts/setup.sh
import-resume: ; backend/.venv/bin/python backend/scripts/import_resume.py
init-db: ; backend/.venv/bin/python backend/scripts/init_database.py
dev: ; ./scripts/dev.sh
test: ; backend/.venv/bin/python -m pytest backend/tests && cd frontend && npm test
build: ; ./scripts/build.sh
start: ; ./scripts/start.sh
stop: ; ./scripts/stop.sh
clean: ; find backend -type d -name __pycache__ -prune -exec rm -rf {} +; rm -rf frontend/dist
