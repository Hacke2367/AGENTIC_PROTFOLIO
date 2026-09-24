# agent_protfolio

Portfolio site: resume on the front page, per-project AI chat agent for recruiters. Full
project shape lives in `docs/project_context.md` — read that first, not this file.

## Where things are
- `docs/project_context.md` — WHAT and WHY (source of truth for scope, red lines).
- `docs/resume.md` — resume content (transcribed from the owner's PDF).
- `docs/projects/0N_*.md` — one deep-dive per showcased project; this is the chat agent's
  knowledge base.
- `docs/projects/projects_summary.md` — short cross-project overview + open questions.
- `docs/development_plan.md`, `docs/pending_work.md` — current plan and open items.
- `knowledge/` — the agent-facing context actually loaded at runtime (built from
  `docs/projects/`).
- `app/` — FastAPI app: `main.py` (routes), `agent.py` (routing/context-switch/OpenAI call),
  `templates/` (HTMX + Jinja2), `static/` (CSS, no custom JS).

## Stack
FastAPI + Jinja2 + HTMX (no hand-written JS) + OpenAI. Light theme, one load animation, CSS
only. Target host: Vercel (Python runtime).

## Rules
- No custom JavaScript — HTMX attributes only. If something seems to need JS, say so and ask.
- Never commit `.env` or any API key. `.env.example` documents required vars only.
- The chat agent never invents facts outside `knowledge/`; never gives legal advice for the
  AI Lawyer project; never commits the owner to salary/availability.
- See `docs/project_context.md` → Red lines for the full list.

## Skills
- Workflow (spec, plan, start_work, gate, ship, handoff, review): devsystem only.
- `mattpocock-skills` is enabled for this project only. Use just `prototype`, `tdd`,
  `diagnosing-bugs`, `grill-me`, always by full name (`/mattpocock-skills:prototype`).
  Never its `to-spec`, `implement`, `handoff` or `code-review`, which clash with devsystem.
