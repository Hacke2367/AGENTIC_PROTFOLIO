# Pending Work

Last updated: 2026-09-26 (spec 02 ready for review)

## WIP
- `feature/front-page` (base `dev` @ 837c5ec, 2026-09-26): the front page. Uncommitted
  throwaway prototype (dev-only `?variant=` route, `/prototype/*` routes in `app/main.py`,
  `app/prototype_front_page.py`, `app/templates/prototype_front_page/`,
  `app/static/prototype_empty.html`); capture it on a `spike/` branch once a variant wins.

## Current focus
Step 02 (front page), stage `Spec`. The owner picked prototype variant D (`?variant=d`: Geist +
electric blue agent console) and wants it polished to a premium finish; `frontend-design` was
adopted for that (P-002). Round 1: the owner kept B's two-pane layout and rejected A and C;
round 2: D chosen over E (Satoshi + saffron). Polish pass done (the owner is reviewing it):
AA-contrast tokens (midnight ink #0C1631), hero CTAs, `/resume` emphasised in the bar,
title-card image slots, segmented command controls, the active agent pings on switch, favicon,
footer, tidier mobile.

Owner decisions so far (2026-09-26), to carry into `docs/specs/02_front_page.md`:
- The page shows email only, no phone. `/resume` serves the PDF, phone number included.
- Sections: profile, skills, experience, education, certifications, projects, contact, plus
  `/why-hire-me` and `/feedback` (feedback stored privately, never shown publicly).
- A premium light theme, built on B's layout: a sticky agent console with an agent map, and a
  bottom sheet on mobile.
- Six proof-backed tags (`--always-building` ...); the "successful startup" tag is dropped.
- Four static slash commands per project (`/usp`, `/pipeline`, `/hardest-problem`,
  `/philosophy`) plus site commands in a top bar.
- `/why-hire-me` text: Claude's draft for now; the owner rewrites it later.
- Image slots stay empty for now; GitHub/LinkedIn stay pending (email only).

## Next up
1. **Resume point.** `docs/specs/02_front_page.md` (v1.0.0) is ready for the owner's review.
   The owner will also send design tweaks for polished D (`?variant=d`); they amend spec §4/§7.
   On the owner's yes: capture the prototype on `spike/front-page-prototype`, then `/plan`
   → `docs/specs/02_front_page_impl.md`, then build. The owner approves it, then `/plan`,
   then build. Run the prototype: `./venv/Scripts/python.exe -m uvicorn app.main:app --port 8765`.
   Read first: `docs/development_plan.md` (step 02 row), `app/prototype_front_page.py` (all
   draft copy: tags, why-hire-me, the 20 command answers), and `app/templates/` (keep the
   `#chat`, `#chat-log`, `#chat-state`, `#chat-input` and `#chat-title` IDs and the `hx-*`
   attributes).
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
- [ ] Compress `app/static/resume.pdf` (4.2 MB) before it ships.
- [ ] Resolve the open questions in `docs/projects/projects_summary.md`: repo visibility, hero
      demos, public project names, and how to frame the AI-assisted work.
- [ ] Revoke or rotate the leaked key described in `docs/projects/01_manim_code_video_template.md`
      before linking that repo publicly.
