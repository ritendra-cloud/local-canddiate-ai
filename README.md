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

## Phase 3A: structured local job matching

`POST /api/job-match` accepts a job description, optional title, optional existing session UUID, and `include_interview_questions`. It returns a validated analysis generated locally by Ollama, then finalized in Python. Ollama supplies only requirement observations; Python validates evidence, resolves profile facts, groups requirements, calculates the score, recommendation, timestamps, model label, and public UUID.

Candidate facts come only from `candidate.json`. Job-description text is delimited as untrusted data; instructions inside it cannot alter scores, recommendations, evidence, or reveal prompts. A MATCH or PARTIAL must include valid evidence references. Supported roots are `experience`, `skills`, `certifications`, `education`, `achievements`, and `publications_and_patents`; private attributes, `import_metadata`, traversal, filesystem-like paths, and invalid indexes are rejected.

Each accepted reference yields a UI-facing object such as `{"reference":"skills.tools[0].name","label":"Skill evidence","value":"Selenium"}`. The score is the weighted sum of MATCH=1, PARTIAL=.5, MISSING/UNCLEAR=0 divided by total importance weight: MUST_HAVE=3, PREFERRED=1.5, RESPONSIBILITY=1, UNCLEAR=.5. Recommendations are STRONG_INTERVIEW (80+), INTERVIEW (65+), CONSIDER (50+), or NOT_RECOMMENDED; more than half missing MUST_HAVE requirements cap the recommendation at CONSIDER. The **AI-generated profile-to-job alignment score** is an evidence-based comparison, not a hiring probability.

Python makes exactly one structured repair request after invalid model output. Failed analyses are not persisted. Safe errors use `{"error":{"code":"...","message":"...","retryable":true}}`. Saved analyses use `GET /api/job-analyses`, `GET /api/job-analyses/{analysis_id}`, `DELETE /api/job-analyses/{analysis_id}`, and `DELETE /api/job-analyses`; no internal database IDs, prompts, or raw model output are exposed.

Routine tests use temporary databases, fictional profiles, and mocked Ollama responses. For real local verification, start with `make start`, run the supplied local HTTP client with an extended timeout, then clean up its temporary analyses and run `make stop`. The real-model check is deliberately not part of `make test` or `make build`.
