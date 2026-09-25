# Implementation Plan: Front Page
**Spec:** `docs/specs/02_front_page.md` (v1.0.0, approved by the owner on 2026-09-26)
**Branch:** `feature/front-page` | **Step:** 02 in `docs/development_plan.md`
**Design reference:** prototype variant D on `spike/front-page-prototype` @ `10c42cc`
(`app/templates/prototype_front_page/console.html`, `app/prototype_front_page.py`)

## 1. Files

| Action | File | Reason |
|---|---|---|
| CREATE | `app/content.py` | All page copy and the 20 command answers, in one reviewable place (spec §4 content sources; hard rule: no invented facts) |
| CREATE | `app/feedback.py` | Private feedback store with a per-visitor daily limit (spec §3 `/feedback`, §5) |
| MODIFY | `app/limits.py` | `_memory_run` learns `LPUSH` / `LTRIM` so feedback works without Upstash in dev and tests. The caps don't change |
| MODIFY | `app/main.py` | Full page with the first console panel, `cmd` on `/chat/open`, typed/button commands in `/chat` before the caps, `POST /feedback`, `CONTACT_EMAIL` from `content` |
| MODIFY | `app/templates/index.html` | The full page, rebuilt from prototype variant D |
| MODIFY | `app/templates/chat_panel.html` | `data-active` on `#chat-title`, command buttons, an optional command exchange, the OOB sheet opener |
| MODIFY | `app/templates/message.html` | Command turns; `data-active` on the OOB `#chat-title` after a switch |
| MODIFY | `app/templates/_chat_fields.html` | Skip the input OOB for button commands (`keep_input`) |
| CREATE | `app/templates/_command.html` | One command exchange: the `/cmd` bubble plus an answer, pipeline flow or help |
| MODIFY | `app/static/styles.css` | The variant D theme. Existing chat selectors keep working |
| CREATE | `app/static/resume.pdf` | The owner's PDF, compressed to ≤ 1 MB (§5.6) |
| DELETE | `app/prototype_front_page.py`, `app/templates/prototype_front_page/`, `app/static/prototype_empty.html`, prototype edits in `app/main.py` | Prototype must not ship (AC16). Preserved on the spike branch |
| CREATE | `tests/conftest.py` | The fake OpenAI client, fixtures and helpers, moved from `test_offline.py` so both suites share them |
| MODIFY | `tests/test_offline.py` | Import the moved helpers. No behaviour change |
| CREATE | `tests/test_front_page.py` | Offline tests for spec 02 (§10) |
| MODIFY | `.env.example` | `FEEDBACK_DAILY_LIMIT` (optional, default 3) |
| MODIFY | `CLAUDE.md` | "Where things are": add `content.py` and `feedback.py` (one line) |

## 2. Architecture Decisions

| # | Decision | Derives from | Rejected alternative, and why |
|---|---|---|---|
| D1 | **Page copy and command answers live in `app/content.py`** as plain Python data | Hard rule: no invented facts; the owner approves the text in one place (AC18) | YAML or Markdown files: a parser or a new dependency. `knowledge/`: that is the LLM's context, and page copy there would bloat every prompt |
| D2 | **Slash commands are a server lookup that runs before the caps**, never the model | Spec §3: instant, no OpenAI call, no cap; AC5–6 | Sending `/usp` to the model: it costs money, is nondeterministic, and uses up the visitor's 20 messages |
| D3 | **Command exchanges are appended to the signed history** (bounded by `MAX_HISTORY` / `MAX_TURN_CHARS`) | Continuity: "why that choice?" after `/philosophy` needs context | Leaving them out: the model can't see what the recruiter just read |
| D4 | **Row buttons open a fresh panel** (`GET /chat/open?project=&cmd=`). **Console buttons post through `/chat`** with `hx-vals` + `hx-include="#chat-state"` | Spec: console commands act on the *active* project, which can change by free-chat switch | Console buttons with a baked-in slug: stale after a switch, and they would wipe the conversation |
| D5 | **The map reads `data-active` on `#chat-title` via CSS `:has()`**. 01's OOB title swap on a switch carries the new value | AC4, AC8, no custom JS; reuses 01's OOB swap and adds no new IDs | OOB-swapping the whole map: it replays the load animation on every switch (breaks AC10). Anything JS |
| D6 | **Per-project map selectors come from a small inline `<style>` loop over `PROJECTS`** in `index.html`. Everything else is in `styles.css` | Slugs stay single-sourced; AC9 needs per-slug `:has()` rules | Hard-coding five slugs in `styles.css`: it drifts from the registry |
| D7 | **The first panel (AutoShorts) is rendered server-side** into `index.html` with `data-initial`, which suppresses the ping | Spec §11: no layout shift; AC10: one load animation; saves a request | The prototype's `hx-trigger="load"` fetch: an empty-console flash plus an extra request |
| D8 | **Mobile sheet: hidden checkbox `#sheet`, `<label for>` and CSS.** Project actions open it by returning `<input id="sheet" checked hx-swap-oob="true">` | Spec §3 mobile sheet; no custom JS | `<dialog>` needs JS to open. `hx-on` is JS |
| D9 | **Feedback storage: JSON in an Upstash list** (`LPUSH feedback`, `LTRIM 0 999`), plus a counter `fbrl:<visitor>:<day>`. Reuses `limits._kv` and `limits.visitor_id` | Spec: private, the owner reads it in the Upstash console, per-visitor limit; 01's store | A new DB, service or email: out of scope. Raw IPs: 01 D12. An unbounded list: spam could fill the store |
| D10 | **Feedback errors keep the form.** The response is 200 with `HX-Retarget: #fb-status` + `HX-Reswap: innerHTML`. Success and "limited" replace the form | Spec §5: a store failure must not lose the visitor's text; HTMX only | 4xx responses: HTMX doesn't swap them by default. Replacing the form every time: text lost on error |
| D11 | **The resume is a static file**, compressed once (§5.6) | AC13 (≤ 1 MB); `/static` is already mounted | Serving the 4.2 MB original: slow on mobile data |
| D12 | **Geist and Geist Mono from Google Fonts**, `display=swap`, with system fallbacks | Spec §4 tokens; CSP limits only `script-src` | Self-hosting fonts: more files for no gain in v1 |
| D13 | **Content corrections vs the prototype**, found by fact-check (§8 fact table): DMC stat 3 becomes "82% of 280 fresh scripts pass all 9 viewer guarantees"; DOT_TO_IMAGE says "30 automated checks"; AI Lawyer's pitch says the simulator is in progress and names what is built | Hard rule: no invented facts; AC3 | Keeping the prototype text. Its "5 LLM roles" isn't supported (the knowledge names 4 roles), "tests" should be "checks", and it implied the simulator is playable |

## 3. Data Structures

**`app/content.py`**
- `EMAIL: str`: `"abhishekmlen25@gmail.com"`. The single source; `main.CONTACT_EMAIL = content.EMAIL`.
- `PERSON: dict[str, str]`: `name`, `role`, `place` ("Mumbai"), `profile` (resume §Profile, verbatim),
  `cue` ("Every project below has its own AI agent. Ask it anything, or run a command like").
- `NAV: tuple[tuple[str, str], ...]`: `(label, href)` for `/projects #projects`,
  `/why-hire-me #why-hire-me`, `/about #about`, `/contact #contact`, `/resume /static/resume.pdf`,
  `/feedback #feedback`. AC1.
- `FLAGS: tuple[tuple[str, str], ...]`: the six `(flag, proof)` pairs from the prototype's `FLAGS`. AC2.
- `WHY_HIRE: dict[str, str]`: `serious`, `fun`. Claude's draft until the owner rewrites it.
- `SKILLS: tuple[tuple[str, str], ...]`, `EXPERIENCE: dict`, `EDUCATION: dict`,
  `CERTS: tuple[tuple[str, str, str], ...]`: from `docs/resume.md`, as in the prototype.
- `Card` (frozen dataclass): each field enforces a spec §3 row part.
  - `short: str`: the map label and the image-slot title.
  - `status: str`, `in_progress: bool`: the label and its colour (`--good` / `--wip`).
  - `pitch: str`.
  - `stats: tuple[tuple[str, str], ...]`: exactly 3 `(value, label)` pairs.
  - `stack: tuple[str, ...]`.
- `CARDS: dict[str, Card]`: keyed by slug, with the same keys as `agent.BY_SLUG` (tested). AC3.
- `COMMAND_NAMES: tuple[str, ...] = ("usp", "pipeline", "hardest-problem", "philosophy")`.
- `Pipeline` (frozen dataclass): `built: tuple[str, ...]`, `planned: tuple[str, ...] = ()`. AC7.
- `COMMANDS: dict[str, dict[str, str | Pipeline]]`: slug → the `usp`, `pipeline`,
  `hardest-problem` and `philosophy` answers. The text comes from the prototype's `COMMANDS`,
  already fact-checked. AC5.
- `HELP: str`: "Try /usp, /pipeline, /hardest-problem or /philosophy, or just ask a question."

**`app/feedback.py`**
- `KEY = "feedback"`, `KEEP = 1000`: the list and its cap (D9).
- `MAX_MESSAGE = 500`, `MAX_FIELD = 80`: spec §3 and §5.
- `_daily_limit()`: env `FEEDBACK_DAILY_LIMIT`, default 3 (spec §10).
- Stored record: `{"at": ISO-8601 UTC, "name": str, "company": str, "message": str}`. No IP and no
  visitor hash.

**`app/limits.py`**
- `_memory: dict[str, tuple[object, float]]`: the value can now be a list (for `LPUSH`).

**Template context**

| Template | Keys |
|---|---|
| `chat_panel.html` | `project`, `greeting`, `state_token`, `cmd`, `cmd_label`, `answers`, `help`, `command_names`, `initial`, `open_sheet` |
| `index.html` | the `chat_panel.html` keys plus `person`, `nav`, `flags`, `why`, `skills`, `exp`, `edu`, `certs`, `projects` (`agent.PROJECTS`), `cards`, `email` |
| `message.html` | 01's keys plus `cmd`, `cmd_label`, `answers`, `help`, `keep_input`, `switched_slug` |

## 4. Function Specifications

**`app/content.py`**

| Function | Input → Output | Notes |
|---|---|---|
| `parse_command(message: str) -> str | None` | → a command name, `"help"`, or `None` | `strip().lower()`. No leading `/` → `None`. `m[1:]` in `COMMAND_NAMES` → that name. Any other `/...` → `"help"`. Pure |
| `command_text(slug: str, cmd: str) -> str` | → plain text for history | `help` → `HELP`. `pipeline` → built steps joined by `" → "`, plus `" (planned: …)"` when there are planned steps. Otherwise `COMMANDS[slug][cmd]`. An unknown slug raises `KeyError` |

**`app/feedback.py`**

| Function | Input → Output | Notes |
|---|---|---|
| `save(visitor, message, name="", company="", now=None) -> Literal["saved", "limited"]` | → outcome | Logic in §5.4. Store errors raise `limits.LimitStoreError`. Calls `limits._kv` through the module, so the tests' monkeypatch applies |

**`app/limits.py`**
- `_memory_run`: add `LPUSH key value` (prepend, return the length) and `LTRIM key start stop`
  (keep the inclusive slice, return `"OK"`).

**`app/main.py`**

| Function | Route / Input → Output | Notes |
|---|---|---|
| `panel_context(slug, cmd="", *, initial=False, open_sheet=True) -> dict` | → the `chat_panel.html` context | A fresh `ChatState(slug)`. When `cmd` is set, the history holds the `/cmd` turn and `command_text` (≤ `MAX_TURN_CHARS`). Also sets `answers=content.COMMANDS[slug]`, `help`, `command_names` and `cmd_label="/"+cmd` |
| `index(request)` | `GET /` → `index.html` | Content plus `panel_context(PROJECTS[0].slug, initial=True, open_sheet=False)` |
| `open_chat(request, project="", cmd="")` | `GET /chat/open` → `chat_panel.html` | Unknown project → the 01 404 fragment. A `cmd` not in `COMMAND_NAMES` is ignored. `open_sheet=True` |
| `chat(request, message=Form(""), state=Form(""), via=Form(""))` | `POST /chat` → `message.html` | Logic in §5.1. The command branch runs before `limits.check` |
| `_command_turn(request, st, message, cmd, via)` | → `message.html` response | Appends the exchange to the history. `keep_input = via == "button"` |
| `feedback_submit(request, message, name, company, website)` | `POST /feedback` → fragment | All fields are `Form("")`. Logic in §5.3 |
| `_feedback_reply(text, *, keep_form) -> HTMLResponse` | → `<p class="fb-done" role="status">…</p>` | `html.escape(text)`. `keep_form` → headers `HX-Retarget: #fb-status`, `HX-Reswap: innerHTML`. Always 200 |

## 5. Logic Flow

**5.1 `POST /chat`** (01 §5.1 with one new step)
1. `message = message.strip()`. If it is empty → 204.
2. If it is over 500 characters → the shorten notice. Stop.
3. `st = load_state(state)`. If `None` → the expired notice. Stop.
4. **New:** `cmd = content.parse_command(message)`. If `cmd` is set:
   1. `text = command_text(st.active, cmd)`.
   2. Append `{"user": message}` and `{"assistant": text}`, each cut to `MAX_TURN_CHARS`, then
      keep the last `MAX_HISTORY`.
   3. Render `message.html` with `cmd`, `cmd_label=message`, the new signed state, and
      `keep_input`.
   4. No `limits.check`, no OpenAI call, no `record_spend`. Stop.
5. 01 steps 4–8, unchanged: caps, answer, spend, state, render.
6. **Changed:** on a switch, the OOB `#chat-title` carries `data-active="<new slug>"` and no
   `data-initial`, so the map moves and pings (AC8).

**5.2 `GET /chat/open`**
1. If `project` is not in `BY_SLUG` → the 404 fragment.
2. `cmd = cmd if cmd in COMMAND_NAMES else ""`.
3. Render `chat_panel.html` with `panel_context(project, cmd)`. The response ends with the OOB
   sheet checkbox, so the mobile sheet opens (D8).

**5.3 `POST /feedback`**
1. Strip every field.
2. If the `website` honeypot is set → log at info level, then the thank-you, which replaces the
   form. Nothing is stored.
3. If `message` is empty → `keep_form`: "Please write a message first."
4. If `message` is over 500 characters → `keep_form`: "Please keep it under 500 characters."
   If `name` or `company` is over 80 → `keep_form`: "Please keep name and company under 80
   characters."
5. `feedback.save(limits.visitor_id(request), message, name, company)`. On `LimitStoreError` →
   log the exception, then `keep_form`: "Couldn't save your feedback right now. You can email
   {EMAIL}."
6. If the result is `"limited"` → replace the form: "Thanks, you've already sent feedback today."
7. If `"saved"` → replace the form: "Thanks, your feedback reached Abhishek."

**5.4 `feedback.save`**
1. `now = now or datetime.now(timezone.utc)`. `key = f"fbrl:{visitor}:{now:%Y-%m-%d}"`.
2. `_, count = limits._kv(["SET", key, "0", "EX", "86400", "NX"], ["INCR", key])`.
3. If `count > _daily_limit()` → `"limited"`.
4. `record = json.dumps({...}, ensure_ascii=False)`.
5. `limits._kv(["LPUSH", KEY, record], ["LTRIM", KEY, "0", str(KEEP - 1)])` → `"saved"`.

**5.5 Map state** (inline `<style>` in `index.html`, one block per slug `S` from `PROJECTS`)
- Active: `.console:has(#chat-title[data-active="S"]) .node[data-p="S"]` → label in ink, the dot
  filled with the accent, a soft ring. The matching `.edge[data-p="S"]` gets an accent stroke,
  width 2.
- Ping: `.console:has(#chat-title[data-active="S"]:not([data-initial])) .node[data-p="S"] .dot`
  → `animation: ping .8s ease-out`.
- Hover: `.page:has(.project[data-p="S"]:hover) .edge[data-p="S"]` and `… .node[data-p="S"] .dot`
  → accent.

**5.6 Resume PDF (one-off build step)**
1. `./venv/Scripts/python.exe -m pip install pypdf pillow`: dev venv only, not added to the
   requirements.
2. A scratchpad script, not committed:
   - read the owner's original PDF;
   - downscale each embedded image to ≤ 1600 px on its long side;
   - re-encode as JPEG at quality 70;
   - `compress_content_streams()`, then `compress_identical_objects()`;
   - write `app/static/resume.pdf`.
3. Verify: ≤ 1 MB; text still selectable; links still work; it looks the same when opened.
4. If it is still over 1 MB, or visibly worse → stop, and ask the owner for a lighter export (for
   example "Save as PDF → minimum size" from the source document).

## 6. Edge Case Implementation Map

| Spec edge case | Mechanism | Location |
|---|---|---|
| OpenAI down, or a cap reached | The command branch runs before caps and the model; 01's notices are unchanged | `main.chat` step 4 |
| AI Lawyer `/pipeline` | `Pipeline.planned` → `li.planned` (dashed), plus the legend "Dashed steps are planned, not built yet." | `content.COMMANDS`, `_command.html` |
| Command with odd case or spaces | `strip().lower()` | `content.parse_command` |
| Unknown `/command` | → `"help"` → `HELP`. No OpenAI call | `content.parse_command`, `main.chat` step 4 |
| Feedback message empty | `required` on the textarea, plus the server check → keep form | `index.html`, `main.feedback_submit` step 3 |
| Feedback message over 500 characters | `maxlength=500`, plus the server check → keep form | `index.html`, `main.feedback_submit` step 4 |
| Bot trap filled | Off-screen `website` field → a fake thank-you, nothing stored | `index.html` (`.hp`), `main.feedback_submit` step 2 |
| Over the feedback limit | `fbrl` counter → `"limited"` | `feedback.save` steps 2–3 |
| Feedback store fails | `LimitStoreError` → keep the form, with the email | `main.feedback_submit` step 5 |
| Web fonts fail | `font-family` falls back to `system-ui` / `ui-monospace` | `styles.css` tokens |
| 320 px screen | Single column; nav `overflow-x: auto`; `overflow-wrap: anywhere` on long strings; `min-width: 0` on grid children | `styles.css` mobile block |
| Reduced motion | `@media (prefers-reduced-motion: reduce)`: `animation: none` on `.edge`, `.node`, `.node .dot`; `transition: none` on `.console`; smooth scroll only under `no-preference` | `styles.css` |
| JavaScript disabled | The page is fully server-rendered, and nav links are plain anchors | `index.html` |
| Deep link to `#section` | `scroll-margin-top` on `.block`: 76 px desktop, 104 px mobile | `styles.css` |

## 7. File Layout

- **`app/content.py`**: docstring (single source; the owner approves; every number traces to
  the §8 fact table) → imports → `EMAIL`, `PERSON`, `NAV` → `FLAGS`, `WHY_HIRE` → `SKILLS`,
  `EXPERIENCE`, `EDUCATION`, `CERTS` → `Card`, `CARDS` → `Pipeline`, `COMMAND_NAMES`,
  `COMMANDS`, `HELP` → `parse_command`, `command_text`.
- **`app/feedback.py`**: docstring → imports → constants → `_daily_limit` → `save`.
- **`app/main.py`**: 01's order, plus `panel_context` after the state helpers. Routes:
  `index`, `open_chat`, `chat` (with `_command_turn`), `feedback_submit` (with `_feedback_reply`).
- **`app/templates/index.html`**:
  - `head`: charset, viewport, title, description, data-URI favicon, fonts, `styles.css`, the
    HTMX tag (unchanged, with SRI), and the per-slug `<style>` loop (§5.5).
  - `body`:
    - `input#sheet[hidden]`
    - `header.bar`: brand, and the nav from `NAV` (`/resume` gets `class="primary" download`)
    - `div.page#top`
      - `main.col`: `section.hero` → `section#projects` (5 × `article.project[data-p]`) →
        `section#why-hire-me` → `section#about` → `section#contact` → `section#feedback` (lede,
        privacy note, `form.fb` with `p#fb-status`) → `footer.foot`
      - `aside.console`: `label.c-head[for=sheet]` → `div.map` (SVG edges, hubs, labels, plus
        5 × `button.node`) → `section#chat`, which includes `chat_panel.html`
- **`app/templates/_command.html`**: the `.msg.user.cmd` bubble (`cmd_label`), then one of:
  a pipeline `ol.flow` with legend, `HELP`, or `answers[cmd]`, inside `.msg.reply.out`.
- **`app/static/styles.css`**: tokens (`:root`, variant D) → base → command bar → page grid →
  hero → sections → project rows → why/about/contact/feedback → footer → console → map →
  chat panel (01 selectors, commands, flow) → mobile `max-width: 1023px` → reduced motion.
- **`tests/conftest.py`**: `FakeResponses` → fixtures `fake`, `client` → `TOKEN_RE`,
  `open_token`, `say`, `token_of`.
- **`tests/test_front_page.py`**: imports → the `FACTS` table (§8) → one test per AC in §10.

## 8. Dependencies

- **Runtime:** no new packages.
- **Dev, one-off:** `pypdf` + `pillow` for §5.6 only, not added to `requirements*.txt`.
- **Frontend:** Google Fonts (Geist, Geist Mono). HTMX 2.0.4 is unchanged.
- **Module graph:**
  - `main` → `content`, `feedback`, `agent`, `limits`.
  - `feedback` → `limits`.
  - `content` depends on nothing.
  - Templates get content through their context only.
- **Build order:** content → limits → feedback → main → templates and CSS → tests (conftest move
  first) → resume PDF → prototype removal → `CLAUDE.md` line.
- **Conflicts found in the current code:**
  - The working tree still has the prototype. Run `git checkout -- app/main.py` and delete the
    untracked prototype files; they are preserved at `10c42cc`. The untracked 4.2 MB
    `app/static/resume.pdf` is replaced by the compressed file.
  - The fixtures in `tests/test_offline.py` move to `conftest.py`, so its imports change.
  - 01's `test_no_custom_js` counts `<script` across top-level templates (it must stay 1) and bans
    `on…=` attributes. New templates must not trip it: no `on…=` text even in copy or CSS, and
    no `js:` in `hx-vals`.
  - `styles.css` is "chat styles only" today and is replaced wholesale. The `.chat-panel`,
    `#chat-log`, `.msg.*`, `.switch-notice` and `#typing` selectors must still exist.
  - `main.CONTACT_EMAIL` stays, because tests import it. It now aliases `content.EMAIL`.
- **Owner prerequisites:**
  - Approve `COMMANDS`, `FLAGS` and `WHY_HIRE` before merge (AC18).
  - Design tweaks, whenever they come, amend spec §7.

**Fact table** (AC3; each value appears on the page, and its evidence appears verbatim in the
knowledge file):

| Project | Page value | Evidence in `knowledge/` |
|---|---|---|
| AutoShorts | `$0.036` · `7` templates · `0.00 s` drift, down from `6 s` | `30 AI calls, ~$0.036 total` · `7 production templates` · `(0.00s delta)` · `0.76–6.08s` |
| Project DMC | `r = 0.97` · `846` scripts · `82%` · 80 dots | `r = 0.97` · `846 scripts checked against 9 viewer guarantees` · `230 (82%) passed` · `simulates 80 glowing dots` |
| DOT_TO_IMAGE | `2,763` · `$5.38` / `~573` · `1,180` · 1,000–3,000 dots · 30 checks | `2,763 dots on one A2 poster` · `~$5.38` · `573` · `1,180 test functions` · `1,000 to 3,000` · `30 validation checks` |
| AI Cartoon | `₹30–50` vs `₹1,500+` · `1.74` GPU-hours, 12 shots · `463` | `₹30–50 per video` · `₹1,500+ via paid APIs` · `1.74 GPU-hours` · `12 shots, all AI motion` · `463 tests passing` |
| AI Lawyer | `0.90` vs `0.805` · `81 / 81` · `1,107` · 4 of 20 steps | `hybrid dense+keyword 0.900` · `keyword baseline 0.805` · `81 of 81 fake test citations` · `1,107 verbatim units` · `4 are merged` |
| Flags | `$0.036` · `r = 0.97` · `1,180` · `1,082` | as above · `1,082 offline tests` |

## 9. Hard Boundaries

- [ ] No custom JavaScript:
  - no `<script>` except the HTMX tag;
  - no `hx-on`, no `on…=` attributes, no `hx-trigger` filters;
  - `hx-vals` is static JSON only (never `js:`).
- [ ] Commands never call OpenAI, `limits.check` or `limits.record_spend`.
- [ ] Feedback never calls OpenAI, and is never shown on any page.
  - It is never stored unless it passes the honeypot, length and limit checks.
  - No raw IP, and no email field.
- [ ] No phone number in any template, in `content.py`, or in the rendered HTML.
- [ ] No `|safe` on any content or user input. Autoescape everywhere.
- [ ] The `#chat`, `#chat-log`, `#chat-state`, `#chat-input` and `#chat-title` IDs and 01's `hx-*`
  flow are unchanged, and 01's tests pass.
- [ ] No prototype file, route or `?variant=` handling ships.
- [ ] One load animation (the map draw). Nothing moves under reduced motion.
- [ ] Every number in `content.py` is in the §8 fact table.

## 10. Acceptance Criteria (runnable)

The gate is `./venv/Scripts/python.exe -m pytest -q` (offline). `tests/test_front_page.py` is
`F` below.

| AC | Command | Expected (pass) |
|---|---|---|
| 1 | `pytest F -k page_sections` | `GET /` is 200. The ids `projects`, `why-hire-me`, `about`, `contact`, `feedback` and `class="foot"` appear in that order. The nav has the 6 `NAV` hrefs; `/resume` has `download`; `app/static/resume.pdf` exists |
| 2 | `pytest F -k hero_flags` | Six `<details class="flag" name="flags">`, each with its proof text. Both CTA labels are present |
| 3 | `pytest F -k "project_rows or card_facts"` | Five `article.project` in `PROJECTS` order, each with 3 `<dt>`, "Talk to this project" and 4 command buttons. Every `FACTS` value is in the page, and its evidence is in the right knowledge file |
| 4 | `pytest F -k talk_opens_active` | `GET /chat/open?project=dmc` → `id="chat-title" data-active="dmc"`, plus the OOB `id="sheet"` with `checked` |
| 5 | `pytest F -k row_commands` | For all 5 × 4 `GET /chat/open?project=S&cmd=C` → 200, containing the escaped answer (for `pipeline`, every built step). `fake.calls == []`. No `rl:` key in `limits._memory` |
| 6 | `pytest F -k typed_commands` | `POST /chat` with `/usp`, `  /USP `, `/pipeline`, `/hardest-problem`, `/philosophy` → the matching answers. `/help` and `/nope` → `HELP`. `fake.calls == []`, no `rl:` key, the history grows. `via=button` → no `id="chat-input"` in the response |
| 7 | `pytest F -k pipeline_flow` | `ai_lawyer` → `ol.flow` with 5 built + 2 `li.planned` and the legend. `autoshorts` → no `planned` |
| 8 | `pytest F -k switch_moves_map` | Active `autoshorts` + "tell me about the lawyer project" → the body has `id="chat-title" data-active="ai_lawyer"` with `hx-swap-oob="true"` and no `data-initial` |
| 9 | `pytest F -k map_rules` + manual | `GET /` has the active, ping and hover rules for every slug. Manual: hovering each row lights its line |
| 10 | `pytest F -k motion` + manual | `styles.css` keyframes are only `draw`, `fade` and `ping`, and the reduced-motion block sets `animation: none` on `.edge`, `.node` and `.node .dot`. The initial panel has `data-initial`. Manual (DevTools → Rendering → reduced motion): nothing moves |
| 11 | manual | Headless Chrome `--window-size=1440,900` and `1024,900`, plus DevTools device mode at 768, 390 and 320: no horizontal scroll. Below 1024 a row action opens the sheet and Close closes it |
| 12 | `pytest F -k feedback` | Valid → "reached Abhishek" and one JSON record in `limits._memory["feedback"]`. Empty → "write a message" with the `HX-Retarget` header, nothing stored. 501 chars → "under 500", nothing stored. Honeypot → thank-you, nothing stored. 4 posts from one IP → the 4th says "already sent" and 3 are stored. `_kv` raises → the email text plus `HX-Retarget`. `fake.calls == []` |
| 13 | `pytest F -k contact_privacy` | `GET /` contains `content.EMAIL`, and neither `9930692220` nor `+91`. `resume.pdf` is ≤ 1,048,576 bytes |
| 14 | `pytest -k no_custom_js` | 01's test passes. The new test also scans `/chat/open?…&cmd=pipeline`, a command turn and the feedback reply, and finds no `js:` |
| 15 | `pytest F -k contrast` + manual | The `:root` token pairs meet ≥ 4.5: ink, slate and faint on paper and on surface; good, wip and accent-ink on surface; white on accent; white on ink. Manual: Tab through the page; every control is reached and its focus is visible |
| 16 | `pytest F -k prototype_gone` | No `app/prototype_front_page.py` and no `app/templates/prototype_front_page/`. `GET /prototype/cmd?project=dmc` → 404. `GET /?variant=d` has no `proto-switcher` |
| 17 | `python -m pytest -q` | All offline tests (01 and 02) pass |
| 18 | manual | The PR description has the owner's ticks for `COMMANDS` (20), `FLAGS` (6) and `WHY_HIRE` |
| (perf) | `pytest F -k page_weight` | `len(GET /) + len(styles.css)` < 100,000 bytes (spec §11) |

## 11. Build Checklist
- [x] Remove the prototype from the working tree (the spike branch keeps it)
- [x] `app/content.py` with the D13 corrections; `app/limits.py` memory ops; `app/feedback.py`
- [x] `app/main.py`: `panel_context`, `index`, `open_chat` (`cmd`), the command branch in `chat`,
  `POST /feedback`
- [x] Templates: `index.html`, `chat_panel.html`, `message.html`, `_chat_fields.html`, `_command.html`
- [x] `styles.css`: the variant D theme; chat selectors intact
- [x] `tests/conftest.py` move, then `tests/test_front_page.py`, all green (55 offline tests)
- [x] Resume PDF ≤ 1 MB (§5.6): 4.2 MB → 359 KB by subsetting the embedded Segoe UI Emoji font
  to the 4 glyphs used (fontTools); a PyMuPDF render is pixel-identical, and all 12 links are kept
- [x] `.env.example`, and the `CLAUDE.md` pointer line
- [x] Browser checks over Chrome DevTools, a throwaway harness that isn't committed: 20/20.
  - AC11: no sideways scroll at 1440/1024/768/390/320 px, even with every flag proof open.
  - AC10: reduced motion stops the map. The sheet opens and closes, commands answer, and the
    log scrolls to the newest turn.
  - AC9: row hover lights its line.
  - AC15: all 57 controls are reachable by Tab, each with a focus ring.
- [ ] Owner approval of the content (AC18), recorded in the PR
