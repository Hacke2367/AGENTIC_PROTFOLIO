# Pending Work

## WIP
- `feature/chat-agent` (base `dev` @ a9952d5, 2026-09-25): the per-project chat agent.

## Current focus
Chat agent build (`docs/specs/01_chat_agent_impl.md`). The code, knowledge files and offline
tests are done, and all 13 offline tests pass. Waiting on the live tests.

## Next up
1. Owner adds `.env` with `OPENAI_API_KEY`, then run `python -m pytest -m live -s` and hand-check
   the AC2 answers.
2. `/ship` step 01 (PR into `dev`).
3. Steps 02 (front page) and 03 (deploy): see `docs/development_plan.md`.

## Done
- 2026-09-25: `chore/scaffold` merged into `dev` (PR #1). Docs, tracking files, and the
  FastAPI + HTMX skeleton.

## Open items
- [ ] Get the GitHub and LinkedIn URLs from the owner (resume contact links).
- [ ] Resolve the open questions in `docs/projects/projects_summary.md`: repo visibility, hero
      demos, public project names, and how to frame the AI-assisted work.
- [ ] Revoke or rotate the leaked key described in `docs/projects/01_manim_code_video_template.md`
      before linking that repo publicly.
