# Development Plan

Project roadmap for v1: live today (2026-09-25) per `docs/project_context.md`. One row per
step, run in order. `/start_work` picks the first row that is not `Done`, and `/ship` and
`/merge_pr` update the Status and PR columns.

Statuses: `Todo` → `Spec` → `Plan` → `Build` → `Review` → `Done`.

| # | Step | Branch | Status | Spec | PR |
|---|---|---|---|---|---|
| 00 | Scaffold: docs, tracking, FastAPI + HTMX skeleton | `chore/scaffold` | Done | n/a | #1 |
| 01 | Chat agent: knowledge curation, routing and context switch, caps, red lines | `feature/chat-agent` | Done | `specs/01_chat_agent.md` | #2 |
| 02 | Front page: resume sections, project cards, light theme, load animation | `feature/front-page` | Blocked | `specs/02_front_page.md` | #3 (draft) |
| 03 | Deploy: Vercel, env vars, OpenAI budget backstop, public URL | `chore/deploy` | Todo | | |

## Step details

**01: Chat agent.**
- Delivers: `knowledge/` files curated from `docs/projects/`, plus the chat endpoint and the
  agent behaviour in `specs/01_chat_agent.md`.
- Needs: owner approval of the spec.
- Done when: all 17 acceptance criteria pass.

**02: Front page.**
- Delivers: the resume (profile, skills, education, experience, contact), the 5 project
  cards with a "Talk to this project" trigger that opens the 01 chat panel, a light theme with
  one load animation, and a mobile layout.
- Needs: the 01 chat endpoint, the GitHub/LinkedIn URLs (the contact section can ship with
  email only), and the frontend-design pass (`prototype` for 2-3 directions).
- Done when: its spec's acceptance criteria pass.

**03: Deploy.**
- Delivers: the app live on a public Vercel URL with `OPENAI_API_KEY` in the host env and an
  OpenAI dashboard budget limit set.
- Needs: owner access to the Vercel and OpenAI dashboards.
- Done when: the public URL loads, a chat round-trips, and the key is absent from the page
  source.
