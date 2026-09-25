# Pending Work

Last updated: 2026-09-26 (merge of PR #2)

## WIP
- None. `feature/chat-agent` merged into `dev` (PR #2).

## Current focus
Step 02 (front page) is next. Step 01 (chat agent) is Done: 13/13 offline tests and 11/11
non-QA live tests pass.

## Next up
1. **Resume point.** Step 02 (front page): `/start_work` (branch `feature/front-page` off `dev`),
   then `/spec` (resume sections, project cards, light theme, one load animation). During the
   spec, run `/mattpocock-skills:prototype` with the frontend-design skill for 2-3 UI directions.
   Then `/plan`, then build.
   Read first: `docs/development_plan.md` (step 02 row), `docs/resume.md`, `knowledge/`, and
   `app/templates/` (keep the `#chat`, `#chat-log`, `#chat-state`, `#chat-input` and
   `#chat-title` IDs and the `hx-*` attributes).
   Needs from the owner: the GitHub and LinkedIn URLs (contact can ship with email only).
2. Step 03 (deploy): see `docs/development_plan.md`.

## Done
- 2026-09-26: `feature/chat-agent` merged into `dev` (PR #2). Per-project recruiter chat agent:
  curated `knowledge/`, deterministic routing and context switch, caps, signed state, red-line
  replies.
- 2026-09-25: `chore/scaffold` merged into `dev` (PR #1). Docs, tracking files, and the
  FastAPI + HTMX skeleton.

## Open items
- [ ] **Owner: revoke/rotate the OpenAI key pasted in chat on 2026-09-26** after testing, and put
      the new key in `.env` only.
- [ ] Get the GitHub and LinkedIn URLs from the owner (resume contact links).
- [ ] Resolve the open questions in `docs/projects/projects_summary.md`: repo visibility, hero
      demos, public project names, and how to frame the AI-assisted work.
- [ ] Revoke or rotate the leaked key described in `docs/projects/01_manim_code_video_template.md`
      before linking that repo publicly.
