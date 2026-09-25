# DOT_TO_IMAGE

## Pitch
DOT_TO_IMAGE turns a picture into a giant "connect-the-dots" puzzle with 1,000 to 3,000 numbered dots — join them in order and a detailed drawing (a lion, a temple, a ship) appears. Artists traditionally hand-draw these puzzles over weeks; this system builds and quality-checks one in minutes, then a human approves it before print. Abhishek built it end to end: AI art generation through a validated, print-ready poster or KDP book.

## Problem
"Extreme" dot-to-dot puzzles (1,000+ dots) for adults are an established but under-supplied category. Early research assumptions noted that a well-known hand-drawn puzzle series has reportedly sold over a million copies despite few new titles in decades, since each is hand-drawn, and that free online dot-to-dot generators only produce low-quality output around 100-300 dots.

The original idea was a zero-inventory, print-on-demand paperback sold through Amazon KDP. Research into KDP's rules — capped new titles per day, low-quality/duplicate AI books removed — shifted the goal from mass production toward a premium-quality play: turning roughly two weeks of manual puzzle-making into about two hours. Generated books include a mandatory AI-art disclosure page.

The product targets three audiences: adults wanting large-format posters, kids getting a paperback with bigger numbers and fewer dots, and maze players who solve a puzzle by drawing it first.

## What it does
The core engine takes AI-generated art (its main path), a photo, or a procedural maze, and turns it into a validated, print-ready dot-to-dot puzzle. Around it, Abhishek has built several product lines:

- Extreme dot-to-dot posters (A2 and A3) for adults, sold as large-format prints.
- A Kids paperback book, assembled and preflighted for direct publication through KDP.
- "Draw to Win" and "Solo Levels" maze posters, where connecting the dots draws a maze then played solo or as a two-player race.
- A sketch-guide and character-puzzle line: photo-to-line-art drawing guides, plus stained-glass-style AI character and deity dot-to-dot puzzles.
- Artist Challenge Books: drawing-challenge puzzles (mirror-drawing, spot-the-difference, finish-the-drawing, grid-copy, and more) across difficulty levels and age groups.
- An AI-video flipbook: a short AI-generated video turned into a print-and-cut flip-book puzzle sequence.

An optional per-image override file lets a human force or suppress pen-lift breaks, choose marker symbols, or mask out regions of the art. Difficulty comes from dot spacing, not a fixed dot count, since different artwork supports very different densities.

## How it works
Three input types — AI art, traced photos, procedural mazes — converge on one routing representation; everything downstream is shared code:

```
image -> trace -> binarize -> skeleton -> graph -> route (Chinese Postman)
      -> sample dots (RDP + spacing + chord repair)
      -> label numbers (greedy seed + simulated annealing)
      -> validate (30 checks, never crashes)
      -> render vector PDF -> human review -> book assembly -> preflight
```

- **Routing:** the image is traced, binarized, and reduced to a 1-pixel skeleton, turned into a graph (junctions/endpoints as nodes, pixel paths as edges). Disconnected pieces are bridged by a minimum-spanning tree over nearest endpoints; the graph is "eulerized" (minimum edges duplicated so every edge can be walked once) and walked as an Eulerian path — Chinese Postman / route-inspection, not a travelling-salesman tour over points.
- **Dot placement:** the route is simplified with Ramer-Douglas-Peucker corner detection plus a minimum spacing rule; a "chord-fidelity" repair adds a dot, pre-prints a short arc, or forces a pen-lift wherever a line would drift off the art.
- **Labelling:** placing 1,000+ non-overlapping numbers is NP-hard, solved with a greedy density-first seed then simulated annealing (200,000 iterations, high to low temperature), with fixed cost weights penalizing label-label overlap far more than a label touching the art.
- **Validation:** ~30 independent checks (sequence gaps, spacing, margins, label overlap, similarity to source, chord fidelity, unmarked pen-lifts, and more) run on every puzzle; a crashing check is logged, never stops the pipeline, and only a hard error blocks publishing. The same puzzle spec always produces byte-identical PDF output.
- **Books:** page count is computed first, independent of layout; the binding margin is looked up from that count; every page is re-rendered with the final margin and number, then merged and preflighted.
- **Mazes:** a poster shows only numbered dots; connecting them draws the maze. Ordinary maze walls form tree shapes, which routing would retrace almost completely, so walls are carved as a grid maze and thickened into closed-loop bars instead.

## Stack
- Language: Python (3.10-3.12). CLI: Typer. Config/models: Pydantic v2. HTTP: raw `httpx` (no vendor SDKs).
- Image processing: OpenCV, scikit-image, NumPy, SciPy.
- Graph/routing: sknw (skeleton to graph), NetworkX (spanning tree, eulerization, Eulerian circuit).
- Geometry/collision: Shapely, Rtree, a custom spatial index.
- PDF: ReportLab (render), pikepdf (merge/preflight), embedded TrueType font.
- Storage: SQLite (generation logs, review decisions); JSON/PNG/pickle run artifacts.
- AI image generation: Replicate, pinned Flux model version. AI vision QC: OpenAI's `gpt-4o-mini` as an automated "Art Director."
- Product-line AI: an MIT-licensed line-art model and MediaPipe face landmarks (sketch guide); `gpt-image-2.5` from a multi-model bake-off (challenge books); AI video led by Veo 3.1 Fast, with Nano Banana Pro keyframes and `gpt-5.5` as planner (flipbook).
- Tooling: `uv` (locked deps), `ruff` (lint), `pytest`, GitHub Actions CI across two Python versions.

## Key decisions
- Chinese Postman routing (cover every edge) over TSP/nearest-neighbour ordering: TSP jumps between strokes and produces a scribble.
- Skeleton-to-graph over outline-tracing/vectorization: outline tracing returns a doubled path for a 1-pixel line, so dots land on two parallel lines.
- ReportLab with an embedded TrueType font over Matplotlib/built-in fonts: built-in fonts are never embedded, and KDP rejects non-embedded fonts.
- KDP's 8.5"x11" trim for the book, A3/A2 for posters, over an original A4 plan: measured dot capacity scales sharply with page size, and A4 isn't KDP's standard trim.
- Difficulty driven by dot spacing, not a fixed dot-count target: a fixed target failed on most art, since dot count is a consequence of artwork and page, not a free parameter.
- Splitting AI art into dots, pre-printed ink, and filled tone instead of forcing every line into dots: on detailed art 63-74% of line work couldn't legibly take dots, so it's pre-printed within a fixed budget.
- AI-generated stained-glass art over procedural (algorithmic) ornament: the ornaments had flawless metrics but read as abstract lines, not pictures; the tradeoff cost some dot density and a small per-image cost.
- A validator that never crashes, satisfiable only by fixing the issue, not a human override: the approval gate lives in the backend so no tool can bypass it.
- A default no-real-API-call art provider, a pinned model version, and two spend caps, so a forgotten flag can't create an unexpected bill.
- Killing the adult-book (Letter/A4) line after 92 generations all failed a pre-agreed pass condition.

## Engineering highlights
- Built a full Chinese-Postman/Eulerian-path routing pipeline from a raster image, with a gradient-coloured debug render to verify dot order follows natural stroke order.
- Solved NP-hard label placement for up to 3,000 numbers with a greedy-seed-plus-simulated-annealing solver, plus a measured formula linking digit count, spacing and safe font size.
- Found a bug where every dot's number sat exactly on its own marker — invisible in every metric (99.47% placement, zero errors) for a month, caught only by rendering a PDF and looking. Became a standing rule: always render and visually inspect output.
- Diagnosed a bug class where a validation check and the value it checked shared the same source, so a poster was once silently rendered at the wrong page size and still passed; fixed with two independently written code paths for expected vs. actual values.
- Chord-fidelity repairs measurably improved output: one repair took image similarity from 0.873 to 0.915 and cut off-artwork chords from 15.3% to 5.7%. Mutation tests inject known faults into good puzzles to prove each of the 30 checks fires; a golden-corpus regression suite stayed green across 40+ development phases.
- Proved standard maze walls form tree shapes (fatal for edge-covering routing) and fixed it by thickening walls into closed loops; separately caught a "hard" maze with a shorter solution than "easy" (loops as shortcuts).

## Numbers
- Typical "extreme" puzzle: 1,000-3,000 numbered dots.
- Dot ranges: Extreme A2 1,378-2,390; A3 1,056-1,669; Spread A1 (on hold) ~2,415; Kids book 51-136; Draw to Win maze 907-3,126; Solo Levels maze 727-1,503.
- Record: 2,763 dots on one A2 poster, up from a previous ceiling of 2,390.
- 39 print-ready posters produced, all validator-clean; a further 10x3 catalogue: 10 A2 (1,589-2,787 dots), 10 A3 (998-1,464), 10 Kids images (52-131).
- Kids KDP book assembled at up to 64 pages, 8.5"x11", with 0 preflight issues on completed builds.
- Label placement rate 99.47% on one A2 run; golden regression suite 5/5.
- Kids art judged by an automated "Art Director" as recognisable 9-10/10, coherent 8-9/10, on 10 of 10 images; 12 AI stained-glass character puzzles at 1,582-2,453 dots each, zero blocking errors.
- 593 logged AI art generations (573 real, 20 free test); 316 of 573 passed pre-filter; total spend ~$5.38 (~$0.003/image, ~$0.012/usable image). A five-model comparison: $3.27/41 calls. AI-video runs: $0.58-$1.72/attempt.
- Adult book line dropped after 92 generations; pre-print ink share never fell below 0.25.
- Codebase: ~79 Python modules, ~23,800 lines; ~20,700 test-code lines, 87 files, 1,180 test functions; 30 validation checks; ~24 CLI commands; 198 recorded commits.
- Early research assumptions (not measured): a 100-page B&W paperback costs ~$2.05 to print; at $12.99 list, ~$5.74 profit/copy. Poster economics were not estimated.

## Status
Done: the full puzzle-generation engine, six product configurations, the poster output batch, Kids KDP book assembly, the maze/solo products, the two-stage quality gate (validator plus human review), and the book assembler with PDF preflight.

In progress, pending Abhishek's review: an A3 maze product awaiting visual approval; Artist Challenge Books awaiting a physical print test; the sketch-guide/character-puzzle line awaiting a small dependency fix. The AI-video flipbook stays intentionally separate from the core set.

Next: a physical print test of the tightest maze corridor, more Kids subject variety, a wider poster format, pre-print limits on the largest formats, testing on human faces, a small test-suite fix, and moving output off a single laptop.

## Limitations
- Colour is lost — the pipeline keeps only black line art, causing readability complaints on some pieces.
- Page size changes everything: the same art needs ~13-18% pre-printed ink on the largest poster, 25-35% on the mid poster, 53-88% on the book page.
- Numbering has a practical ceiling of ~999 consecutive dots at readable spacing; larger puzzles restart numbering with a distinguishing marker.
- Photo-to-dots cannot reliably preserve a person's likeness (low-contrast areas give the tracer nothing to detect), so photo portraits moved to a separate drawing-guide product.
- A known, accepted routing edge case can occasionally create an unusually long connecting line; affects a small fraction of dots and is left as-is, since the routing code is considered too risky to change casually.
- A maze-product issue: a start label can occasionally sit on a dot's number. A small test-suite fix is also pending.
- AI art acceptance rate varies by style, from ~25% down to much lower for some; negative prompt instructions are unreliable (only positive descriptions work).

## Code & demos
Code is available on request — contact Abhishek. Demo outputs include: print-ready posters with up to 2,763 dots, a Kids KDP book, two-player race maze posters, AI-generated stained-glass character puzzles, and solution-key PDFs for every puzzle produced.

## Recruiter Q&A

**Q: What is this project in one sentence?**
A: A Python pipeline that turns AI-generated or photo-traced line art into print-ready "extreme" dot-to-dot puzzles with 1,000-3,000 numbered dots, checks them automatically, and assembles them into KDP books or large posters.

**Q: Why is this hard — isn't it just putting dots on lines?**
A: Order: dots must follow the drawing's strokes, a routing problem (cover every edge, not just visit every point) or the result is a scribble. Labels: placing 1,000+ non-overlapping numbers is NP-hard, solved with simulated annealing. Printability: dots need real minimum spacing, so the art must suit the page size.

**Q: How do you make sure a bad puzzle never gets printed?**
A: Two independent gates. An automated validator runs ~30 checks, and any blocking error stops publishing. A human then reviews every puzzle, and the system refuses to let anyone approve a puzzle that failed validation. The PDF then passes a separate preflight check (page size, fonts, colour space, margins).

**Q: How is AI used?**
A: AI generates the source line art (logged with prompt, seed, cost per attempt), and a separate AI vision model acts as an automated "Art Director" judging whether a puzzle reads as recognisable. AI stays outside the core pipeline, which remains deterministic and testable without it. Newer lines add AI video generation with a self-repair step for a flipbook product.

**Q: How much did the AI cost?**
A: 573 real image generations for about $5.38 total, roughly $0.003/image and $0.012 per usable image. Every experiment runs under two spend limits, and the default configuration makes no real API calls, so a forgotten flag can't create an unexpected bill.

**Q: What's the most interesting bug you found?**
A: A dot's printed number sat exactly on its own marker for about a month — every metric looked perfect (99.47% placement, zero errors) — found only by rendering a page and looking. A related class: a validation check and the value it checked came from the same source, so a poster was once silently produced at the wrong page size and still passed. Fixed with two independent code paths for expected vs. actual values.

**Q: How does the maze product work?**
A: The poster shows only numbered dots; connecting them draws a maze, solved solo or raced by two players. Standard maze walls form tree shapes, which routing would retrace almost entirely, so walls are carved as a grid maze then thickened into bars, turning the outline into one closed loop. Two-player fairness comes from mirror symmetry; difficulty models solution length plus backtracking cost.

**Q: How is it tested?**
A: ~1,180 automated test functions across 87 files: per-stage unit tests, mutation tests that inject faults into good puzzles to prove the validator catches them, a golden-image regression suite with directional pass/fail rules, and CI across two Python versions.

**Q: What didn't work, and what happened as a result?**
A: Procedural ornament patterns scored perfectly on metrics but weren't recognisable pictures, so they were replaced with AI art. The adult book product was dropped after 92 generations failed a pre-agreed quality bar. Photo-to-dots couldn't preserve likeness, so that became a separate drawing-guide product.

**Q: Who actually wrote the code, and what was the process?**
A: Abhishek designed the systems, made the architectural and product decisions, and directed AI coding agents (Claude Code / Codex) that wrote most of the code; he reviewed and tested it. Development was spec-first and phase-by-phase: a plain-language spec before each phase, then a "how" plan, then code, with a running decisions log and lessons file throughout.
