# dot_to_image: AI Extreme Dot-to-Dot Puzzle Generator (repo `DOT_TO_IMAGE`, package `dot-to-dot`, CLI `d2d`)

> **Status: working engine, product-ready output, not confirmed as published.** `main` has a finished,
> tested pipeline and six defined product lines. On disk there are 39 print-ready posters and assembled
> Kids KDP book PDFs. Three experimental product lines live on separate branches/worktrees (challenge
> books, character dots + sketch guide, AI-video flipbook). All facts below come from `C:\DOT_TO_IMAGE`
> and its sibling worktrees as of the last commit on `main` (2026-09-15), read on 2026-09-25. Paths are
> relative to `C:\DOT_TO_IMAGE` unless stated otherwise. The repo's docs, docstrings and commit messages
> are deliberately written in **Hinglish** (Roman-script Hindi + English; `CLAUDE.md` "Bhasha" section).
> Quotes below are translated.

---

## One-line pitch (plain language, for a non-technical recruiter)

Software that turns a picture into a giant "connect-the-dots" puzzle with 1,000 to 3,000 numbered dots.
When you join the dots in order, a detailed drawing (a lion, a temple, a ship) appears. The output is a
print-ready PDF poster or book page. Artists usually make these puzzles by hand over weeks; this system
builds one in minutes and checks it for mistakes before a human approves it.

---

## Problem & who it's for

- **The market.** "Extreme dot-to-dot" puzzles for adults (1000+ dots) are an established category. The
  repo's market notes cite David Kalvitis's "Greatest Dot-to-Dot" series (1M+ copies sold) as proof of
  demand, and say those puzzles are drawn by hand, "hence 20 books in 25 years" (`ARCHITECTURE.md`
  Part A). The notes also say the free online "connect the dots generators" use simple nearest-neighbour
  sampling and only produce 100-300-dot kids-level output. (These are the owner's research notes; the
  repo does not verify them.)
- **The original business idea** (`project_context.md`): a zero-inventory, print-on-demand paperback on
  Amazon KDP, where Amazon prints, ships and pays royalties.
- **What the research changed** (`ARCHITECTURE.md` Part A): KDP caps new titles per day and removes
  low-quality or duplicate AI books, so the goal became a **premium quality play** ("50 genuinely hard,
  genuinely solvable puzzles") rather than mass production. The notes put it as: turn 2 weeks of manual
  work into 2 hours, not 100 books a day. AI-image disclosure on KDP is treated as mandatory, and the
  generated books include an AI-disclosure page (`debug/book_sheet.png`).
- **Who it's for today** (`CLAUDE.md` "Bikne wale products"):
  - **Adults:** large-format posters (A3 and A2). "More dots is better, fewer dots bores them."
  - **Kids:** an 8.5" x 11" KDP paperback with 51-136 dots and big numbers.
  - **Maze players:** "Draw to Win" posters. You connect the dots to draw a maze, then play it solo or
    as a two-player race.
- **Who runs it:** the owner, as an operator. The workflow is CLI-driven (`d2d ...`), with a human review
  step before anything goes into a book.

---

## What it does (user-facing features / workflow)

### Products defined on `main` (`CLAUDE.md`)

| # | Product | Preset + page | Dots | Channel |
|---|---|---|---|---|
| 1 | Spread A1 | `glasswork` + `a1_spread` | ~2415 | poster (**on hold**) |
| 2 | Extreme A2 (42x59 cm) | `glasswork` + `a2` | 1378-2390 | poster |
| 3 | 1000-Dot A3 (30x42 cm) | `glasswork` + `a3` | 1056-1669 | poster |
| 4 | Kids Letter (8.5x11 in) | `kids` + `letter` | 51-136 | **KDP book** |
| 5 | Draw to Win A2 (maze) | `d2d maze` + `a2` | 907-3126 | poster (separate SKU) |
| 6 | Solo Levels A3 (maze, 10 levels) | `d2d solo` + `a3` | 727-1503 | poster (separate SKU) |

An adult Letter/A4 book product was **deliberately dropped** after 92 AI generations: the share of the
drawing that had to be pre-printed (rather than dotted) never went below 0.25 (`CLAUDE.md`;
`docs/STEP5_LETTER_POSTER.md`). Only Kids goes to KDP. The adult line is posters only.

### End-to-end workflow (README, `.claude/rules/book.md`)

```bash
d2d prompts <theme> --page a2 --preset glasswork   # build prompts from templates (no LLM)
d2d generate "<prompt>" --theme <theme>             # AI art via Replicate + 2-second pre-filter
d2d fit art.png                                     # which paper size suits this art?
d2d batch art/generated/*.png --out runs            # N images -> N puzzle runs; one failure doesn't stop the rest
d2d review pending --runs runs                      # what needs a human look
d2d review set <id> -d approved --runs runs         # human decision (stored in SQLite)
d2d book --title "..." --author "..."               # books/{id}/interior.pdf + cover.pdf
```

Other commands: `d2d run <image>` (one image, full pipeline; exit 0 = validated PDF, 1 = validation
failed but the PDF was still written, 2 = crash), per-stage commands (`trace`, `binarize`, `skeleton`,
`graph`, `route`, `sample`, `labels`, `validate`, `render`) for debugging, `d2d ornament`
(procedural art), `d2d maze` / `d2d solo` (maze posters), and `d2d golden` (regression check).
There are about 24 commands in total in `dot_to_dot/cli.py`.

### Inputs the engine accepts

1. **AI art ("Feature 1").** The main path. Stained-glass style art (`colourglass` theme) with the
   `glasswork` preset for posters, and simple bold art for Kids.
2. **Photos ("Feature 2").** A `trace` stage turns a photo into line art (`D2D_TRACE__PROVIDER=classical`).
   It works, but the repo concludes that low contrast is a hard limit (details below). The photo
   direction later moved to a "sketch guide" product on a branch.
3. **Procedural ornament.** Generated patterns (`dot_to_dot/ornament/`). Technically perfect, but
   dropped from products because they are not recognisable pictures.
4. **Procedurally generated mazes** (`dot_to_dot/maze/`) for Draw to Win and Solo Levels.

### Outputs

- `puzzle.pdf` (what gets printed) and `solution.pdf` (the answer key) for every run.
- Book mode: `interior.pdf` + `cover.pdf`, including a title page, copyright + AI disclosure, "How to
  Solve", puzzles, and solution thumbnails (`dot_to_dot/book/`).
- Per-stage JSON/PNG artifacts and debug previews in `runs/{puzzle_id}/` for inspection and resume.

### Operator control ("sidecar")

An optional `art.d2d.json` next to an image lets a human force or suppress pen-lift breaks, pick marker
symbols, and mask out regions (normalized 0..1 coordinates, so the same mask works at any resolution).
Unknown keys fail loudly (`OVERRIDE_INVALID`), and editing the sidecar re-runs only the stages that read
the changed part (`dot_to_dot/overrides.py`, README).

### Difficulty and legibility

Difficulty comes from **dot spacing**, not a fixed dot count (`easy` / `standard` / `hard` / `extreme`),
because different art supports very different dot counts (53 to 1027 on the same corpus, README). Label
font size is computed by a measured law:
`pt_max(digits) = (min_spacing_any_mm - safety - 2*padding) / (0.224448 * digits)` (`label_sizing.py`).

---

## How it works (architecture, pipeline, data flow)

### Big picture

Three sources of line geometry meet at the same point (the `RouteResult`). From there, everything
(dot sampling, labelling, validation, PDF) is shared.

```
                    d2d prompts (templates, no LLM)
                           |
                    d2d generate --> Replicate (pinned Flux version) --> art/prefilter.py (~2 s gate)
                           |                                                 | reject -> art/rejected
                           v                                                 v
 RASTER      image -> trace -> binarize -> skeleton -> graph -> route ------------------+
             (photo or   (identity   (OpenCV)   (scikit-image  (sknw ->     (Chinese      |
              AI art)     for line               1-px + spur    NetworkX     Postman, or   |
                          art)                   pruning)       MultiGraph)  "split" mode) |
                                                                                           |
 PROCEDURAL  ornament families (contour / truchet) ---------> RouteResult -----------------+
                                                                                           |
 MAZE        grid maze -> thickened walls -> closed-loop strands -> RouteResult -----------+
                                                                                           v
             sample (RDP corners + spacing + chord repair) -> labels (greedy + simulated annealing)
               -> validate (30 checks, never raises) -> render (ReportLab PDF, embedded font)
                                                                                           |
             human review (SQLite; cannot override a validator ERROR) <--------------------+
                                                                                           v
             d2d book: page_plan -> resolve gutter -> RE-RENDER every page -> merge -> cover -> preflight (pikepdf)
```

### Stage by stage (`dot_to_dot/stages/`, `CLAUDE.md`, `DECISIONS.md`)

| Stage | What happens | Key tech / detail |
|---|---|---|
| **generate** | Text prompt -> AI line art. The provider makes a single attempt and raises typed errors; the stage handles retries. Every attempt is logged to SQLite (prompt, seed, model version, cost, pre-filter metrics). | Replicate REST via raw `httpx`, not the SDK. Default provider is `fake` (no bill). Model version must be pinned. |
| **prefilter** | Right after binarize, rejects bad art in about 2 seconds (shading, variable stroke width, fragmentation, ink fraction) instead of failing about 90 seconds later on SSIM. | `art/prefilter.py` |
| **trace** | Photo -> line art. The default `passthrough` is an identity, so the line-art path stays byte-identical. `classical` = downscale -> optional mask -> edge-preserving smooth -> Difference-of-Gaussians band -> close/despeckle -> fidelity gate. A `regions` tracer produces closed loops from colour regions. | OpenCV + scikit-image only: no model downloads, no network |
| **binarize** | Grayscale -> bilateral filter -> Otsu -> morphological close -> speck removal | OpenCV |
| **skeleton** | 1-pixel centerline + spur pruning | `skimage.morphology.skeletonize` |
| **graph** | Skeleton pixels -> graph (nodes = junctions/endpoints, edges = pixel paths) | `sknw.build_sknw(..., multi=True)` -> NetworkX MultiGraph |
| **route** | Tiny components become decorations. Disconnected components are joined by an MST over nearest endpoint pairs (`cKDTree`, k=32). `nx.eulerize` duplicates the minimum set of edges, then an Eulerian path/circuit is walked. The walk is checked for coverage, continuity and retrace ratio. | Chinese Postman (route inspection), **not** TSP |
| **split mode** (AI stained-glass art) | The art is split into (a) strokes that can take dots, (b) fine detail that is **pre-printed** as ink, (c) filled "tone" areas, and (d) lighter background lines. Each stroke is walked once (retrace 1.00 by construction). | `artsplit.py`. CPP on open strokes fails: 248 of 251 nodes had odd degree. |
| **sample** | Walk -> dots. Corners are always kept (RDP + turn-angle), with a binary search on the RDP epsilon. Minimum spacing between any two dots and between consecutive dots. **Chord-fidelity repair**: add a dot, pre-print a short arc, or force a pen-lift, worst chord first. Every pen-lift must get a printed marker. | `geometry.rdp`, `cKDTree` |
| **labels** | Places the numbers with no overlaps (NP-hard map labelling). Radial candidates -> greedy density-first seed -> **simulated annealing** (200k iterations, T 1.0 -> 0.01). Cost weights are fixed in code: label-label 1000 > label-dot 500 >> label-art 10 > bias 1. | `spatial.BoxIndex`. A single text-width source (`text_metrics.label_size_in`) is shared by solver and renderer. |
| **validate** | QC gate with 30 `check_*` functions: sequence gaps/duplicates, spacing, margins, label overlap/occlusion, SSIM vs source, chord fidelity, line-off-ink, dottability, pre-printed ink ratio, dot count, retrace, placement rate, segment and series numbering, fold keep-out, max step, unmarked pen-lift, page fill, and more. It **never raises**: a crashing check becomes a `VALIDATION_CHECK_CRASHED` issue. Only `ERROR` blocks publishing. | `validate.py` (about 1,440 lines) |
| **render** | Vector PDF at the exact page size, embedded TrueType font (`assets/fonts/Vera.ttf`), pen-lift markers drawn as vector shapes, and a solution page. Byte-reproducible. | ReportLab |
| **preflight** | Checks the PDF itself: MediaBox vs expected size (computed by a *different* code path), fonts embedded, no transparency, colour space, content inside the safe area. | `pikepdf` (`preflight.py`) |
| **review** | A human approves or rejects each puzzle. Stored in SQLite so hours of review survive a browser refresh. The guard that stops a human approving a validator-failed puzzle is in the **backend**, not the UI. | `review/store.py`, `d2d review set/pending/list/stats` |
| **book** | Two passes: the page count comes first (geometry-free), then the gutter is looked up from the page count (KDP table), then **every page is re-rendered** with the new gutter and page number, then merge, cover (spine width from paper type), and preflight. `page_plan()` deliberately has no `PageConfig` parameter, so page count cannot depend on the gutter. | `book/plan.py`, `book/assemble.py`, `book/cover.py` |

### Engineering rules the code enforces (`CLAUDE.md` "Architecture" / "Invariants")

- **Stages never import each other.** Only `pipeline.py` wires them together, and `pipeline.py`
  contains no domain logic (only ordering, persistence and resume). Stage modules never touch disk.
- **Resume needs two things:** the artifact exists **and** its per-stage `config_hash` matches.
  `Config.stage_hash()` hashes only the config sections that stage uses (`_STAGE_RELEVANT_SECTIONS`).
  If one stage is stale, every stage after it is stale.
- **Persistence** (`run_store.py`) dispatches by payload type: ndarray -> PNG, pydantic model -> JSON,
  graph -> pickle. A corrupt artifact returns `None` (treated as pending) and never raises.
- **Determinism:** same `PuzzleSpec` -> same PDF bytes. Every random step uses `cfg.seed`.
- **All errors go through one type:** `StageError(code, stage, message, **detail)` with codes in
  `models.ErrorCode`.
- **The test suite never touches the network.** Paid tests need `-m network` explicitly.
- **No chord may be printed that isn't in the art.** A pen-lift without a marker is taken back.

### Maze engine (`dot_to_dot/maze/`, `DRAW_TO_WIN.md`, `MAZE_DIFFICULTY.md`)

The idea: a poster shows only numbered dots. Joining them draws a maze, which you then play (solo, or
two players racing from opposite sides). Key pieces:

- **Closed-loop walls.** A normal "perfect" maze has walls that form **trees**, and Chinese Postman
  retraces a tree completely (measured retrace 1.70-1.78 against an ERROR limit of 1.6). The fix: carve
  a real grid maze, then **thicken the walls** into bars. A thickened tree is simply connected, so its
  outline is one closed curve. On a 16x22 maze this gave 2 contours, 43 dead ends and about 1,300 dots
  (`maze/grid.py` docstring).
- **Measured difficulty.** Difficulty is modelled as separate "loads" (solution length and the cost of
  backtracking out of wrong branches, citing Zhao & Marquez 2013 and Pullen), not as three tuning knobs.
- **Variants:** rings, swirl, checkpoints, rooms, one-way arrows, two-player. Two-player fairness comes
  from **180-degree symmetry**.
- **Anti-spoiler:** the puzzle page does not show the maze, only dots.
- **Solo pack:** 10 levels on a 22.0 x 1.2^(n-1) difficulty ladder, with seeds pinned. The worst level
  error is 3.1% (`ENGINE_LESSONS.md`); `output_pack/README.md` says every level is within 3.2% of target.

### Tools outside the pipeline (`tools/`)

- **Art Director** (`tools/director.py`): renders the finished puzzle/solution PDFs to images and asks
  an OpenAI vision model (`gpt-4o-mini`, raw httpx) whether the picture is recognisable and coherent. It
  sits outside the pipeline on purpose, so the pipeline stays deterministic and network-free. It has its
  own spend brakes (`--cost-cap`, `--max-calls`). The first run cost $0.012 for 4 calls.
- `gen_until.py` (keep generating until N usable art exist, with a hard call cap), `genart.py` (prompt
  tuning loop), `fit_levels.py`, `contact_sheet.py`, `prod_gen.py` / `prod_report.py` (product runs).

---

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.10-3.12 (`pyproject.toml`) |
| Image processing | `opencv-python-headless`, `scikit-image`, `numpy`, `scipy` (`ndimage`, `cKDTree`) |
| Graph / routing | `sknw` (skeleton -> graph), `networkx` (MST, `eulerize`, `eulerian_circuit`) |
| Geometry / collision | `shapely`, `rtree`, and a custom `BoxIndex` |
| PDF | `reportlab` (render), `pikepdf` (merge + preflight), embedded Bitstream Vera TTF |
| Config / models | `pydantic` v2 + `pydantic-settings` (env overrides like `D2D_ART__PROVIDER`) |
| CLI | `typer` (`d2d`) |
| HTTP | `httpx` (raw REST to Replicate and OpenAI, no vendor SDKs) |
| Storage | SQLite (`art/generations.db` art log, `reviews*.db` human review), JSON/PNG/NPY/pickle run artifacts |
| AI image generation | Replicate, pinned Flux model version (see Open questions). The challenge branch also benchmarked `gpt-image-2.5`, Seedream 4.5, Flux 2 Max and Nano Banana Pro. |
| AI vision QC | OpenAI `gpt-4o-mini` (Art Director tool) |
| Branch-only AI | Video: Google Veo 3.1 Fast (default), Wan 2.7, Kling v3 via Replicate. Keyframes: `google/nano-banana-pro`. Planner/vision agent: OpenAI `gpt-5.5` (flipbook). Line-art ONNX model (informative-drawings, MIT) run through `cv2.dnn`, plus MediaPipe face landmarks (sketch guide). |
| Tooling | `uv` (locked deps, `uv.lock`), `ruff` (E/F/I/UP/B, line length 100), `pytest` (+ `network` / `slow` markers), GitHub Actions CI (Python 3.10 and 3.12 matrix + e2e job) |
| Dev workflow | Spec -> implementation plan -> code per phase (`specs/`, `NN_phaseN_*_impl.md`). A merge log (`.gitkeep`), `DECISIONS.md`, `ENGINE_LESSONS.md`. Repo configured for Claude Code (`CLAUDE.md`, `.claude/rules/`, a `/gate` skill). |

---

## Key technical decisions & tradeoffs

| Decision | Alternative rejected | Why (evidence in repo) |
|---|---|---|
| **Chinese Postman routing** (cover every *edge*) | TSP / nearest-neighbour over points (the original blueprint) | TSP covers each *point* once, so the pen jumps between strokes and the drawing becomes a scribble. "The difference between kids-toy quality and Kalvitis quality" (`ARCHITECTURE.md` Part B, `route.py` docstring). |
| **Skeleton -> graph directly with `sknw`** | Potrace -> SVG -> svgpathtools | Potrace traces *outlines*, so a 1-px skeleton comes back as a doubled path and dots land on two parallel lines. It fails silently. Dropping the vector round-trip also removed a dependency and a precision loss (`ARCHITECTURE.md`, `project_context.md` §5). |
| **ReportLab + embedded TTF** | Matplotlib; ReportLab base-14 Helvetica | Matplotlib lacks exact MediaBox and font-embedding control. Base-14 fonts are never embedded and KDP rejects them, so they are kept out of the font registry on purpose (`CLAUDE.md`). |
| **8.5"x11" for the book; A3/A2 for posters** | A4 (blueprint) | 8.5x11 is KDP's US standard trim. Measured capacity on the same art: Letter 869 dots, A4 915, A3 1520, **A2 2248**. "2000+ dots only come on A2" (`DECISIONS.md`). |
| **Difficulty = spacing, `dot_budget=None`** | Fixed dot budget (e.g. 1000) | A fixed budget fails on most art (budget 1000, got 763 -> `DOT_COUNT` ERROR). "Dot count is a result of the page, not a knob" (`CLAUDE.md`). |
| **Series numbering on big formats** (restart at 999 with a double-ring marker) | Continuous 4-digit numbers | At 3.0 mm spacing, 4-digit labels need 2.51 pt, below the 3.2 pt readability floor, so the pipeline crashed at dot 1000. Restart markers are separate from pen-lift markers ("keep the pen down, only the count restarts"). |
| **Split art into dots + pre-printed ink + tone** for AI art | Force every line into dots | On detailed art, 63-74% of the line could not physically take dots (`artsplit.py`). Pre-print ink is capped (`PREPRINT_INK_BUDGET = 0.20`) and the validator has an *independent* witness at 0.24, so the check can actually fire. |
| **AI stained-glass art replaces procedural ornament** | Keep procedural ornament (perfect metrics: fill 1.00, retrace 1.00, SSIM 0.87-0.97) | The Art Director and the owner judged the ornaments "abstract wavy lines", not a picture. Tradeoff accepted: A2 dots dropped from 4179 to about 2390, and art now costs money. The owner's framing: "will we sell art or abstract lines?" (`docs/REAL_ART.md`). |
| **Validator never raises; only ERROR blocks; humans cannot override** | Validator that auto-fixes; UI-only guard | The report is never empty, even if a check crashes. The guard lives in `review/store.py`, so no script or future API can bypass it (`DECISIONS.md`). |
| **Resume by artifact + per-stage config hash** | Resume if the file exists | Existence-only resume would silently reuse stale dots after a config change (`pipeline.py` docstring). |
| **Label-solver weights hard-coded, not config** | Runtime-tunable weights | "A knob that can make a puzzle unsolvable should be a reviewed code change, not runtime config" (`labels.py`). |
| **Raw `httpx` for Replicate/OpenAI** | Vendor SDKs | Full control over retry and timeout, easier to mock, less version churn (`art/providers/replicate.py`). |
| **Default art provider `fake`, pinned model version, two spend brakes** (`cost_cap_usd` + `max_generations_per_run`) | Real provider by default, `latest` model | "A forgotten flag must not create a real API bill"; reproducibility of books months later (`CLAUDE.md`). |
| **DoG band tracing, no GrabCut by default** (photo path) | XDoG tone mode; automatic GrabCut subject isolation | Tone mode gave 18-25% ink (blobs) against 1.4% for band mode. GrabCut's mask had IoU 0.20 with the real outline, and runtime rose from 0.3 s to 26 s. Manual masks via the sidecar are "the honest route" (`DECISIONS.md`). |
| **Maze walls thickened into closed loops** | Blob/Voronoi mazes (first design) | The blob design **could not make dead ends** (corridor degree 0, 2 or 3, never 1). After the owner allowed U-turns, dead ends became the main source of difficulty (`DRAW_TO_WIN.md` update 2). |
| **Kill the adult Letter/A4 product** | Keep tuning prompts | 92 generations across three art "mediums", with pass conditions written *before* running. Every one FAILED. "Don't repeat prompt tuning" (`CLAUDE.md`, `ENGINE_LESSONS.md`). |
| **One trunk (`main`); products are git *tags*, not branches; dead ends archived as tags** | One branch per product | Two product branches would mean merging every bugfix twice, forever (`.gitkeep` release notes). The later cleanup went from 81 branches to 7 with a zero-loss proof (`BRANCH_CLEANUP_PLAN.md`). |

---

## Hard problems solved / engineering highlights

1. **Routing that follows the artwork.** The graph is built from the skeleton, MST-bridged, eulerized
   and walked as an Eulerian path. There is a gradient-coloured debug render (blue -> red along the
   walk), because metrics alone can't tell natural stroke order from scribble (`debug/route_render.py`).
   A subtle bug class is documented: edge pixels stored in reverse order create a "V" that passes
   continuity checks but shows on paper.
2. **NP-hard label placement for 1,000-3,000 numbers**, solved with greedy seeding + simulated
   annealing, plus measured legibility laws. A market complaint is noted: reviewers of 1000-dot books
   need a magnifying glass, since digits at the `extreme` preset are only 0.86 mm tall. The repo shows
   that three label fields must change together to get bigger numbers (`DECISIONS.md` "legibility law").
3. **"Clean metrics != clean output."** A bug where every marked dot's number was printed on top of its
   own marker stayed hidden for a month with `placement_rate` 0.9947 and 0 errors. It was found only by
   rendering the PDF at 300 dpi and looking at it. This became a working rule: render every PDF with
   `pdftoppm` and inspect it (`CLAUDE.md` rule 4, `ENGINE_LESSONS.md`).
4. **A check that shares its source with the thing it checks verifies nothing.** Found three times: an
   A2 PDF was actually generated at Letter size (8.5x11), and all checks passed because they read the
   same config. A large-format left margin was zero and preflight passed for the same reason. Fix:
   expected size and actual size now come from two independent code paths (`preflight.expected_mediabox`
   vs `render.page_size_pt`), guarded by `tests/test_phase14_page_size.py`. In a similar case, the
   first 13-puzzle Kids book failed its own preflight: a caption's descenders ("p", "y", "_") dipped
   1.35 pt below the 0.375" safe margin, which KDP would reject. The existing test missed it because it
   filled only one grid row (commit `0870880`).
5. **False straight lines across posters.** A pen-lift flag was read at a single sampled point, so on
   A3 the same art printed a 240 mm fake line (344 mm on A2). The fix checks the whole walk span between
   consecutive dots, and a test runs it on every page preset (`DECISIONS.md` "Bridge flag").
6. **Chord fidelity + "dottability".** The repo introduced a metric for "is the straight line the solver
   will draw actually on the art?", and a cause metric: the share of ink lying closer than the minimum
   dot spacing. Repair results, for example e2 art on A2: SSIM 0.873 -> 0.915, over-tolerance chords
   15.3% -> 5.7% (`DECISIONS.md`).
7. **Validator tested by mutation.** `tests/mutations.py` injects single faults (duplicate index, gaps,
   shuffled order, and so on) into known-good puzzles, to prove each check actually fires.
8. **Golden-corpus regression with directional comparison.** SSIM or placement *dropping* is a failure;
   retrace *rising* is a failure; improvements are not. The baseline is never auto-updated
   (`golden.py`). The repo claims `d2d golden` stayed 5/5 across 40+ phases, because every big change
   shipped as an opt-in path with defaults unchanged (`ENGINE_LESSONS.md` method 7).
9. **Maze theory made practical.** Proved that perfect-maze walls are trees (fatal for Chinese Postman)
   and solved it by thickening. A measured "braid" bug was caught: `hard` had a *shorter* solution than
   `easy` (2392 mm vs 3432 mm), because loops are shortcuts. The fix re-measures the path after each
   cull (`MAZE_DIFFICULTY.md` §1).
10. **Bugs in its own code found by measurement** (Phases 45-46 merge log): tone had silently died on
    64 of 80 posters (a crop/pad bug), and a frame guard meant 0 of 539 branches produced a background.
11. **Cost discipline for paid AI.** Two spend brakes. Every paid experiment gets a committed
    "pass condition" file *before* money is spent, so results can't move the bar afterwards. The repo
    found and documented that the in-process call counter resets per shell process, and that Replicate
    throttles to 6 requests/min under $5 credit (`ENGINE_LESSONS.md`).
12. **Working on a small machine.** The full test suite gets OOM-killed on this laptop (~1.2 GB free),
    so the quality gate runs `ruff` + pytest in 5 chunks + `d2d golden` separately (`.gitkeep` release
    notes, `/gate` skill).
13. **Zero-loss git cleanup.** 81 branches -> 7. Every removed name became an annotated tag pushed to
    GitHub, with a bundle backup, a `.git` copy, a restore-test clone, and a scripted
    "ZERO-LOSS PROOF: PASS" across 84 refs (`BRANCH_CLEANUP_PLAN.md`, `.gitkeep`).

---

## Results, metrics, scale

**Output produced (on disk, not in git):**
- **39 print-ready posters** in `output_pack/`: Extreme A2 x10 (1378-2491 dots), 1000-Dot A3 x10
  (1056-1655), Draw to Win A2 x9 (907-3126), Solo Levels A3 x10 (727-1503). All are "validator-clean
  (no ERROR)" (`output_pack/README.md`).
- **"10 x 3" product catalogue** (`product/CATALOG.md`): 10 A2 (1589-2787 dots), 10 A3 (998-1464),
  and 10 Kids art (52-131 dots), each with measured warnings listed honestly.
- **Record dot count:** 2,763 dots on one A2 poster (cathedral, `scenic` preset). The previous ceiling
  was 2,390 (`.gitkeep` Phase 45-46).
- **Kids KDP book:** the merge log reports builds of 45 pages / 20 puzzles and later 49 pages /
  22 puzzles / 7 distinct pictures, with preflight at 0 issues. The newest assembled interior on disk,
  `books/kids_v1/interior.pdf`, is 64 pages at 8.5x11. (Page counts differ between logs and files; see
  Open questions.)

**Quality numbers:**
- Label placement rate 0.9947 on an A2 run. Golden corpus 5/5.
- Kids art judged by the Art Director at recognisable 9-10 / coherent 8-9 on 10 of 10
  (`docs/REAL_ART.md`).
- Character branch: 12 AI stained-glass characters at 1582-2453 dots each, zero ERROR
  (`C:\DOT_TO_IMAGE_character\docs\evidence\character_12.png`).

**AI art spend and yield** (`art/generations.db`, main worktree, read-only query):
- 593 logged generations: 573 real Replicate calls + 20 fake.
- **316 of the 573 passed the pre-filter.** By theme: `colourglass` 129/145, `kids` 125/150,
  `poster` 1/40, `shaded` 10/45.
- Top reject reasons: shading/variable stroke weight 140, too fragmented 46, no tone 35.
- **Total recorded spend: about $5.38** (553 of the rows use estimated cost).
- The per-image price is about $0.003, so a usable image costs about $0.012 at a ~25% accept rate for
  ornament themes (`DECISIONS.md`).
- Pre-filter acceptance is not the same as usable puzzles: for Kids, 79 art -> about 19 usable (~24%).
- Branch spend: the challenge-branch model bake-off cost $3.27 for 41 calls (`docs/STEP11_BAKEOFF.md`).
  Video flipbook runs cost $0.58-$1.72 per attempt.

**Codebase scale (`main`):**
- 79 Python modules in `dot_to_dot/`, about 23.8k lines.
- 87 test files (about 20.7k lines), **1,180 test functions**, before parametrization.
- Branches reach about 28k-32k source lines and 1,350-1,408 test functions.
- 30 validator checks, about 24 CLI commands, 51 spec/plan/doc markdown files, plus `DECISIONS.md`,
  `ENGINE_LESSONS.md` and a 1,540-line merge log.
- 198 commits on `main`, 256 across all refs, 80 tags.

**Market numbers (research estimates in `ARCHITECTURE.md`, not measured):** for an 8.5x11 100-page
B&W paperback, printing costs about $2.05. At a $12.99 list price that leaves about $5.74 profit per copy.
Poster economics were explicitly **not** measured (`ENGINE_LESSONS.md` part 5).

---

## Feature lines / worktrees

`git worktree list` (from `C:\DOT_TO_IMAGE`) plus branch and tag state:

| Folder | Branch / HEAD | What it is | Status |
|---|---|---|---|
| `C:\DOT_TO_IMAGE` | `main` @ `508bec6` (2026-09-15) | The trunk. All sellable products (dot-to-dot A2/A3/Kids + Draw to Win + Solo Levels). | Clean, pushed to GitHub. |
| `C:\DOT_TO_IMAGE_character` | `v30-character-dots` (locked) | **Two things.** (1) **Feature 2 reborn as "Sketch Guide"** (Phases 47-49): photo -> faint graded line guide + 8-step "how to draw this face" page + practice page with measurement marks. Uses an MIT line-art ONNX model through `cv2.dnn` and MediaPipe landmarks. It started after the photo-to-dots "portrait proof" (19 experiments) concluded **dots can't carry a face's likeness** (photo face: 337 dots, 0.834 pre-print vs AI wolf head: 1378 dots, 0.172). (2) **Feature 3 "character dots"**: stained-glass AI characters and a deity theme as dot-to-dot. Proof PASSED 6/10 against a pre-committed condition of 4; the deity theme scored 12/12. | Live, awaiting owner "yes" and a fix for `mediapipe` missing from `pyproject`/`uv.lock` (`BRANCH_CLEANUP_PLAN.md` §6). Last commit 2026-09-11. |
| `C:\DOT_TO_IMAGE_challenge` | `v35-challenge-quality` (locked) | **"Artist Challenge Books"** (Phases 52-54): drawing challenges built from the same art pool, in 7 kinds (Draw the Other Half/mirror, Spot the Differences, Finish, Draw the Rest, Mirror Mistakes, Grid copy / Upside-Down) x 5 levels x 3 audiences (kids 6-11, teen 12-16, adult 17+). Also: a book source for KDP, an `openai_images` provider, a brief-writing tool, and a challenge "judge". A 5-model bake-off chose on quality over price (`gpt-image-2.5` at $0.049/image, 0/8 pre-filter rejects). Two 30-page proof books were built with 0 preflight errors. | Live, waiting for a physical print test and owner "yes". Deeply coupled to core (16 expected conflict blocks with v30). Last commit 2026-09-12. |
| `C:\DOT_TO_IMAGE_flipbook` | `v37-flipbook-video` (locked) | **Flipbook product** (Phases 55-58). First, code-drawn animation with a measured smoothness threshold: 3.5 mm per-frame movement, set by the owner's eye test, which favoured the 144-frame version. Then "any story" via **AI video**: keyframes (Nano Banana Pro) -> image-to-video (Veo 3.1 Fast default, Wan 2.7 fallback, Kling v3 tested) -> frames -> a vision **frame-repair agent** (interpolate, re-render a span, trim, cut, retry) -> print imposition (cut-and-stack PDF). A cost ledger with spend brakes; `fake` is the default provider. | By the owner's decision it **always stays on its own branch** (`BRANCH_CLEANUP_PLAN.md`). Only one story was fully proven on real video; Replicate credit ran out (HTTP 402). Last commit 2026-09-13. |
| `C:\DOT_TO_IMAGE_product` | detached @ `df1d451` (= tag `v28-product-10x3`) | The "10 x 3" product run: 10 A2 + 10 A3 + 10 Kids items, catalogue and tools. | **Merged into main** 2026-09-15 (`d7519ef`). The folder is kept (locked) because it holds un-versioned outputs. |
| `C:\DOT_TO_IMAGE_testfix` | detached @ `e0e66e0` (= tag `v32-canary-fix`) | Fixed three "canary" tests that broke on main after Phase 46. | **Merged into main** 2026-09-15 (`27ff1f5`). |
| *(no worktree)* | branch `v31-maze-a3` | Phase 51: maze tiers on A3 (A2 folds and isn't portable). Difficulty comes from "spice" (loops, rooms, one-way arrows, checkpoints), not narrower corridors. Easy 786 / medium 946 / hard 1425 dots. | Unmerged, waiting for the owner to visually approve A3 maze previews (`runs_maze_a3/`). |
| `C:\D2D_BACKUP` | not a worktree | Backup created before the branch cleanup: git bundle (`d2d-all.bundle`, about 80 MB), a full `.git` copy, a restore-test mirror, ref snapshots, and the old `_monument` worktree folder. | Note only. |

Earlier product lines are archived as tags (e.g. `v14-*` maze phases, `v15-tour-art` and
`v4-decorations` as recorded dead ends, `v27-portrait-proof` for the photo-to-dots experiment).

---

## Current status & timeline

**Timeline (from git; the GitHub repo was created 2026-08-20 UTC):**

| Date | Milestone |
|---|---|
| 2026-08-21 | Initial commit; Phase 0 scaffold (config, models, fixtures, CI); specs for Phases 1-10 written first |
| 2026-08-22 → 23 | Phases 1-9: binarize/skeleton, graph, Chinese Postman routing, dot sampling, label solver (SA), mutation-tested validator, PDF render + KDP preflight, E2E CLI + golden corpus, AI art provider |
| by 2026-08-28 | Phase 10: book assembly + review store + KDP preflight (archive tag `phase-10`) |
| 2026-08-31 | Phase 14: large formats (page presets) + series numbering |
| 2026-09-03 | Line fidelity (chord fidelity + dottability) merged. Maze core + Draw to Win phases 19-23 (strands, printed truth, two-player, real grid maze). |
| 2026-09-04 | Maze phases 24-29 (dot yield, solution path, variants, route visibility) |
| 2026-09-05 → 06 | AI stained-glass art + split layers + tone (`v16-art-split`); Kids product (Phase 35) |
| 2026-09-07 | One-way arrows, Solo Levels, maze fit. **Release v1.0 tags:** `v1.0-dots`, `v1.0-kids`, `v1.0-maze`. Book copy in two voices (kids/adult). |
| 2026-09-08 | Adult Letter product killed (Phase 40); measured dot-count floors (41-42); scene prompts + `ENGINE_LESSONS.md` (43); 39-poster output pack |
| 2026-09-09 | `scenic` / `monument` presets (45-46); 10x3 product run |
| 2026-09-09 → 11 | Sketch guide + character dots (branch) |
| 2026-09-11 → 12 | Artist Challenge Books + model bake-off (branch) |
| 2026-09-12 → 13 | Flipbook spike -> AI-video flipbook (branch) |
| 2026-09-15 | Branch cleanup (81 -> 7, zero-loss); merged canary fix, 10x3 tools, CLAUDE.md trim |

**Done:** the full engine; 6 product definitions; the poster output pack; Kids KDP book assembly;
maze/solo products; the review gate; the book assembler with preflight.

**In progress / waiting on the owner:** A3 maze merge (visual approval); challenge books (print test +
"yes"); sketch/character (owner "yes" + dependency fix); flipbook (separate branch by design).

**Planned / open (from `ENGINE_LESSONS.md` part 5 and `BRANCH_CLEANUP_PLAN.md` §6):**
- A physical print test of the 13 mm hard-maze corridor
- More Kids subjects (11 subjects die on too much pre-printed ink)
- A sky clause for mountain scenes
- Wider 3:2 art for A1 (the model predicts 4,943 dots; it got 2,415)
- Measuring the tabloid pre-print ceiling
- Testing human faces
- Fixing the 2 CI tests that fail on ANSI colour
- Backing up ~11 GB of outputs off the laptop

The README's "Phase 0-10 complete" status line is **out of date**; `CLAUDE.md` and the merge log are
the current sources.

---

## Limitations & known issues

- **CI is red on `main`.** The latest GitHub Actions runs (2026-09-15) fail. The documented cause: 2
  tests break on the runner because of ANSI colour codes in `--help` output (`BRANCH_CLEANUP_PLAN.md`
  §6). Locally the gate is green (ruff clean, golden 5/5).
- **Colour is lost.** The pipeline keeps only black lines. Anything the AI art separates by *colour*
  disappears after binarize. This caused "art not visible" and "grid behind the art" complaints, and
  needs prompt-level fixes (`ENGINE_LESSONS.md` part 2B).
- **Page size changes everything.** The same art needs 13-18% pre-print on A2, 25-35% on A3 and
  53-88% on Letter, so every new page needs new measurements.
- **~999 continuous-number ceiling** at 3.0 mm spacing (4-digit labels are unreadable). Large formats
  use numbering restarts.
- **Photo -> dots can't carry likeness.** The classical tracer's real wall is contrast: dark trousers on
  dark rock have no brightness step to detect. Photo portraits were abandoned for dots.
- **Known routing quirk:** `nx.eulerize` can create an unbounded-length synthetic bridge. It affects
  about 0.3% of dots and is left unfixed on purpose, because `route.py` is the riskiest module
  (`DECISIONS.md`).
- **Open maze issue:** a `START` label can cover a dot number (e.g. on the solo level-10 poster). Found
  at 300 dpi, not fixed.
- **Stale reports:** `validation.json` can be stale after resume. Filters should use raw `dot_count`.
- **Accept rates:** ~25% for some themes, and much lower for "poster"/"boldline" styles.
- **Negative prompt clauses don't work** ("no whiskers" still gives whiskers). Only positive shape
  descriptions do (`ENGINE_LESSONS.md` method 4).
- **Unverified numbers:** the KDP gutter table in `book/plan.py` still needs checking against real KDP
  docs (its own disclaimer). Poster economics are unmeasured.
- **Single-machine risk:** ~11 GB of outputs (paid art, sellable PDFs, review DBs) live only on this
  laptop plus `C:\D2D_BACKUP`.
- **Branch dependencies:** `mediapipe` is missing from dependencies on the sketch branch, and the
  challenge merge would change a pre-filter floor (0.10 -> 0.05 for `engraving`).
- **The review UI is CLI only.** The code docstring says the review UI "is a Streamlit app", but no
  Streamlit code exists in the repo.

---

## Demo assets

**GitHub:** `https://github.com/Hacke2367/DOT_TO_IMAGE`. It is **PRIVATE** (checked with `gh repo view`
on 2026-09-25). The default branch is `main`, last pushed 2026-09-15.

**Print-ready PDFs (best showcase; posters are A2/A3 vector PDFs, so render to PNG for the web):**
- `output_pack/01_extreme_a2/*_puzzle.pdf` / `*_solution.pdf`: 10 A2 posters (elephant, lion, owl, ship, temple, and more)
- `output_pack/02_thousand_dot_a3/`, `output_pack/03_draw_to_win_a2/`, `output_pack/04_solo_levels_a3/`, plus `output_pack/README.md` and `manifest.json`
- `solo_pack/level_01_saada/` … `level_10_sab-kuch/`: `puzzle.pdf` + `solution.pdf` per level
- `maze_puzzles/*.pdf`: easy/medium/hard/checkpoint/two-player/rooms/swirl mazes with solutions
- `final_output/A2_Extreme_dragon/`, `final_output/A1_Spread_wingedlion/` (older products)
- Books: `books/kids_v1/interior.pdf` (64 pp) + `cover.pdf`; `books/book_01/interior.pdf` (31 pp) + `cover.pdf`

**Images (ready to use):**
- `debug/book_sheet.png`: contact sheet of an assembled book (title, copyright + AI disclosure, How to Solve, a temple puzzle, a mandala puzzle, a maze, the solutions page)
- `docs/evidence/C_dense_puzzle.png`: a dense ~1000-dot puzzle page showing pen-lift marker symbols; `C_dense_solution.png`, `A_readable_solution.png`, `D_lion_solution.png`, `letter_3_outputs.png`
- `compare/01_letter_solution.png`, `02_letter_puzzle.png`, `03_a2_extreme.png`, `04_spread.png` (earlier procedural-ornament era)
- `proof/00_TEENO_SAATH.png` (three-way comparison)
- `runs_maze_a3/a3_*_P.png` (puzzle) and `a3_*_S.png` (solution): A3 maze previews
- `C:\DOT_TO_IMAGE_character\docs\evidence\character_12.png`: **12 AI stained-glass characters next to their dot layers, 1582-2453 dots, "zero ERROR"** (very visual)
- `C:\DOT_TO_IMAGE_character\docs\evidence\deity_12.png`, `character_final.png`, `anime_eye_before_after.png`, `sketch_guide_mock.png`
- `C:\DOT_TO_IMAGE_challenge\books\bakeoff_54\sheet_<subject>.png` (model bake-off sheets), `books\proof_54\sheet_pages_1-18.png`, `style_sheet.png`, `levelup_interior.pdf`

**Video / GIF (flipbook branch):**
- `C:\DOT_TO_IMAGE_flipbook\runs_flip\SIDE_BY_SIDE.mp4`
- `runs_flip\a48|a72|a96|a144\preview.gif` (smoothness vs frame count), `runs_flip\ek_lakeer\preview.mp4`
- `runs_flip\video\vision\final_veo\preview.mp4` + `flipbook.pdf` + `impose.pdf` (AI-video flipbook, the chosen model)

**Other:** `graphify-out/` (a knowledge graph of the codebase) and per-stage debug PNGs inside any `runs*/<id>/` folder (binarize, skeleton, graph, gradient route render, label zoom).

---

## Why this impresses a recruiter

**Non-technical angle (impact, product sense):**
- It takes a hand-made product that takes weeks per page and automates it end to end: art -> puzzle ->
  QC -> print-ready book or poster. It produced 39 finished posters and a Kids paperback.
- It is disciplined about money and evidence. AI art cost about $5 in total for ~570 generations.
  Every paid experiment had a written pass condition *before* spending. When the numbers said no (the
  adult Letter book failed after 92 tries), the product was dropped rather than forced.
- It shows real product judgment. The team chose "recognisable art" over "perfect metrics" (abstract
  patterns had flawless numbers but weren't what customers buy), and chose premium quality over
  mass-publishing after researching KDP's rules.
- It branches into adjacent products (mazes you draw and then play, drawing-challenge books, AI-video
  flipbooks) from one shared engine.

**Technical angle (depth):**
- Real algorithms applied correctly: Chinese Postman / Eulerian paths (not the naive TSP the original
  plan proposed), MST bridging, NP-hard label placement with simulated annealing, RDP simplification,
  graph theory for maze walls (trees vs closed loops), SSIM-based validation.
- Production engineering: pure stage functions, per-stage config-hash resume, byte-deterministic PDFs,
  a 30-check validator that never crashes, mutation-tested QC, a directional golden-corpus regression,
  an independent PDF preflight, two-pass book assembly, spend brakes on every paid API, network-free
  tests, locked dependencies, CI.
- Unusual measurement culture: every threshold in `DECISIONS.md` comes with the measurement that
  produced it. Bugs were found by rendering and *looking*, and written up as reusable lessons
  (`ENGINE_LESSONS.md`).
- Multi-modal AI integration kept outside the deterministic core: image generation, a vision "Art
  Director", model bake-offs, and a video-generation agent with self-repair.

---

## Likely recruiter Q&A

**Q: What is this project in one sentence?**
A: A Python pipeline that turns AI-generated (or photo-traced) line art into print-ready "extreme"
dot-to-dot puzzles with 1,000-3,000 numbered dots, validates them automatically, and assembles them
into KDP books or large posters.

**Q: Why is this hard? Isn't it just putting dots on lines?**
A: Three things make it hard. (1) **Order:** the dots must follow the drawing's strokes. That is the
Chinese Postman problem (cover every edge), not a travelling-salesman tour, or the result is a
scribble. (2) **Labels:** 1,000+ numbers must not overlap each other, other dots or the art, which is
an NP-hard map-labelling problem, solved here with simulated annealing. (3) **Printability:** dots
need a minimum physical spacing (3 mm) and numbers must stay readable, so the art itself must suit the
paper size. The repo measures this as "dottability".

**Q: What was the original plan, and what changed?**
A: The blueprint (`project_context.md`) proposed Potrace -> SVG, TSP nearest-neighbour ordering,
Matplotlib, A4 and Midjourney. The implementation replaced these with a skeleton -> graph via `sknw`,
Chinese Postman routing, ReportLab with embedded fonts, KDP's 8.5x11 for books (A3/A2 for posters),
and a hosted, pinned API model (Midjourney has no official API). Each change is justified in
`ARCHITECTURE.md` Part B and `project_context.md` §5.

**Q: How do you make sure a bad puzzle never gets printed?**
A: Two independent gates. An automated validator runs 30 checks (sequence continuity, spacing, label
overlap, SSIM against the source, chord fidelity, unmarked pen-lifts, margins, and more), and any ERROR
blocks publishing. Then a human reviews every puzzle, and the backend refuses a human "approve" on a
validator-failed puzzle. The finished PDF also goes through a pikepdf preflight (page size, embedded
fonts, no transparency, colour space, content bounds).

**Q: How is AI used?**
A: For generating the source art (Replicate, pinned model version, logged to SQLite with prompt/seed
/cost), and as an optional vision "Art Director" (`gpt-4o-mini`) that judges whether the finished
puzzle looks like a recognisable picture. AI is deliberately kept **outside** the core: the pipeline
itself is deterministic, network-free and fully testable. The branches add AI video (Veo/Wan/Kling)
with a vision repair agent for flipbooks, and a multi-model bake-off for challenge books.

**Q: How much did the AI cost?**
A: The main art log records 573 real image generations for about $5.38 total (roughly $0.003/image,
about $0.012 per usable image). A later 5-model bake-off cost $3.27. There are two spend brakes (a
dollar cap and a call-count cap), and the default provider is a free "fake" one, so a forgotten flag
can't create a bill.

**Q: What's the most interesting bug you found?**
A: A few candidates. (1) Every marked dot's number printed on top of its own marker, hidden for a month
behind a 99.47% placement rate and zero errors, and found only by rendering the PDF and looking at it.
(2) A2 posters were silently produced at Letter size, and every check passed because the check and the
output read the same config value. The fix was two independent code paths. (3) In the maze engine,
"hard" mazes had *shorter* solutions than "easy" ones, because loops act as shortcuts.

**Q: How does the maze product work?**
A: The poster shows only numbered dots. Connect them and a maze appears, which you then play solo or
as a two-player race. Because Chinese Postman fully retraces trees (and perfect-maze walls are trees),
the walls are thickened so each becomes one closed loop. Two-player fairness comes from 180-degree
symmetry, and difficulty is a measured model (solution length + backtracking cost). The Solo pack has
10 levels, each ~20% harder than the last.

**Q: What results can you show?**
A: 39 validator-clean posters (A2/A3 dot-to-dots and maze posters), a 10x3 product catalogue, and
assembled Kids KDP book PDFs with 0 preflight issues. A record 2,763 dots on one A2 poster.
Stained-glass character posters at 1,582-2,453 dots with zero errors. The full list of paths is under
Demo assets.

**Q: How is it tested?**
A: About 1,180 test functions on `main` across 87 files: unit tests per stage, mutation tests that
inject faults into good puzzles to prove the validator catches them, a golden corpus of 5 synthetic
images with directional regression checks, tests that guard prompt clauses before money is spent on
generation, and CI on Python 3.10 and 3.12. The machine has little RAM, so the gate runs the suite in
5 chunks. CI on GitHub is currently red, from 2 known tests that fail on ANSI colour codes in `--help`.

**Q: What didn't work, and what did you do about it?**
A: Several things, all documented with numbers. Procedural ornaments had perfect metrics but weren't
recognisable pictures, so they were replaced by AI art. Adult Letter-size books failed after 92
generations, so they were dropped. Photo-to-dots portraits couldn't keep a person's likeness, which led
to the "sketch guide" branch. Celtic knotwork put two dots on top of each other at every crossing, so
non-crossing art families were required. Each dead end is kept as a git tag and written up so nobody
repeats it.

**Q: Is it live / selling?**
A: The repo describes the products as "for sale" definitions, and a planning doc says selling is
"about to start". The repo itself doesn't record a KDP publication or poster sales, so the owner
should confirm (see Open questions).

**Q: What would you do next?**
A: From the repo's own open list: a physical print test of the tightest maze corridor, more Kids
subjects, wider 3:2 art for A1 posters, fixing the CI colour issue, merging the A3 maze and (after
approval) the challenge and character lines, and backing up outputs off the single laptop.

**Q: What was the development process?**
A: Spec-first and phase-by-phase: a WHAT/WHY spec, then a HOW implementation plan, then code, with a
merge log, a decisions log and a lessons file. The repo is configured for AI-assisted development with
Claude Code (`CLAUDE.md`, `.claude/rules/`, a `/gate` skill). The owner's product decisions are logged
separately ("User ka faisla") from measured engineering findings.

---

## Open questions for the owner

1. **Is anything published or sold yet?** A KDP Kids book, posters (which print service?), or none. Any
   sales or review numbers?
2. **Which exact image model** is the pinned Replicate version `c846a699…`? The ~$0.003/image price
   suggests FLUX.1 [schnell] (the challenge bake-off calls its baseline "schnell"), but the model name
   isn't stored in the repo.
3. **Kids book final size:** the logs say 45 pp / 20 puzzles and later 49 pp / 22 puzzles, while
   `books/kids_v1/interior.pdf` has 64 pages. Which is the final book?
4. **Physical proofs:** was a printed proof ordered (KDP author copy or poster print), and how did dot
   size and number legibility look on paper? The docs mention paper tests for the maze (Tests A and B
   PASS) and a sketch-guide print, but not a KDP proof copy.
5. **Should the GitHub repo stay private,** or will a public/demo version be shared? Which demo assets
   are OK to publish (AI art is uncopyrightable, but these are sellable products)?
6. **How should AI-assisted development be described?** The repo is set up for Claude Code. How does
   the owner want to present their role (product owner/architect/reviewer vs. hands-on coder)?
7. **Branch plans:** will `v31-maze-a3`, `v35-challenge-quality` and `v30-character-dots` be merged? Is
   the flipbook meant to become a real product?
8. **Review UI:** was a Streamlit review app ever built? The docstring mentions one, but only the CLI
   exists in the repo.
9. **Positioning numbers:** can the market-research figures in `ARCHITECTURE.md` (Kalvitis 1M+ copies,
   KDP 3 titles/day limit, ~$5.74/copy margin) be quoted on the portfolio, or should they be framed as
   early research assumptions?
10. **Second author email** in 4 commits: is it the owner's other account? (Not shown here, for privacy.)
