# Local CandidateAI

Phase 1 is a fully local foundation: DOCX import, validated candidate JSON, local SQLite, Ollama status checks, FastAPI, and a React profile summary. No cloud model, deployment service, analytics, or remote assets are used.

## Architecture

`data/source/resume.docx → make import-resume → data/processed/candidate.json → FastAPI /api/profile → React summary`

Requires Python 3.11+, Node/npm, and local Ollama with `qwen2.5-coder:7b`. Place the resume at `data/source/resume.docx`, run `make setup`, then `make import-resume`; review the generated draft JSON before use. The SQLite database is `backend/app/db/candidate_ai.db`.

Use `make dev` for development, `make build` then `make start` for production-style local serving, and `make stop` to stop it. API endpoints: `/api/health`, `/api/profile`, `/api/config/public`.

Troubleshooting: start Ollama with `ollama serve`; manually install the required model if absent; ensure the DOCX exists and opens in Word; correct malformed `candidate.json`; run `make build` if the frontend is missing. Tests: `make test`.

## Phase 2: local candidate chat

Candidate Chat streams Server-Sent Events from the local Ollama `/api/chat` endpoint. Events are `session`, `token`, `complete`, and `error`, each with JSON data. The browser uses `AbortController` for Stop; interrupted assistant text is not stored, while the user message remains stored. SQLite stores local session titles and completed user/assistant messages only; the system prompt is never stored. Conversation history resolves references but candidate facts always come only from `candidate.json`. Session APIs are `GET /api/sessions`, `GET /api/sessions/{id}`, `DELETE /api/sessions/{id}`, and `DELETE /api/sessions`.

Routine `make test` uses temporary SQLite databases and mocked Ollama stream clients for chat service coverage; it never calls the model. Real local streaming is a manual verification step and uses only the configured Ollama endpoint. Browser disconnect behavior is best-effort through request-disconnect checks and AbortController; automated ASGI tests cannot precisely emulate every browser TCP disconnect.

## Planned local profile sync and resume tailoring

Phase 3 reserves `data/source/linkedin/` for manually exported LinkedIn files and `data/processed/linkedin_profile.json` for a future local review artifact. No LinkedIn scraping, browser automation, API use, or network synchronization is implemented. LinkedIn-only facts must be reviewed before they can affect the approved candidate profile. Future job-match gap classifications support evidence-backed resume opportunities only; they never modify `data/source/resume.docx`, automatically add missing skills, or generate a resume without explicit approval.
