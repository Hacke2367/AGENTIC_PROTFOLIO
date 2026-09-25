# Pending Work

## WIP
- `feature/chat-agent` (base `dev` @ a9952d5, 2026-09-25): the per-project chat agent.

## Current focus
Chat agent: spec approved, and the plan `docs/specs/01_chat_agent_impl.md` is written and waiting for the owner's yes before build.

## Next up
1. Owner reviews `docs/specs/01_chat_agent_impl.md`. On a yes, build per its §11 checklist.
   Needs `OPENAI_API_KEY` in a local `.env` for the live tests.
2. Steps 02 (front page) and 03 (deploy): see `docs/development_plan.md`.

## Done
- 2026-09-25: `chore/scaffold` merged into `dev` (PR #1). Docs, tracking files, and the
  FastAPI + HTMX skeleton.

## Open items
- [ ] Get the GitHub and LinkedIn URLs from the owner (resume contact links).
- [ ] Resolve the open questions in `docs/projects/projects_summary.md`: repo visibility, hero
      demos, public project names, and how to frame the AI-assisted work.
- [ ] Revoke or rotate the leaked key described in `docs/projects/01_manim_code_video_template.md`
      before linking that repo publicly.
