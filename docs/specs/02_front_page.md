# Spec: Front Page
**Version:** 1.0.0 | **Component:** front page (`app/templates/`, `app/static/`, `app/main.py`)
**Status:** Ready for Review

## 1. Problem Statement
Today `/` is a bare list of project names with a chat button. A recruiter sees no resume, no
proof of what each project achieved, and nothing that shows craft, so the step 01 agent sits
behind a page that does not earn a second look. The owner targets AI/ML, GenAI/agent and
full-stack + AI roles (`docs/project_context.md`), so the page must read as a resume, prove
each project with numbers, and make the per-project agents the centrepiece.

## 2. Objective
One light-theme page that a recruiter can skim in under a minute and question in depth: the
full resume, five project rows with proof, instant slash-command answers, and a docked agent
console. It uses the look of the polished prototype variant D, on desktop and mobile.

## 3. Scope & Constraints

**Will Do:**
- **Command bar** (sticky): monogram + name, and `/projects`, `/why-hire-me`, `/about`,
  `/contact`, `/resume`, `/feedback`. Each jumps to its section; `/resume` downloads the PDF and
  is visually emphasised.
- **Hero:** name, role line, a one-line cue on how to use the agents, two CTAs ("See the
  projects", "Download resume (PDF)"), and six flags. Clicking or tapping a flag reveals its
  one-line proof, one at a time.
- **`/projects`:** the five projects in fixed order (AutoShorts, Project DMC, DOT_TO_IMAGE,
  AI Cartoon, AI Lawyer: Legal Flight Simulator). Each row has an image slot, name, status,
  pitch, three stats, stack, a "Talk to this project" button and four command buttons.
- **Slash commands**, per project: `/usp`, `/pipeline`, `/hardest-problem`, `/philosophy`.
  - Answers are pre-written, owner-approved text. They appear instantly in the console, make no
    OpenAI call, and don't count toward the visitor's chat limit.
  - `/pipeline` renders as a step flow; steps that are planned but not built are marked.
  - The same commands work when typed into the chat, for the active project. `/help` and any
    unknown `/command` get a short reply listing the four commands.
- **Agent console:** docked on the right on desktop, a bottom sheet on mobile. It holds:
  - a header ("Talk to a project", "5 agents online");
  - the **agent map**: you → router → five project nodes;
  - the step 01 chat panel, plus the four command buttons for the active project.
- **Agent map behaviour:**
  - It marks the active project, which changes on "Talk to this project", on a command, on a
    node click, and on a free-chat switch made by 01's router.
  - Hovering a project row highlights that project's line.
  - The active node pings once when it changes.
- **`/why-hire-me`:** the owner's message, a serious paragraph plus one "less serious" line.
  Claude's draft ships until the owner rewrites it.
- **`/about`:** profile, skills, experience (Nullclass internship), education and the three
  certifications, all from `docs/resume.md`.
- **`/contact`:** email (mailto), "Based in Mumbai, India", and the resume download.
- **`/feedback`:** a form with message (required, 500 characters max), name (optional) and
  company (optional).
  - A note on the form says only Abhishek reads it.
  - Submissions are stored privately; the visitor sees a thank-you in place of the form.
- **Theme and layout:** light theme, one load animation (the agent map draws in), and a
  responsive layout from 320 px up.
- **Footer:** © line plus "Built with FastAPI, HTMX and OpenAI. No custom JavaScript."

**Will NOT Do:**
- Project images, GIFs or video. The slots show an empty title card until the owner supplies
  media, which is a separate change.
- A headshot, or GitHub/LinkedIn links. Links are added when the URLs arrive; email only until
  then.
- Anything public or admin-side for feedback: no public display, no email notification, no
  admin page. The owner reads feedback in the Upstash console.
- A dark theme, a command palette or keyboard shortcuts, or looping/ambient animation. The
  agent map replaced the floating-widget idea.
- The "at least one successful startup" flag (dropped by the owner).
- Any change to 01's answers, knowledge or caps, beyond typed commands and map sync.
- Blog, CMS, analytics or cookies.

**Hard Rules:**
- **No custom JavaScript.** HTMX attributes and CSS only (`CLAUDE.md`).
- **No invented facts.** Every fact on the page comes from `docs/resume.md`, `knowledge/`, or
  text the owner wrote or approved. The 20 command answers, the six flags with their proofs,
  and the `/why-hire-me` text are owner-approved before merge.
- **Command answers follow 01's red lines.** No legal advice in any AI Lawyer answer; nothing
  about leaked keys, API credits or the owner's open questions; no commitments on salary or
  availability.
- **No phone number in the page HTML.** The resume PDF, which the owner approved with the
  number, is the only place it appears.
- **01's chat contract holds.** The `#chat`, `#chat-log`, `#chat-state`, `#chat-input` and
  `#chat-title` IDs and the `hx-*` flow stay, and 01's offline tests keep passing.
- **The caps hold.** Commands and feedback never call OpenAI. Feedback has its own per-visitor
  limit.
- **Accessibility.** WCAG AA text contrast, keyboard operable with visible focus, and no motion
  under `prefers-reduced-motion: reduce`.
- **Prototype code does not ship.** That means `?variant=`, `/prototype/*`,
  `app/prototype_front_page.py` and `app/templates/prototype_front_page/`. It is captured on a
  `spike/` branch before the build.

## 4. Core Design

**Page structure** (the reference is the polished prototype variant D, `?variant=d`):
```
DESKTOP (>= 1024 px)
+------------------------------------------------------------------------------+
| [AM] name   /projects /why-hire-me /about /contact [/resume] /feedback       |
+----------------------------------------------+-------------------------------+
| Abhishek Maurya                              | Talk to a project  * online   |
| role line                                    | you -- router --< 5 nodes     |
| cue with /pipeline                           |-------------------------------|
| [See the projects] [Download resume (PDF)]   | <active project>              |
| --flag --flag --flag                         | chat log (step 01)            |
| --flag --flag --flag                         |                               |
|                                              | [/usp /pipeline /hardest ...] |
| /projects                                    | [Ask about this project][Send]|
| [slot] name ........................ status  | (sticky, full height)         |
|        pitch, 3 stats, stack                 |                               |
|        [Talk to this project] [4 commands]   |                               |
|        ... x5                                |                               |
| /why-hire-me, /about, /contact, /feedback    |                               |
| footer                                       |                               |
+----------------------------------------------+-------------------------------+
MOBILE (< 1024 px): one column; the command bar scrolls sideways; the console is a bottom
sheet with a 64 px peek bar that opens on any project action and has a Close control.
```

**Design tokens (variant D):**

| Token | Value | Use |
|---|---|---|
| Paper | `#F6F7FA` | page background, faint dot-grid texture in the hero |
| Surface | `#FFFFFF` | console, slots, controls |
| Ink | `#0C1631` | text |
| Slate / Faint | `#505A6E` / `#667085` | secondary / tertiary text (both AA) |
| Accent | `#2F5BFF` (text/hover `#2447E0`) | active agent, primary buttons, links |
| Rules | `#E2E6EE` / `#C7CEDB` | dividers, borders |
| Status | `#0E7A4C` working, `#955700` in progress | status labels |

- **Typography:** Geist for all text, and Geist Mono only for things you can run: commands,
  flags and agent names.
- **Radius scale:** 20 (console), 14 (slots), 10 (buttons), 999 (flags).
- **Motion:** one load moment (the map draws). Every other motion answers an action: the ping,
  and the sheet slide.

**Content sources:**

| Section | Source | Approval |
|---|---|---|
| Name, role, profile, skills, experience, education, certifications, email | `docs/resume.md` | as transcribed |
| Project pitch, stats, stack, status | `knowledge/0N_*.md` | fact-checked against knowledge |
| Flags + proofs, 20 command answers, `/why-hire-me` | drafts in `app/prototype_front_page.py` | owner approves before merge |
| Resume PDF | owner's PDF, phone number included | owner-approved; compressed to ≤ 1 MB |

**Flows:**
```
"Talk to this project" / node click  -> console shows that project's chat (01) -> map marks it
command button                       -> console shows project + "/cmd" + static answer
                                        (no OpenAI call, no cap) -> map marks it
typed "/usp" in chat                 -> same static answer for the active project, no OpenAI call
typed "/help" or "/unknown"          -> help reply listing the four commands, no OpenAI call
free-chat message naming project M   -> 01 switch notice + answer -> map moves to M
feedback submit                      -> validate -> per-visitor limit -> store -> thank-you
```

**Endpoints (conceptual):**
- The page (`/`).
- Open a project's chat, optionally with a command. This extends 01's open endpoint.
- The chat endpoint (01's), which also recognises typed commands.
- A feedback endpoint.
- The resume PDF as a static file.

Mechanisms (where the answers live, how the map learns about a switch, the feedback storage
shape) are `/plan`'s call.

## 5. Edge Cases & Error Handling

| Case | Behaviour |
|---|---|
| OpenAI down, or a chat cap reached | 01's notices apply. Commands still answer, because they are static. |
| AI Lawyer `/pipeline` | Built steps plus planned steps, visibly marked "planned, not built yet". |
| Typed command with different case or spaces (`  /USP `) | Treated as `/usp`. |
| Typed `/something-else` | Help reply listing `/usp`, `/pipeline`, `/hardest-problem`, `/philosophy`. No OpenAI call. |
| Feedback message empty | Not sent. |
| Feedback message over 500 characters | Rejected with "Please keep it under 500 characters." Not stored. |
| Hidden bot-trap field filled | Thank-you shown, nothing stored. |
| Same visitor over the feedback limit (default 3 per day) | "Thanks, you've already sent feedback today." Not stored. |
| Feedback store fails | "Couldn't save your feedback right now. You can email abhishekmlen25@gmail.com." Logged server-side. |
| Web fonts fail to load | System font fallback; layout intact. |
| 320 px wide screen | No horizontal page scroll; the command bar scrolls sideways; long names wrap. |
| `prefers-reduced-motion: reduce` | No map draw, no ping, no sheet slide, no smooth scroll. |
| JavaScript disabled | All static content is readable and anchor links work. Chat and commands need HTMX. |
| Deep link to `#section` | Lands below the sticky bar, not under it. |

## 6. Acceptance Criteria
1. `/` renders, in order: command bar, hero, `/projects`, `/why-hire-me`, `/about`, `/contact`,
   `/feedback`, footer. Each bar item jumps to its section, and `/resume` downloads the PDF.
2. The hero shows name, role line, cue, both CTAs and six flags. Clicking a flag shows its proof,
   and opening another closes the first.
3. The five project rows appear in the fixed order, each with image slot, name, status, pitch,
   three stats, stack, "Talk to this project" and four command buttons. Every number matches
   `knowledge/` (checked against the plan's fact table).
4. "Talk to this project" opens that project's chat in the console, and the map marks that
   project active.
5. Each of the 20 command buttons shows its approved answer in the console, with the OpenAI
   client mocked to raise: there is no OpenAI call and no change to the visitor's chat count.
6. Typing each of the four commands in the chat returns the same answer for the active project,
   with no OpenAI call. `/help` and `/nope` return the help reply.
7. `/pipeline` renders an ordered step flow, and AI Lawyer's planned steps are marked as
   planned.
8. A free-chat message that switches project (01 AC3) also moves the map's active node to the
   new project.
9. On desktop, hovering a project row highlights that project's line in the map.
10. The map drawing is the only animation on load. With `prefers-reduced-motion: reduce`,
    nothing animates.
11. At 1440, 1024, 768, 390 and 320 px there is no horizontal page scroll. Below 1024 px the
    console is a bottom sheet that opens on any project action and closes with Close.
12. Feedback:
    - A valid message shows the thank-you, and the record is readable in the store.
    - An empty message is not sent.
    - A message of 501+ characters is rejected.
    - A filled bot trap stores nothing.
    - A visitor's 4th submission in a day gets the limit message and stores nothing.
13. The page HTML contains the email and no phone number. The resume PDF returns 200 and is
    ≤ 1 MB.
14. The only script tag is the pinned HTMX one with SRI (01 AC17 still holds).
15. Every text/background pair meets WCAG AA (4.5:1, or 3:1 for large text). Every control is
    reachable by keyboard with visible focus.
16. The merged branch has no `?variant=` handling, no `/prototype/*` routes, no
    `app/prototype_front_page.py` and no `app/templates/prototype_front_page/`.
17. 01's offline tests pass, and the chat IDs and `hx-*` flow are unchanged.
18. The PR records the owner's approval of the 20 command answers, the six flags with their
    proofs, and the `/why-hire-me` text (or the owner's replacements).

## 7. UI/UX Behavior
- The look is prototype variant D as polished on 2026-09-26. The owner will send design tweaks
  later; they amend this section and the tokens in §4. They don't change the acceptance
  criteria unless they say so.
- Buttons keep one name through the flow. "Talk to this project" opens the console titled
  "Talk to a project", and a command's label is echoed as the user's message (`/usp`).
- The empty image slot is a quiet title card: a dot-grid surface with the project's short name.
  It must not look broken.
- The flags use proofs from `app/prototype_front_page.py` → `FLAGS`: `--always-building`,
  `--claude-code-power-user`, `--cost-obsessed`, `--measure-before-trust`, `--1000+-tests`,
  `--hinglish-first`.

## 8. Dependencies
- Step 01 (merged): the chat endpoints, router, caps, and Upstash store.
- Fonts: Geist and Geist Mono from Google Fonts. CSP limits only `script-src`, so no change is
  needed.
- The owner's resume PDF, 4.2 MB, compressed to ≤ 1 MB for the site. Source:
  `C:\Users\abhishek maurya\OneDrive\Desktop\Documents\abhishek_resume_pdf.pdf`.
- Later, from the owner: project media, the GitHub/LinkedIn URLs, a rewrite of
  `/why-hire-me`, and the design tweaks.

## 9. Owner decisions (2026-09-26)
- Two-pane layout (prototype round 1, B); variant D chosen over E (round 2), then polished.
- Email only on the page, with `/resume` serving the PDF including the phone number.
- Sections: standard resume plus certifications, and `/why-hire-me` and `/feedback`.
- Proof-backed flags; the startup flag dropped.
- Slash commands `/usp`, `/pipeline`, `/hardest-problem`, `/philosophy`, answered statically.
- The agent map instead of a floating emoji widget, keeping one load animation.
- Image slots stay empty for now. The `/why-hire-me` draft is by Claude, rewritten later by the
  owner.
- `frontend-design` adopted as the project's design skill (`docs/tooling.md` P-002).

## 10. Defaults assumed (owner can override)
- The feedback limit is 3 per visitor per day. Feedback is kept until the owner deletes it.
- The "5 agents online" label is static. When the daily cap is hit, the chat's own notice
  explains it, and commands still work.
- Flags open on click or tap, not on hover. Hover-only would fail on touch screens.

## 11. Performance Targets
- A command answer appears in under 300 ms on localhost; there is no model call.
- The page's HTML + CSS stays under 100 KB uncompressed, excluding fonts and the PDF.
- No layout shift when the console loads its first panel: the space is reserved.
