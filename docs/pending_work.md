# Pending Work

Last updated: 2026-09-26 (handoff: step 02 built, draft PR #3)

## WIP
- `feature/front-page` (base `dev` @ 837c5ec, 2026-09-26): the front page. Built, pushed, draft
  PR #3 (https://github.com/Hacke2367/AGENTIC_PROTFOLIO/pull/3). The UI prototype is kept on
  `spike/front-page-prototype` @ 10c42cc (pushed; never merge it).

## Current focus
Step 02 (front page), status `Blocked`: built and verified, waiting on the owner.
- Built: `app/content.py` (all copy and the 20 command answers), static slash commands, the
  agent map, the mobile bottom sheet, private `/feedback`, the variant D theme, and the resume
  PDF (4.2 MB → 359 KB).
- Verified: gate 55/55 offline; 20/20 browser checks in headless Chrome, plus row hover and a
  Tab walk over 57 controls.
- Owner decisions for this step are in `docs/specs/02_front_page.md` §9.

## Next up
1. **Resume point.** Step 02 is `Blocked` on the owner, with draft PR #3 open. The owner:
   - (a) sends design tweaks, which amend spec §7 and the CSS;
   - (b) approves or edits `app/content.py`: `COMMANDS` (20), `FLAGS` (6), `WHY_HIRE` (AC18);
   - (c) says whether the GitHub/LinkedIn URLs go on `/contact`.

   Then apply the changes, re-run the gate, tick AC18 in the PR, and `/ship` (mark it ready).
   Read first: `docs/specs/02_front_page_impl.md` §11, PR #3's checklist, and
   `app/content.py`. Run it locally: `./venv/Scripts/python.exe -m uvicorn app.main:app --port 8765`.
2. Step 03 (deploy): see `docs/development_plan.md`. It is blocked on revoking the AutoShorts
   leaked key (see Open items).

## Done
- 2026-09-26: `feature/chat-agent` merged into `dev` (PR #2). Per-project recruiter chat agent:
  curated `knowledge/`, deterministic routing and context switch, caps, signed state, red-line
  replies.
- 2026-09-25: `chore/scaffold` merged into `dev` (PR #1). Docs, tracking files, and the
  FastAPI + HTMX skeleton.

## Open items
- [ ] **Owner: revoke/rotate the OpenAI key pasted in chat on 2026-09-26** after testing, and put
      the new key in `.env` only.
- [ ] GitHub and LinkedIn URLs, found in the resume PDF's links: `github.com/Hacke2367` and
      `linkedin.com/in/abhishek-maurya-148542292`. The owner confirms before they go on `/contact`.
- [ ] Resolve the open questions in `docs/projects/projects_summary.md`: repo visibility, hero
      demos, public project names, and how to frame the AI-assisted work.
- [ ] Revoke or rotate the leaked key described in `docs/projects/01_manim_code_video_template.md`
      before linking that repo publicly. **This now blocks deploy (step 03):** the resume PDF
      served at `/resume` links `github.com/Hacke2367/Auto_shorts_engine_1`.
- [ ] FYI for the owner: the resume PDF has two typos ("synchronizatio", and "API ra te limits
      securely.search" in the AutoShorts bullets). Fix them in the source and re-export if wanted.
