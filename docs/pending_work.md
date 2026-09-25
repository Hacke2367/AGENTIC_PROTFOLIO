# Pending Work

Last updated: 2026-09-26 (handoff after shipping step 01)

## WIP
- `feature/chat-agent` (base `dev` @ a9952d5, 2026-09-25): the per-project chat agent.

## Current focus
Chat agent build (`docs/specs/01_chat_agent_impl.md`). The code, knowledge files and offline
tests are done, and all 13 offline tests pass.
- First live run: 14/16 pass, median latency 2.6s, and the AC2 hand check is OK. The unknown-fact
  question was already covered by the knowledge, so it was replaced. The commitment reply
  paraphrased its phrase, so the prompt now asks for an exact sentence.
- Re-run on 2026-09-26: 11/11 non-QA live tests pass, and 13/13 offline tests pass.

## Next up
1. **Resume point.** Step 01 (chat agent) is in `Review`, with PR #2
   (https://github.com/Hacke2367/AGENTIC_PROTFOLIO/pull/2) open into `dev`. The build checklist
   is complete, the gate passes 13/13, and the live tests are green. **Waiting on the owner:**
   "PR 2 merge karo" → `/merge_pr 2`. Then `/start_work` picks step 02 (`feature/front-page`),
   then `/spec` (front page: resume sections, project cards, light theme, one load animation).
   During the spec, run `/mattpocock-skills:prototype` with the frontend-design skill for 2-3 UI
   directions. Then `/plan`, then build.
   Read first: `docs/development_plan.md` (step 02 row), `docs/resume.md`, `knowledge/`, and
   `app/templates/` (keep the `#chat`, `#chat-log`, `#chat-state`, `#chat-input` and
   `#chat-title` IDs and the `hx-*` attributes).
2. Step 03 (deploy): see `docs/development_plan.md`.

## Done
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
