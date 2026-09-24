# AI_LAWYER: The Legal Flight Simulator (repo folder `AI_LLM_LAWYER`)

> **Status: work in progress.** The legal-data foundation (the "Evidence Room") is mostly built and tested. The AI
> characters, game engine and chat UI are designed and planned but **not built yet**. Facts below come from
> the repository at `C:\AI_LLM_LAWYER` as of its last commit (2026-09-20), read on 2026-09-25. File paths are
> relative to the repo root. Some work lives on unmerged feature branches; those are marked as such.

---

## One-line pitch (plain language, for a non-technical recruiter)

A practice simulator where ordinary people and law students rehearse a stressful real-life legal moment, being
stopped by traffic police on an Indian highway, against AI characters (the officer, a magistrate, a witness), so
they learn how the law and the procedure actually work *before* it happens for real. It works like a flight
simulator for legal situations, and it is strictly educational, **not legal advice**.

---

## Problem & who it's for

- **The problem.** Most people in India don't know their rights or the procedure when police stop them (document
  checks, fines, drunk-driving tests, what an officer may or may not demand). Reading a law doesn't help much under
  pressure. The project's stated philosophy: *"Just as pilots use simulators to practice before flying, a common
  citizen or law student can use this system to 'crash test' their reactions before facing real-life police or
  courts"* (`project_blueprint.md` §1.1). The product sells *"confidence under pressure, not legal education
  content"* (`docs/project_end_goal.md`).
- **Timing.** In July 2024 India replaced its old criminal codes (IPC, CrPC, Evidence Act) with new ones (BNS, BNSS,
  BSA). Everyone is relearning section numbers, so a tool that maps old numbers to new ones is useful
  (`project_context/feasibility_report.md` §1).
- **Who it's for (V1):** both common citizens and law students (decision D-032 in `DECISIONS.md`). Users can type in
  **English or Hinglish** (Hindi written in Roman script); statute text is always shown in its original English.
  Devanagari Hindi is out of scope for V1.
- **Later audiences (not committed):** a B2B "moot court lab" for law colleges and judiciary-coaching institutes,
  plus more scenarios (landlord disputes, consumer court, FIR filing, cheque bounce) (`docs/project_end_goal.md`,
  "After V1").

---

## What it does (user-facing features / workflow)

**None of the features in this section can be used yet.** They are the V1 design in `project_blueprint.md` and
`docs/project_end_goal.md`. What exists today is the legal-data engine underneath (see "Current status").

Planned V1 experience, one scenario only: **Traffic Police / Highway Checkpoint**:

1. **Case prep.** A Case Prep character asks clarifying questions and builds a "Case File" (facts, vehicle,
   documents, witnesses).
2. **The encounter.** In a WhatsApp-style single chat timeline, an AI traffic officer checks documents, raises
   allegations (e.g. overspeeding, no PUC certificate) and applies pressure. The user answers.
3. **Optional magistrate stage.** A short courtroom stage where a strict magistrate hears the matter (D-032:
   "police stop main, court chhota", meaning the police stop is the main part and the court stage is short).
4. **Meta-Pause.** The user can pause the simulation and ask a "Personal Counsel" mentor character theoretical
   questions (legal context only) without breaking the opponent's character.
5. **Clickable Law Engine.** When any character cites a section, it becomes a link that opens a sidebar with the
   **verbatim** bare-act text fetched from the database, never a paraphrase.
6. **Scoring and debrief.** A Judge character scores the user, applies penalties (e.g. for citing fake law) and
   gives a verdict. "Legal Context cards" in the debrief show the exact law behind each cited section.
7. **Fixed-button controls.** *[Get Help]*, *[You Reply]*, *[I Have a Doubt]*. Free text is limited to the "doubt"
   box, as an anti-abuse measure.

---

## How it works (architecture, pipeline, data flow)

The blueprint (`project_blueprint.md` §3) has three layers: **(1) the Evidence Room** (legal data, retrieval,
citation checking), **(2) the State Machine** (PostgreSQL session state), and **(3) the 3-call LLM pipeline**
(FastAPI). Only layer 1 is substantially built.

### What is built: the Evidence Room data pipeline

```
 India Code (official govt. site)
        │  download over HTTPS, verify byte size + our own pinned SHA-256
        ▼                                   (data/corpus_manifest.toml)
 data/raw_acts/mv_act_1988.pdf  (Motor Vehicles Act, 1988, "as on" 2026-08-15; git-ignored)
        │  pdfplumber text maps with explicit options; watermark, page numbers, footnotes
        │  FILTERED OUT but text is never edited; per-page "needs attention" report
        ▼
 data/extracted/mv_act_1988/pages.jsonl  (176 page records)  + report.json
        │  toc.py parses the Act's "Arrangement of Sections" → 257-entry table of contents
        │  structural chunker: sections → sub-sections / provisos / explanations / state amendments
        ▼
 data/chunks/mv_act_1988/chunks.jsonl  (1,107 VERBATIM units, each an exact character-offset slice)
 data/chunks/mv_act_1988/index.json    (section index that must equal the table of contents)
        │                                              │
        │ STEP 05 (draft PR #6, blocked)               │ STEP 06 (PR #7, in review)
        ▼                                              ▼
 Qdrant collection per embedding model        Citation resolver (no LLM, no network)
  • dense vector: local int8 ONNX model        • parser finds "sec 185 MV Act", "302 IPC",
  • sparse BM25 vector                           "u/s 279/337", "MV Act ki dhara 194D"...
  • hybrid = Reciprocal Rank Fusion            • each citation → verified / unverified /
  • exact (not approximate) search               not_in_act, + verbatim text if verified
  • idempotent build, atomic alias swap        • provisional IPC/CrPC → BNS/BNSS mapping
  • get_section(law, number)                   • S6 measurement: 0 real citations called fake
        │
        ▼
 Retrieval eval harness (STEP 03, merged): 100 synthetic questions (50 EN / 50 Hinglish),
 recall@1/3/5/10 + MRR@10, compared against a BM25 keyword baseline
```

Key modules (Python packages):

| Package | Where | What it does |
|---|---|---|
| `core/` | merged | Typed settings (`core/settings.py`, pydantic-settings, secrets masked as `SecretStr`, errors name the variable but never its value) and logging that never records request content (`core/logging_setup.py`) |
| `backend/` | merged | FastAPI app with `GET /health` (liveness only, D-022) and a pure-ASGI access-log middleware that logs only method, route *template*, status and duration: no query strings, headers, bodies, IPs or exception messages (`backend/middleware.py`) |
| `data_pipeline/corpus/` | merged | Manifest, verified downloader (TLS and host checks, refuses redirects away from HTTPS, 3 retries on 5xx), PDF extraction, table-of-contents parser |
| `data_pipeline/retrieval_eval/` | merged | Eval-set loader and validator, BM25 baseline, recall@k/MRR harness, review-sheet generator for legal QA |
| `data_pipeline/chunker/` | merged | Structural chunker: unit tree, sub-section detection rules, cross-references, state amendments, attention notes, Pydantic schema (`schema.py`) |
| `data_pipeline/index/` | branch `feature/qdrant-index` | Pinned model files, fastembed encoders, Qdrant collection/build/search, retrievers for the eval harness, benchmark (~2,560 lines) |
| `data_pipeline/citations/` | branch `feature/citation-resolver` | Citations file loader, linear-time parser, three-state resolver, S6 measurement, CLI (~1,540 lines) |
| `agents/`, `frontend/` | empty placeholders | Personas (from step 09) and Streamlit UI (from step 16) |

Import rules are enforced by a test (D-021): `core` imports nothing from the project; `agents`, `data_pipeline` and
`frontend` never import `backend`; `frontend` never imports `agents` or `data_pipeline`.

### What is planned: the runtime turn (not built)

```
 User (Streamlit chat, fixed buttons)
    │
    ▼
 FastAPI turn API ──► Python regex "bouncer" (blocks e.g. "[SYSTEM OVERRIDE]") ── not an LLM call
    │
    ▼
 CALL 1 · Gatekeeper (Groq, Llama-3 family, model TBD): route, rewrite 1st-person → 3rd-person,
          list legal issues, extract cited sections, raise flags (fake/unverified citation,
          low legal substance, out of context, injection attempt)
          ├─► citation resolver + Qdrant search ─── not LLM calls
    ▼
 CALL 2 · Stage (Anthropic Claude): speaks in character as officer / prosecutor / witness /
          Personal Counsel, using ONLY Case File facts; strict JSON output
    ▼
 CALL 3 · Bench (Anthropic Claude): Judge + Presenter: reads flags, applies penalties and score,
          verdict, builds "Legal Context cards" from verbatim retrieved text only
    ▼
 PostgreSQL (async SQLAlchemy): session_id, mode, case_file_state, turn_count, strikes, score
```

The blueprint keeps **8 AI personas** (Validator, Retriever, Presenter, Case Prep, Opponent, Judge, Co-Counsel,
Witness) but packs them into **at most 3 LLM calls per user turn** (D-002). Planned mode state machine: case prep →
encounter ⇄ pause → magistrate → debrief → over (`development_plan.md` step 08).

---

## Tech stack

- **Language:** Python 3.12 (moved from 3.10 in step 01 because 3.10 reaches end of life in October 2026; D-025).
- **API:** FastAPI 0.141, Starlette, uvicorn, Pydantic v2, pydantic-settings (`requirements/base.txt`, exact pins).
- **PDF extraction:** pdfplumber 0.11.10 / pdfminer.six (chosen over pypdf, which split words on this PDF, and
  PyMuPDF, which is AGPL-licensed; D-030).
- **Vector search (branch):** Qdrant v1.19.1 (Docker server, or `qdrant-client`'s embedded local mode for offline
  tests), `qdrant-client` 1.19.0, `fastembed` 0.8.0, `onnxruntime` 1.30, `tokenizers`, `numpy`.
- **Embedding models (local, CPU, int8/quantised ONNX, pinned by revision and SHA-256 in
  `data/embedding_models.toml`):** `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, Qdrant's quantised export),
  `multilingual-e5-large` (1,024-dim, Xenova int8 export); BM25 sparse vectors via `Qdrant/bm25`. Candidates waiting
  on download: `bge-m3` int8, `snowflake-arctic-embed-l-v2.0` int8. No hosted embedding API (D-035).
- **Databases:** PostgreSQL 18.6 (dev compose only for now; async SQLAlchemy + asyncpg + Alembic planned in step 07),
  Qdrant.
- **LLMs (planned, not integrated):** Groq (Llama-3 family) for the Gatekeeper call; Anthropic Claude (Sonnet named in
  the blueprint) for the Stage and Bench calls. Exact models are open question Q-005. `ANTHROPIC_API_KEY` and
  `GROQ_API_KEY` exist in `.env.example` but are optional and unused so far.
- **Frontend (planned):** Streamlit (step 16), with a documented plan to leave it if state management breaks down
  (blueprint §7, Q-010).
- **Infra / quality:** Docker Compose (`docker/compose.dev.yml`, ports bound to 127.0.0.1 only), GitHub Actions CI
  (pre-commit + pytest on PRs to `dev`/`main`), Dependabot (weekly, grouped), pre-commit (ruff, mypy **strict** on app
  packages, a custom secret scanner `scripts/check_secrets.py`, `no-commit-to-branch`), pytest with
  `integration` and `network` markers, uv.
- **AI-assisted development tooling:** Claude Code with project hooks written in Node.js (`.claude/hooks/`:
  `git_guard.js`, `session_brief.js`, `tracking_nudge.js`) and project skills (`/start_work`, `/ship`, `/merge_pr`,
  `/handoff`, `/log_decision`).

---

## Key technical decisions & tradeoffs

The repo keeps a formal decision log: **44 numbered decisions** (D-001 to D-044), each with context, alternatives
and consequences (`DECISIONS.md`; D-035 to D-043 live on the feature branches), plus **17 open questions** for the
owner (`docs/open_questions.md`). The most important ones:

1. **Scope cut to one feature and one scenario (D-001).** The original "V0" blueprint
   (`project_context/project_blueprint_v0.md`, titled "The AI Law Teacher") had two features: a "Master Teacher"
   tutor and a multi-scenario simulator with 8 sequential agents. A self-commissioned feasibility post-mortem
   (`project_context/feasibility_report.md`, 2026-06-10, written in the voices of a VC, a system architect and a
   legal-tech expert) judged it "a 5-person roadmap" and "top 5% of AI product ideas, bottom 50% of AI business
   plans". V1 keeps only the simulator, only for the highway checkpoint.
2. **At most 3 LLM calls per turn (D-002).** Five sequential calls would mean 10 to 20 second turns, and a chat UI
   can't survive that. The 8 personas become prompt roles multiplexed into Gatekeeper / Stage / Bench. The regex
   bouncer and vector search don't count against the budget. An automated test must enforce it (success criterion
   S1).
3. **PostgreSQL instead of SQLite (D-003).** Several personas writing state in one turn would hit SQLite's
   single-writer lock ("database is locked").
4. **Removed all "advice" (D-004).** V0 had an output block literally called "Actionable Advice". The feasibility
   report called it "an extinction-level liability", because *a disclaimer does not survive a feature that gives
   advice*. V1 gives procedural information and legal context only.
5. **Data first, agents later (D-016).** The 20-step plan builds the legal corpus, the eval set and retrieval before
   any LLM code. The rejected alternative was a skeleton-first thin demo, turned down because weak retrieval would
   show up late and the personas would be built on ungrounded law.
6. **Eval set before the chunker (D-031, `development_plan.md` step 03).** Labels are written from the law, not from
   the chunks, so chunking choices can't bias the evaluation.
7. **"Not found" ≠ "fake": three citation states (D-039).** The blueprint originally penalised any citation not
   found in Qdrant. But the corpus has only one Act; users cite the IPC, BNS or omitted/former sections; and the Act
   itself cites a *former* section 163A. The owner chose: `verified` / `unverified` (in character: "cite it
   precisely", no penalty) / `not_in_act` (the only state that can be penalised). Penalising all misses was rejected
   because it would punish users for citing real law.
8. **S6 target = zero (D-043).** No real citation may ever be marked fake. A small non-zero rate was rejected
   because wrongly penalising a correct user is exactly the harm D-039 exists to prevent.
9. **Structural, verbatim chunking (D-034).** Units form a tree (section → sub-section → proviso / explanation /
   state amendment), each an exact slice located by character offsets. Rejected: fixed-size chunks or whole sections
   (no unit for "section 130(3)", and sections run to 11,867 characters), and splitting at every "(n)" (breaks on
   nested lists in section 81). State amendments are separate units, so a state's law is never read as central law.
10. **Local multilingual embeddings, dense + hybrid benchmark (D-035), int8 only (D-036).** No hosted embedding API,
    so no new cost or key. The dev machine has 7.7 GB RAM and often ~0.3 to 1.2 GB free; a full-precision model
    thrashed the page file and the OS killed background runs twice. So only ~0.6 GB int8 exports are benchmarked,
    and a search process may use at most 1.5 GB. Accepted tradeoff: int8 may lose some quality vs full precision,
    and this benchmark cannot measure how much.
11. **Reproducible index (D-037).** Every model file is pinned by revision, size and SHA-256. Loading never
    downloads. There is one Qdrant collection per model behind an alias; the build fingerprints its inputs, so an
    unchanged rebuild writes nothing, and a changed one builds beside the live collection and swaps the alias
    atomically (a failure deletes the new one). It uses **exact** cosine search instead of approximate HNSW, because
    HNSW isn't guaranteed identical across rebuilds. The Hugging Face cache is avoided because its blob paths broke
    Windows' 260-character path limit.
12. **Provisional IPC/CrPC → BNS/BNSS mapping (D-040).** The official correspondence tables are a PDF download,
    and the owner has paused all downloads. So a small 41-row table was written from model knowledge, blind-reviewed
    by an independent AI agent, and every row is marked `provisional`. A mapping is never shown as statute text.
13. **AI legal QA instead of a named human reviewer (D-029),** backed by deterministic checks wherever possible
    (e.g. every evidence quote must appear verbatim in the Act). The known weakness (an AI checker can share the
    author's mistakes) is logged, and open question Q-016 asks whether a qualified human spot-checks before public
    release.
14. **Source PDFs outside git (D-029),** pinned by checksum. When India Code silently replaces the PDF after an
    amendment, the rebuild *intentionally fails* until a reviewed manifest change pins the new version.
15. **Shared `core/` package with import rules (D-021),** so the data-pipeline CLIs never import the web API.

---

## Hard problems solved / engineering highlights

- **Getting verbatim law out of a government PDF.** Extraction filters out the rotated "IndiaCode" watermark
  (characters ≥20 pt), footnotes (found by a short horizontal rule at the left margin in the lower half of the page),
  footnote markers (characters ≤0.8× the line's usual size) and page numbers, **without ever editing the text**. A
  formula in section 105 that the PDF *draws* (× sign, fraction bar) is recorded as an "attention note" in
  `data/corpus_attention.toml` rather than "fixed", so the text stays verbatim and readers are warned
  (`data_pipeline/corpus/extract.py`, D-030).
- **Parsing Indian statute structure.** The rules handle provisos and explanations that interrupt clause lists,
  numbers nested inside clauses that aren't sub-sections (section 81), sub-section (1) printed as `[1]`, bracketed
  amendments, chapter omission notes, headings whose printed titles differ from the table of contents (sections 18,
  110B, 147, so headings are matched by number, never title), and state amendments embedded inside central sections.
  The build **stops on anything it cannot place**, and the section index must equal the table of contents
  (`data_pipeline/chunker/`, `specs/04_structural_chunker.md`).
- **Golden tests with independent review.** 19 hard sections (`tests/golden/chunker/mv_act_1988/*.json`) were checked
  against the rendered pages by Claude and then by a fresh-context reviewer. That review caught a real bug: in 6
  places a proviso/explanation inside a clause list "swallowed" the rest of the list. It was fixed with a new spec rule
  (`tests/golden/chunker/review.md`, `docs/session_log.md`).
- **Bilingual retrieval (English + Hinglish → English statute).** The BM25 baseline missed Hinglish questions twice as
  often as English (13 vs 6 with no correct section in the top 10), mostly vocabulary gaps ("helmet" vs the Act's
  "protective headgear", "phone" vs "handheld communications devices"). Hybrid dense + BM25 search with reciprocal
  rank fusion over structural units closes most of that gap (see Results).
- **A citation parser that can't be tricked into false accusations.** It is a scanner with anchored patterns that
  runs in **linear time** (no catastrophic regex backtracking), never raises, and never logs input. It handles
  English and Hinglish forms ("dhara", "dafa", "u/s", "ki dhara", "ke tahat", even Devanagari "धारा"), lists and
  ranges ("279/337"), aliases before or after the number, glued Hindi/English words ("185ke" is not a suffix), and
  same-name different Acts (the Act cites the *1939* Motor Vehicles Act, which must not be read as the 1988 one). Its
  design rule: *doubt always falls on the `unverified` side*. A bare "302 IPC" or "MV Act 500 rupees" can never
  become "fake" (`data_pipeline/citations/parser.py`, `resolver.py`, D-042; 110 synthetic parse cases in
  `tests/data/citations/parse_cases.toml`).
- **Measured false-accusation rate (S6).** `python -m data_pipeline.citations measure` resolves 4,943 real citations
  from six groups (eval questions and evidence, every labelled section in 10 English/Hinglish citation templates,
  every section of the table of contents, every sub-section, and every citation inside the Act's own text) plus 81
  fake ones. It exits non-zero if any real citation is called fake (`data/citation_eval/results.json`).
- **Privacy by construction.** Raw user input is treated as potentially self-incriminating, so logs never contain
  request bodies, query strings, headers, IPs or exception messages (exceptions are logged by type and safe
  traceback only). Search errors are re-raised with fixed messages so query text can't leak through tracebacks.
  Resolutions carry character offsets, never the matched text (`backend/middleware.py`, `core/logging_setup.py`,
  `data_pipeline/index/search.py`, spec 06 hard rule 4).
- **Engineering under a tiny machine.** Everything is designed to run on a 7.7 GB laptop without a GPU: the
  benchmark builds and probes each model in its own process so memory is measured per model and freed between
  them, and there is an embedded Qdrant mode so development works without Docker.
- **A disciplined, auditable process.** A 20-step plan with one branch, one spec, one implementation plan and one PR
  per step (`specs/01_…` to `specs/06_…` with `_impl.md` plans); a decision log; tests that validate the plan's own
  status board (`tests/test_repo_hygiene.py`); hooks that block commits on `main` and require the owner's approval
  before any merge or protected push (`.claude/hooks/git_guard.js`).

---

## Safety, guardrails & red lines

Named as "the business's liability shield" in `CLAUDE.md`; a request that would cross one is treated as an
architecture concern to stop and raise.

**Product red lines (`project_blueprint.md` §1.3, D-004):**

- **Not legal advice.** The system gives *Procedural Information* and *Legal Context* only. It explains how statutes
  and procedures work in the abstract and **never tells a specific user what they personally should do**. The
  README states: *"Educational simulation only. It gives procedural information and legal context, not legal advice,
  and never drafts legal documents."*
- **No document drafting.** It never generates ready-to-use legal documents (FIRs, court petitions). It only explains
  how they work.
- **Verbatim law only.** Statute text shown to users is the exact retrieved text, never a paraphrase presented as a
  quote. Provisional mappings are never shown as statute text.
- **Raw user input is sensitive.** No raw user text in logs or test fixtures until Q-003 is decided (the recommended
  option is to never persist raw input and store only the third-person rewrite). All test questions are synthetic,
  and the eval-set checker rejects Devanagari, 10+ digit runs, e-mails, URLs and vehicle registration numbers
  (D-033).
- **Planned red-line test suite (S2):** zero hits for advice language (in English *and* Hinglish) and document
  requests (step 15). An educational-use notice in the UI and all UI copy checked against the red lines (step 17).

**Planned in-simulation "Shield" (blueprint §6; not built yet):**

- **Regex bouncer:** blocks system-level injection strings before any LLM call.
- **Structured-output "trapdoor":** personas must return schema-validated JSON (native tool calling + Pydantic, one
  retry). If a user jailbreaks a character and the JSON breaks, a hard-coded in-character fallback is shown (e.g.
  *"The Judge bangs the gavel. 'Counsel, stick to the facts!'"*).
- **Third-person rewrite:** the Gatekeeper rewrites extreme first-person input ("I committed…") into third person to
  lower risk while keeping the simulation.
- **Anti-hallucination fact-check:** only `not_in_act` citations get the `[FLAG: FAKE LAW DETECTED]` tag, and the Judge
  penalises in character. This part is **built** (the resolver); the flag and penalty wiring is planned.
- **Jurisdictional focus (anti-RAG-poisoning):** if a user mixes several legal issues, they must pick one, and the
  others are purged from session memory.
- **Contempt of court (anti-token-exhaustion):** low-substance spam gets `[FLAG: LOW_LEGAL_SUBSTANCE]`, one warning,
  then the simulation ends.
- **Fixed-button penalty protocol:** misuse of the free-text doubt box gives 2 warnings, then the box is disabled.
  Open question Q-007 recommends softening this to a cool-down, because hard penalties "punish your customers".

**Honest caveats the project itself records:** "zero hallucinations" was deliberately dropped as a claim (the
feasibility report calls it naive); legal QA is by AI agents, which can share the author's mistakes (D-029, Q-016);
the IPC/CrPC → BNS/BNSS table is unverified against official tables (D-040).

---

## Results, metrics, scale

All numbers are from files in the repo.

**Corpus & chunking (merged):**
- Source: The Motor Vehicles Act, 1988 (Act 59 of 1988), India Code, "as on" 2026-08-15, 4,328,659 bytes, pinned by
  SHA-256 (`data/corpus_manifest.toml`); 176 extracted pages.
- Table of contents: 257 sections (7 omitted).
- **1,107 verbatim units**: 250 sections, 649 sub-sections, 170 provisos, 32 explanations, 6 state amendments
  (`data/chunks/mv_act_1988/report.json`). Chunk build runs in under a second (`CHANGELOG.md`).
- 19 golden sections independently reviewed; 10 sections spot-checked word for word against the PDF (step 02).

**Retrieval eval set (merged):** 100 synthetic questions (50 English, 50 Hinglish; 88 checkpoint, 12 magistrate
stage), 108 labels on 48 sections, each with a verbatim evidence quote (`data/retrieval_eval/questions.toml`).
Reviewed by independent AI legal-QA agents, who found 7 issues, all fixed (`data/retrieval_eval/qa_report.md`).

**Retrieval quality (recall@10 / MRR@10; English and Hinglish recall@10 in brackets):**

| Retriever | recall@10 | MRR@10 | Where |
|---|---|---|---|
| BM25 over whole sections (baseline) | 0.805 (EN 0.870, HI 0.740) | 0.649 | `data/retrieval_eval/results/bm25.json` (merged) |
| MiniLM dense only | 0.795 (0.860, 0.730) | 0.611 | step 05 branch, committed results |
| BM25 over structural units | 0.880 (0.950, 0.810) | 0.647 | step 05 branch, committed results |
| MiniLM hybrid (dense + BM25, RRF) | 0.900 (0.950, 0.850); recall@5 0.85 | 0.731 | step 05 branch, committed results |
| **e5-large int8 hybrid** (prototype) | **0.925 (0.970, 0.880)**; recall@5 0.895 | **0.794** | `specs/05_qdrant_index.md` §9 (prototype, not yet a committed results file) |

- Hybrid beat dense-only and sparse-only for every model; units beat whole sections for BM25.
- The e5 hybrid found a correct section for 13 questions the baseline missed and lost none.
- Speed (prototype, in-process Qdrant, Intel i5-1235U laptop CPU): ~35 ms to embed a query, 12 to 23 ms median to
  search; embedding all units took 77 s (MiniLM) and 547 s (e5 int8); the real e5 index build took 612 s.

**Citation resolver (step 06, in review):**
- **S6 = 0 of 4,943** real citations wrongly marked fake; **81 of 81** fake citations caught (catch rate 1.0)
  (`data/citation_eval/results.json`).
- `data/citations.toml`: 9 laws (MV Act, IPC, CrPC, Indian Evidence Act, BNS, BNSS, BSA, Central Motor Vehicles
  Rules, Constitution), 41 provisional mapping rows (24 IPC, 17 CrPC), 2 former sections (163A, 163B).
- Blind mapping review: 40 of 41 rows agreed, 1 refined (CrPC 41 → BNSS 35(1), 35(2)), 0 disagreements
  (`data/citation_eval/mapping_review.md`).

**Engineering scale:**
- Tests: **1,082 offline tests + 13 network tests pass** on the latest branch (`progress.md`); 864 offline + 29 network
  on step 05; 692 + 23 at step 04.
- Roughly 4,000 lines of application Python merged, plus ~4,100 more on the two in-review branches (excluding tests).
- 44 commits across branches; 8 project PRs (5 merged) plus Dependabot PRs; 44 recorded decisions; 17 tracked open
  questions.

**Not yet measurable:** S1 (≤3 calls/turn), S2 (advice language), S3 (retrieval bar, awaiting owner, Q-017), S4
(latency), S5 (cost per session). None of these exist until the LLM pipeline is built.

---

## Current status & roadmap

**Timeline.** Idea, V0 blueprint and feasibility post-mortem: **2026-06-10** (the first commit). Active build:
**2026-09-14 to 2026-09-20** (setup plus steps 01 to 06 in about a week). Last commit: **2026-09-20**. `main` holds only
the initial commit; all work flows through `dev` (release to `main` happens only at step 20, `v0.1.0`).

**Overall: 4 of 20 planned steps merged; 2 more built and awaiting review/unblocking. Phase 1 (Evidence Room) is
nearly done; Phases 2 to 6 (state, LLM pipeline, guardrail hardening, frontend, ship) have not started.**

| Step | Feature | Status |
|---|---|---|
| 00 | Workflow, tracking, CI, Claude tooling, V1 plan (PR #1) | ✅ Done 2026-09-14 |
| 01 | App skeleton: settings, safe logging, `/health`, dev Postgres + Qdrant (PR #2) | ✅ Done 2026-09-15 |
| 02 | Legal corpus: verified MV Act download + extraction (PR #3) | ✅ Done 2026-09-15 |
| 03 | Retrieval eval set + BM25 baseline (PR #4) | ✅ Done 2026-09-15 |
| 04 | Structural chunker (PR #5) | ✅ Done (merge recorded 2026-09-19) |
| 05 | Qdrant index & hybrid retrieval (draft PR #6, CI green) | ⛔ **Blocked**: code built and verified offline (tasks T1 to T10); the full 4-model benchmark, default-model choice, S3 bar and Docker integration tests wait on the owner allowing ~1.17 GB of model downloads, freeing ~2 GB RAM and starting Docker (D-038) |
| 06 | Citation resolver (PR #7, stacked on step 05) | 🔄 **In review**: built and verified; S6 target of zero confirmed by owner 2026-09-20 |
| side | Blueprint wording fixes (PR #8) | 🔄 In review |
| 07 | Session store (PostgreSQL, async SQLAlchemy, Alembic) | 📋 Planned; needs Q-003 |
| 08 | Checkpoint scenario content + mode state machine | 📋 Planned; needs Q-006 |
| 09 | LLM gateway (Groq + Anthropic, structured output, 3-call budget, cost metering) | 📋 Planned; needs Q-004, Q-005, Q-014 |
| 10 to 12 | Gatekeeper (Call 1), Stage (Call 2), Bench (Call 3) | 📋 Planned |
| 13 | Turn API + terminal play + latency/cost report + model benchmark | 📋 Planned |
| 14 | Penalty protocol (warnings, contempt, jurisdictional focus) | 📋 Planned; needs Q-007 |
| 15 | Red-line suite (advice language, document requests, injection, fake law) | 📋 Planned |
| 16 to 17 | Streamlit chat UI; law sidebar, Meta-Pause, debrief | 📋 Planned; needs Q-009, Q-010 |
| 18 | Docker stack (one `docker compose up`) | 📋 Planned |
| 19 | Observability & retention | 📋 Planned |
| 20 | Release v0.1.0 (acceptance run on S1 to S6) | 📋 Planned; needs Q-016 |

Source: `development_plan.md` (status board), `progress.md`, `docs/session_log.md`, `git log --all`.

**V1 "definition of done"** (`docs/project_end_goal.md`): a user completes a full checkpoint encounter in a chat UI
with pause and score; every cited section opens verbatim text; ≤3 LLM calls per turn; state in PostgreSQL; the
full Shield works end to end; one `docker compose up` runs everything and CI is green on `main`.

**Owner-track items outside the code:** validating willingness to pay (paid waitlist or pilots with two law colleges),
which the feasibility report set as a condition; the development API budget and keys (Q-014); verifying the mapping
table against the official tables.

---

## Limitations & known issues

- **No playable product yet.** No LLM is integrated; there is no UI, no game logic and no session database. The only
  running API endpoint is `GET /health`.
- **One law only.** The corpus is the Motor Vehicles Act, 1988. BNS/BNSS and traffic rules are planned but each needs
  a new owner decision (D-029). Citations to other laws come back `unverified` by design.
- **Step 05 is blocked** on model downloads, memory and Docker. Its default embedding model and the S3 retrieval bar
  are not set, and the best number (e5 hybrid 0.925 recall@10) is from a prototype run, not yet from the committed
  benchmark.
- **Remaining retrieval misses:** mostly Hinglish (e.g. four Hinglish "driving without a licence" questions and a
  Hinglish phone question under the e5 prototype). A higher bar (≥0.95) would need a reranker or query expansion
  (Q-017 option c).
- **int8 quantisation** may cost some quality versus full-precision models, and that cost is unmeasured (D-036).
- **Provisional mapping table:** 41 IPC/CrPC → BNS/BNSS rows written from AI knowledge, not yet checked against the
  official MHA/BPR&D tables (D-040).
- **AI-only legal QA:** checks are by AI agents plus deterministic tests; whether a qualified lawyer reviews before
  release is open (Q-016).
- **Resolver scope limits (by design):** it checks that a provision *exists*, not what the user claims it says; it
  doesn't expand ranges or guess an Act from context; loosely written real citations may come back `unverified`
  rather than `verified` (D-042).
- **Extraction quirks:** the drawn formula in section 105 is incomplete as text (flagged by an attention note).
  The extraction report flags 51 of the PDF's 176 pages (pages 122 to 172) as `no_text` (no text layer); the repo
  doesn't say what those pages hold, but all 257 table-of-contents sections were still chunked
  (`data/extracted/mv_act_1988/report.json`).
- **Stacked PRs don't get CI** until retargeted to `dev` (D-028); the local gate stands in.
- **Known product risks from the feasibility report** (still open): token cost per session vs Indian consumer pricing
  (~₹99/month), the "content treadmill" of authoring new scenarios, 30 to 45 minute sessions vs mobile usage habits,
  Streamlit's limits for a stateful RPG, and possible Bar Council hostility to legal-tech.

---

## Demo assets

No screenshots, images or UI exist yet (there is no UI). Useful artifacts to show:

- **GitHub:** https://github.com/Hacke2367/AI_LAWYER is a **PRIVATE** repository (confirmed via `gh repo view`), so a
  recruiter can't open it unless the owner makes it public or shares access.
- **Product vision & reasoning:** `project_blueprint.md`, `docs/project_end_goal.md`,
  `project_context/feasibility_report.md` (a strong read on product thinking),
  `project_context/project_blueprint_v0.md` (the "before" of the pivot).
- **Decision log:** `DECISIONS.md` (full version on branch `feature/citation-resolver`).
- **Roadmap board:** `development_plan.md`, `progress.md`.
- **Sample data / outputs:**
  - `data/retrieval_eval/questions.toml`: English and Hinglish test questions with verbatim evidence (e.g. q004
    *"Kya bina driving licence ke highway par gaadi chalana allowed hai?"* → MV Act section 3).
  - `data/retrieval_eval/qa_report.md`: the AI legal-QA review of the eval set.
  - `data/retrieval_eval/results/bm25.json` (merged); `dense_minilm_l12_q.json`, `hybrid_minilm_l12_q.json`,
    `sparse_bm25.json` (step 05 branch).
  - `data/chunks/mv_act_1988/chunks.jsonl` and `report.json`: e.g. unit `mv_act_1988:185` (drunk driving) with its
    Explanation as a child unit (built locally, git-ignored).
  - `tests/golden/chunker/review.md` plus `tests/golden/chunker/mv_act_1988/*.json`: 19 golden sections.
  - `data/citation_eval/results.json` (S6 = 0/4,943; 81/81 fakes caught) and `data/citation_eval/mapping_review.md`
    (step 06 branch).
  - `data/citations.toml`: laws, aliases, provisional mapping rows (step 06 branch).
- **Specs showing engineering depth:** `specs/04_structural_chunker.md`, `specs/05_qdrant_index.md` (§9 has the
  prototype benchmark table), `specs/06_citation_resolver.md` (step 05/06 specs are on their branches).
- **CLI demos a reviewer could run** (README): `python -m data_pipeline.chunker show 185`,
  `python -m data_pipeline.retrieval_eval run --retriever bm25`, and on the step 06 branch
  `python -m data_pipeline.citations resolve` / `measure`.

---

## Why this impresses a recruiter

**Non-technical impact angle.** This is a product with a clear human purpose: helping ordinary people and law
students stay calm and informed when facing police or court, in the language they actually speak (Hinglish). What
stands out is judgment. The owner commissioned a brutal feasibility critique of their own idea, accepted it, and cut
scope to one scenario that can be done really well. They designed legal-liability protections in from the start
(no advice, no document drafting, verbatim law only, privacy for possibly self-incriminating input), and they refuse
to let the system accuse a user of citing fake law unless it can prove it. That's responsible-AI thinking in a
high-stakes domain, plus the discipline to measure it.

**Technical depth angle.** Most "legal chatbot" projects chunk a PDF and call an LLM. This one builds the hard,
unglamorous foundation first and proves it with numbers: checksum-pinned sources; a structural parser for Indian
statutes that keeps every chunk a byte-exact slice of the law; a 100-question bilingual eval set built *before* the
chunker to avoid bias; a hybrid dense + BM25 retrieval benchmark that lifts recall@10 from 0.805 to 0.90 (committed)
and 0.925 (prototype); a linear-time, three-state citation resolver measured at 0 false accusations across 4,943 real
citations; reproducible, idempotent indexing with atomic alias swaps; mypy-strict code with over 1,000 tests; and
latency/cost-aware LLM architecture (8 personas packed into ≤3 calls). It's also a case study in running AI-assisted
development with real governance: specs, decision logs, review gates and git guard hooks.

---

## Likely recruiter Q&A

**Q1. What is this project, in simple terms?**
A "Legal Flight Simulator": a text-based role-play where you practise a traffic-police stop on an Indian highway
against AI characters (officer, magistrate, witness), so you learn your rights and the procedure before facing it for
real. It's educational only and explicitly not legal advice.

**Q2. Is it finished? Can I try it?**
Not yet. It's actively in progress. The legal-data foundation is built and tested: the official Motor Vehicles Act
is downloaded, verified, split into 1,107 exact pieces, searchable in English and Hinglish, and there's a checker
that verifies cited sections. The AI characters, game logic and chat UI are designed in detail but not built. Of 20
planned steps, 4 are merged, 2 more are built and in review, and the next phases are the session database, the LLM
pipeline, guardrail hardening and the UI. The owner deliberately built the data layer first, because an AI lawyer
that gets the law wrong is worse than none.

**Q3. Why build the data pipeline before the fun AI part?**
The project's own feasibility review said the "unglamorous" parsing and retrieval layer decides whether everything
above it works, and that a retrieval eval set should come before any agent code. The plan (D-016) rejected a quick
thin demo because weak retrieval would show up late and the AI characters would be built on ungrounded law.

**Q4. How do you stop the AI from giving legal advice?**
It's a formal red line (D-004): the system only explains what the law says and how procedures work, never what *you*
should do, and never drafts FIRs or petitions. Statute text is always shown verbatim. The original design had an
"Actionable Advice" block, and it was removed because a disclaimer doesn't survive a feature that gives advice. A
dedicated red-line test suite (zero hits on advice language, in English and Hinglish) is planned as step 15, plus
schema-validated outputs with an in-character fallback if a user tries to jailbreak a character.

**Q5. How does it catch users who cite fake laws, without punishing honest users?**
A deterministic citation resolver (no LLM) parses citations like "sec 185 MV Act", "302 IPC" or "MV Act ki dhara 194D"
and gives each one of three states: `verified` (exists, with its exact text), `unverified` (can't prove either way,
e.g. another Act, an omitted section or an old IPC number, so the character just asks the user to cite precisely,
with no penalty), or `not_in_act` (the named Act is in the corpus and provably lacks that section; only this can be
penalised). Measured on 4,943 real citations: zero wrongly called fake, and 81 of 81 fake ones caught.

**Q6. What makes the retrieval good, especially for Hinglish?**
Users write "helmet" and "phone" while the Act says "protective headgear" and "handheld communications devices", so
pure keyword search struggles (BM25 baseline: 0.74 recall@10 on Hinglish). The project indexes structural units with
both a multilingual dense embedding and BM25, fused with reciprocal rank fusion. MiniLM hybrid reaches 0.90 overall
(0.85 Hinglish) in committed results; a multilingual-e5-large int8 hybrid prototype reached 0.925 (0.88 Hinglish), with
MRR@10 of 0.794. The final model choice waits on a full 4-model benchmark.

**Q7. What tech stack does it use?**
Python 3.12, FastAPI, Pydantic, pdfplumber, Qdrant with local ONNX embedding models via fastembed (int8 multilingual
models plus BM25), PostgreSQL (planned: async SQLAlchemy/Alembic), Docker Compose, GitHub Actions, pytest, ruff and
mypy strict. Planned LLMs: Groq (Llama-3 family) for a fast router call and Anthropic Claude for the role-play and
judging calls; exact models aren't chosen yet. Planned UI: Streamlit.

**Q8. Why at most 3 LLM calls per turn?**
Latency and cost. The original 8-agent design would chain ~5 sequential calls, 10 to 20 seconds per chat turn, which
kills a WhatsApp-style experience. The 8 personas are kept as prompt roles packed into three calls: Gatekeeper
(route, rewrite, extract citations, raise flags), Stage (in-character reply) and Bench (judge + score + law cards).
Vector search and the regex bouncer run in plain Python and don't count. An automated test will enforce the budget.

**Q9. How do you know the chunks are accurate legal text?**
Every chunk is an exact character-offset slice of the extracted Act, validated by schema; the section index must
equal the Act's own table of contents or the build stops; 19 difficult sections are golden tests reviewed against the
rendered PDF pages by two independent reviewers; 10 sections were spot-checked word for word; and the source PDF is
pinned by SHA-256, so a silently updated government PDF fails the build until it's reviewed.

**Q10. What was the hardest problem?**
Probably the tie between legal correctness and user trust. Structurally, Indian statutes have provisos and
explanations that interrupt clause lists, state amendments embedded in central law, and headings that don't match the
table of contents. For citations, "not found" isn't "fake": the Act itself cites a former section, and users still
use pre-2024 IPC numbers. Both were solved with explicit rules and measurement, not guesswork. Hardware was also a
constraint: everything had to run on a 7.7 GB laptop, which drove the int8 model choice and a per-process benchmark.

**Q11. How is user privacy handled?**
Users might type self-incriminating things, so raw input is treated as sensitive. Logs record only method, route
template, status and duration, never bodies, query strings, headers, IPs or exception messages. The citation parser
and search never log or echo input text. All test data is synthetic, with checks that reject phone-number-like
digits, e-mails, URLs and vehicle registration numbers. Whether raw input is ever stored is an open decision (Q-003);
the recommendation is to never persist it.

**Q12. How was it built? Did an AI write it?**
Answer honestly and positively: the repository documents an AI-assisted workflow where Claude (via Claude Code)
implements most of the code under the owner's direction. The owner acts as product owner and architect: they made
the scope, safety and architecture decisions recorded in `DECISIONS.md`, answered each open question, review every
pull request, and alone can authorise merges (enforced by a git-guard hook). The process is deliberately rigorous:
a spec and implementation plan per step, decision logs, independent reviewer agents, and over 1,000 tests. *(Confirm
with the owner how they want this framed; see Open questions.)*

**Q13. What would you do differently or next?**
Next: unblock step 05 (run the 4-model benchmark and set the retrieval bar), merge steps 05 and 06, then build the
PostgreSQL session store, the scenario and state machine, and the 3-call LLM pipeline. Known improvements already
noted: a reranker or query expansion for the remaining Hinglish misses, verifying the IPC→BNS mapping against official
tables, adding BNS/BNSS to the corpus, and possibly a qualified legal reviewer before public release.

**Q14. Is there a business case?**
The feasibility report positions it as selling "fear-reduction, not education", with a B2B fallback: moot-court labs
for law colleges and judiciary-coaching institutes. It also lists the risks honestly (token cost per session vs low
consumer pricing, scenario authoring cost, Bar Council scrutiny). Validating willingness to pay via a paid waitlist or
college pilots is on the owner's track and hasn't been done yet.

**Q15. Can I see the code?**
The GitHub repository (github.com/Hacke2367/AI_LAWYER) is currently private. The owner can share access or a
walkthrough on request.

---

## Open questions for the owner

1. **How to frame AI-assisted development?** The repo says Claude implements most of the work while you direct and
   review (D-005). How do you want the portfolio agent to describe your role (architect / product owner / reviewer)?
2. **GitHub visibility:** the repo is private. Should the portfolio link to it, make it public, or say "available on
   request"?
3. **Public project name:** "AI_LAWYER", "AI_LLM_LAWYER" or "The Legal Flight Simulator"?
4. **Step 05 unblock timing:** are the model downloads, benchmark and S3 bar decision (Q-017) expected soon, so the
   portfolio can quote a final retrieval number instead of the prototype's 0.925?
5. **Target dates:** is there a target date for a playable V1 or v0.1.0? None is recorded in the repo.
6. **Willingness-to-pay validation:** has any waitlist or law-college pilot happened outside the repo?
7. **Team:** is this solo? The repo shows one owner and no other contributors.
8. **The ~3-month gap** between the first commit / feasibility report (2026-06-10) and the build start (2026-09-14):
   was there work in between that should be mentioned?
9. **LLM choices:** any leaning on the Groq and Claude models for the three calls (Q-005), or on the latency/cost
   budgets (Q-004), that the agent can mention?
10. **Legal review:** do you plan a qualified human legal spot-check before release (Q-016)? Recruiters in legal-tech
    may ask.
11. **Image-only PDF pages:** 51 pages (122 to 172) of the Act's PDF have no text layer (probably schedules or forms).
    Do they matter for the checkpoint scenario, and is OCR planned?
