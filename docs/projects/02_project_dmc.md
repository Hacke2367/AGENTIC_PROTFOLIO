# Project DMC (Dot Matching Content)

> Source of truth: the private repo at `C:\Project_Dmc` (GitHub `Hacke2367/CONTENT_2`, **private**). Everything below is
> taken from its code, docs, specs, decision logs and git history as of 2026-09-25. File paths are relative to
> `C:\Project_Dmc` unless marked otherwise. A git-bundle backup of every branch exists at
> `C:\Project_Dmc_backup\project_dmc_all_branches_2026-09-24.bundle` (24 MB). Only this note mentions it.

---

## One-line pitch (plain language, for a non-technical recruiter)

You type in a topic. An AI pipeline writes a short Hindi voice-over and records it with a natural AI voice. Then it
renders a 30–45 second vertical video for Reels, Shorts or TikTok in which one body of glowing dots acts out each line
as it is spoken. When the voice says "you sink", the dots sink. When it says "you finally let go", they loosen and fade.
Nobody edits anything by hand.

## Problem & who it's for

- **The problem.** Short-form "reflective" or psychology content (the calm narrated reels about habits, regret,
  loneliness and forgiveness) takes a lot of manual work: writing a script, recording a voice, then finding or animating
  visuals that fit each sentence. Stock footage and generic motion graphics don't follow what is being said. The
  original blueprint (git history, `Project_context/project_blueprint.md` on tag `archive/final_update`) calls the goal
  "a fully automated Content Factory … text/audio goes in, and a complete, visually stunning mathematical 3D animation
  comes out, mapped perfectly to the emotional context of the script."
- **Who it's for.** A creator (the owner) publishing Hindi-language short-form videos on YouTube Shorts, Instagram
  Reels and TikTok. `docs/project_end_goal.md`: "a topic goes in, a finished 9:16 vertical video … comes out, with no
  manual editing (the user adds captions by hand)."
- **What makes it different.** The visuals are not decoration. The target, in the owner's words (2026-09-18, recorded
  in `CLAUDE.md` and `docs/project_end_goal.md`): **"The picture does what the words say, literally, at the moment they
  are said."** Example from the docs: the line "सब एक जगह इकट्ठा हो जाते हैं" ("they all gather in one place") has the
  dots gather into one place on that line.
- **The look is fixed on purpose:** only abstract glowing dots in a dark void. No clip-art, SVGs, emojis, faces or
  literal objects (`CLAUDE.md` "Engine rules"). The mood should feel "high quality, rich, with a peaceful vibe, and
  never like a robotic, mechanical video."

## What it does (user-facing features / workflow)

The pipeline runs as four commands. Every stage reads and writes files in one run folder, `outputs/<run>/`
(`docs/how_it_works.md` §2):

| # | Command | What happens | Output |
|---|---|---|---|
| 1 | `python brain.py "<topic>" --out outputs/<run>` | **Writer (LLM).** A topic check comes first. The writer then writes 8–12 Hindi lines, and for each line it plans what happens to "you" and which **move** shows it. A code gate and an LLM **editor**, who reads it as a first-time viewer, check the draft. **ElevenLabs** voices it with character-level timestamps. A **segmenter** cuts the audio into exactly one beat per line. | `writer_plan.json`, `narration.txt`, `narration.wav`, `alignment.json` |
| 2 | `python force_brain.py --only screenplay --out outputs/<run>` | **Director (LLM).** It confirms or changes each line's move (any change needs a note, at most 3 changes). It picks a colour mood for each line, sets strength, accents, the peak and the camera. A code gate checks the result, a headless **replay** through the real engine checks it, and a **blind critic** (LLM) grades every line. The best attempt is kept. | `screenplay.json`, `screenplay.txt` (human-readable, to review before compiling) |
| 3 | `python force_brain.py --only compile --out outputs/<run>` | **Compiler (no LLM).** It turns each move into force numbers and runs a validation gate. Every choice the engine adds on its own is written into the screenplay as `ENGINE NOTES`. | `<run>_force_script.json` |
| 4 | `python main.py --script … --bloom cinematic --voice outputs/<run>/narration.wav` | **Engine.** It renders 80 glowing dots in Manim (OpenGL) at 1080×1920, 60 fps, adds a bloom/vignette/grain pass with ffmpeg, and muxes the voice in. | `outputs/video_<stamp>/dmc_render_final.mp4` |
| 5 (QA) | `python tools/viewer_scorecard.py <mp4> <script.json> --match outputs/<run>` | **Scorecard.** It measures the finished MP4 the way a phone viewer sees it and writes one frame strip per spoken line for line-by-line review. | `scorecard/report.md`, `scorecard/match_test/beat_NN.png` |

**The move vocabulary.** There are 15 "moves", shared by the writer, the director and the engine. They are defined in
`config/gestures.py` (`MOVES` holds the words, `GESTURES` the force numbers):
gathering, crushed, opening, reaching, heavy, circling, trapped, drifting, dissolving, fracturing, holding, settling,
plus three "part" moves where a quarter of the body acts alone: leaving, returning, rising_within.
Each move has a plain-English "what the viewer sees", for example `heavy` = "the body sinks and clearly darkens" and
`dissolving` = "the body loosens, floats up and fades".

**Colour by feeling, not by hex.** The director only names a *register*: clarity, calm, melancholy, grief, numbness,
tension, dread, alarm, warmth, and so on. `config/palette.py` turns that into a fill/key/accent colour triad. A piece
may use at most 4 colours (`agentic/force_validation_gate.py MAX_DISTINCT_COLORS`).

**A real example from the repo** (`outputs/s84_maaf/`, topic "किसी को माफ़ न कर पाना", "not being able to forgive someone"):
- Hook, line 1: "उन्हें माफ़ नहीं किया, पर सज़ा तुम काट रहे हो।" ("You didn't forgive them, but you're the one serving
  the sentence.") The move is `heavy`: the body sinks and darkens.
- Turn, line 8: "माफ़ी उनकी गलती नहीं मिटाती, तुम्हें उस दिन से छुड़ाती है।" ("Forgiveness doesn't erase their mistake;
  it frees you from that day.") The move is `opening`: the body widens, lifts and brightens. This line is the peak.
- The 11 moves in order: heavy → circling → rising_within → holding → heavy → trapped → trapped → opening → opening →
  drifting → settling.
- The editor scored every one of its 9 criteria 3/3 (understood, flow, depth, hook, build, turn, landing, performable,
  natural) after 3 drafts. Voice: 528 characters, 43.28 s of audio.
- Rendered video: `outputs/review_fix76/maaf_3_gap005.mp4` (same file as `outputs/video_20260925_0134/dmc_render_final.mp4`).

## How it works (architecture, pipeline, data flow — technical depth)

```
 topic (Hindi or English)
   │
   ▼
┌──────────────────────── STAGE 1  brain.py  (agentic/pipeline.py) ────────────────────────┐
│ topic check (LLM) → WRITER (LLM, strict JSON) → CODE GATE (counts, words/line, duration,  │
│ hook, variety, allowed chars) → EDITOR (LLM "first-time viewer", 9 scores) → revise       │
│ (whole draft, or only the ≤3 flagged lines)   max 8 drafts, best draft kept               │
│        │ writer_plan.json + narration.txt                                                 │
│        ▼                                                                                   │
│ ElevenLabs eleven_multilingual_v2  convert-with-timestamps → narration.wav + alignment.json│
│        ▼                                                                                   │
│ SEGMENTER (pure Python): danda-aware sentence split; beats tile the audio exactly;        │
│ check: #beats == #writer lines, text identical                                             │
└──────────────────────────────────────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────── STAGE 2  force_brain.py --only screenplay (cinematographer.py) ──────┐
│ DIRECTOR (LLM) → GATE_RULES (15 code rules: one peak, strength floors, ≤4 colours,        │
│ light floor 0.20, ≤2 accents, motif direction, returning-after-away, arc…)                │
│   → HEADLESS REPLAY through the real engine (viewer guarantees G1–G7)                     │
│   → BLIND CRITIC (LLM sees only narration + code-written description of what renders)     │
│   ≤3 attempts; best-ranked kept; "cannot_perform" bounces back to the writer              │
└──────────────────────────────────────────────────────────────────────────────────────────┘
   │ screenplay.json
   ▼
┌──────────── STAGE 3  compile (screenplay_compiler.py + force_validation_gate.py) ─────────┐
│ move name → GESTURES force recipe + deltas, clamped to schema ranges → ForceBeat per line │
│ adds camera drift/arc, peak light & push-in, fade carry, etc. → ENGINE NOTES              │
└──────────────────────────────────────────────────────────────────────────────────────────┘
   │ <run>_force_script.json   (pydantic-validated ForceScript)
   ▼
┌──────────────────────── STAGE 4  main.py  (Manim CE 0.18.1, OpenGL) ──────────────────────┐
│ DMCScene: dark void, slow camera orbit, SafeZoneEnforcer (owns zoom)                      │
│ spawn Swarm once (80 dots as an OpenGLPMobject point cloud + hero billboard points)       │
│ ForceOrchestrator walks beats → ForceDispatcher glides forces/light/colour (OKLab)        │
│ ForceField._tick every frame (60 fps): gravity, turbulence, repulsion, flow, attractor,   │
│   confinement, anisotropy, clustering, viscosity, friction, dot pressure, cohesion,       │
│   size floor, home zone, stage, containment, brake, velocity cap, swirl — all numpy       │
│ NodeShading: per-dot energy + live depth haze + beat colour                               │
│ → dmc_render.mp4 → ffmpeg bloom/vignette/grain (post_bloom.py) → mux voice                │
└──────────────────────────────────────────────────────────────────────────────────────────┘
   │ dmc_render_final.mp4
   ▼
 QA: tools/viewer_scorecard.py (pixels of the MP4) · tools/replay_screenplay.py (headless,
     ~4 s/script) · tools/corpus_check.py (846-script corpus vs guarantees G1–G9)
```

### Key design points (from code)

- **Stages hand off through files, not memory** (`agentic/pipeline.py` docstring). Any stage can be re-run on its own
  (`--only write|tts|segment|screenplay|compile`) without paying for the stages before it. `alignment.json` means
  ElevenLabs is never called twice for the same script. The pipeline also checks that `narration.txt` still matches the
  saved alignment character for character. An edited text with stale timings is refused.
- **Every LLM call is one strict-JSON call** (`agentic/llm.py`: `response_format` json_schema with `strict: True`,
  `reasoning_effort`, `max_completion_tokens` 12000) and is metered per stage (`agentic/usage.py`). Each run prints a
  token report. The model is `gpt-5.6-sol` for the writer, editor, director and critic, overridable by env var
  (`DMC_WRITER_MODEL`, `DMC_DIRECTOR_MODEL`, …). `OPENAI_BASE_URL` can point the same code at any OpenAI-compatible
  endpoint (`brain.py`).
- **The TTS output is ground truth** (`agentic/tts_client.py`). The model is pinned (`eleven_multilingual_v2`) so pacing
  cannot drift. The client checks that the alignment arrays are index-aligned and that `''.join(characters) == text`,
  and it measures duration from the WAV file itself. The writer's gate bans Latin letters, digits and full stops
  because "one Latin letter or digit breaks the voice's character alignment and shifts every timestamp after it"
  (`agentic/force_writer.py _FOREIGN_CHARS`).
- **The segmenter** (`agentic/segmenter.py`) is pure Python and never imports secrets. It splits on the Devanagari
  danda (।). Beats *tile* the audio: each beat owns the pause after its sentence, and the last beat ends at the measured
  file duration.
- **A physics engine, not keyframes.** `utils/force_field.py` (2,731 lines) is the core. Every frame it integrates a
  velocity for every dot from a set of forces. Nobody places dots; the shape emerges. The design rule is "motion is
  viscous, never flocking: local forces share momentum, they never steer (ink, not bees)" (`CLAUDE.md`). Motion carries
  across line boundaries (velocity is only zeroed on a population change). The dispatcher *glides* force values
  (about 0.17 s) and applies a short brake in the pause between spoken lines, so each new move starts on its first word
  (`specs/55`, `docs/decisions.md` 2026-09-19).
- **Vectorised numpy only.** There are no per-dot Python loops. Neighbour forces use spatial binning shared per frame,
  and the relational forces read only the other body's centroid (O(N)). The old design doc benchmarked a naive pairwise
  (N,N,3) repulsion at 15.2 ms/frame against 0.126 ms/frame for the whole force integrator at N=500
  (`Project_context/force_architecture.md` §3, git history).
- **Point cloud rendering.** `utils/swarm.py` renders the dots as one `OpenGLPMobject` point cloud (a few draw calls)
  instead of hundreds of Manim surfaces. The docstring records "~215 fps for 400 nodes on the RTX 3090" from an earlier
  GPU-pod phase. There are two custom GLSL shader sets in `shaders/` (`soft_dot`, `lit_dot`). The soft-sprite shader is
  off by default for a measured reason (it starved the bloom pass; `config/settings.py`).
- **Colour science.** Colour transitions glide in **OKLab**, not RGB. A far hue change passes through grey, which
  stopped a green flash between orange/gold and cyan (`specs/75`, `specs/77`; `config/palette.to_oklab/from_oklab`).
  Per-dot shading (`utils/shading.py`) gives every dot a persistent "energy" (a few hot dots, most low) and live depth
  haze. This was a fix for an earlier "disco light", everything-one-flat-colour look.
- **Platform safe zones.** `utils/safe_zone_enforcer.py` keeps the action out of the top 15% (header), bottom 25%
  (captions) and right 15% (like/share buttons) of a 9:16 frame by adjusting the camera zoom.
- **Post-processing outside the engine.** `utils/post_bloom.py` runs bloom on the finished MP4 with ffmpeg: a
  bright-pass that crushes the near-black void to 0, blur, then a screen blend in planar RGB. The docstring explains
  that in YUV the screen blend tints the whole frame magenta. The voice is then muxed in; a failed mux fails the run on
  purpose, because "a silent file that looks finished is worse than an error" (`main.py`).
- **A render watchdog.** `utils/liveness.py` counts rendered frames and reports a genuine stall with a stack trace. It
  never kills a slow render on a timer.

### Measurement / QA layer (a big part of the engineering)

- `tools/replay_screenplay.py` runs the real Swarm, ForceField, Dispatcher and SafeZoneEnforcer on a fake scene with no
  renderer, about 4 s per script. For each line it measures travel, size, dot spacing, light, zoom and arrival time.
  According to `specs/83`, its numbers predict real renders at r = 0.97 (lit area, 47 lines, 5 renders).
- `tools/corpus_check.py` replays a growing corpus against the **viewer guarantees G1–G9** (`specs/83` §2): readable
  dots, a visible body (≥2.5% of the frame lit), the body comes home, the climax is the strongest picture, no
  near-black line, a calm camera, few jolts, fixed bugs stay fixed, and "no script gets worse". The corpus holds real
  runs, synthetic screenplays that pass the director's gate, "hard" sets that each press on one thing, and fresh "exam"
  sets. **`outputs/corpus/` holds 846 scripts plus a baseline.** Failures are added permanently; the corpus only grows.
- `tools/viewer_scorecard.py` scores the actual MP4 (sampled at 4 fps, 270×480): the lit share of the first frame,
  whether the voice is present, colour timing, size range, the peak's rank, focal point, dust/clutter, safe-zone
  violations. It also writes per-line frame strips for review.
- A custom Claude Code agent, `.claude/agents/match-judge.md`, grades a render blind in two stages. First it describes
  the strips without the words. Then it gets the Hindi lines and grades each line yes / partly / no. Three runs plus a
  control are used.
- Tests: 25 test files, about 8,800 lines, 180 `test_`/`check_` functions (for example `tests/test_viewer_guarantees.py`,
  `tests/test_sequence_catalogue.py`, which runs every ordered pair of the 15 moves × 3 seeds, and
  `tests/test_force_continuity.py`). Each file runs on its own. The whole suite at once runs out of memory on the
  owner's laptop.

## Tech stack (languages, frameworks, models/APIs, infra)

| Layer | Technology (from `requirements.txt` and the code) |
|---|---|
| Language | Python 3.10 (venv 3.10.11); GLSL (custom point-sprite shaders) |
| Rendering | **Manim Community Edition 0.18.1, OpenGL renderer only**; 1080×1920, 60 fps (`config/settings.py`) |
| Math / physics | NumPy (vectorised force integration), SciPy (`ndimage` for the scorecard, `linear_sum_assignment` in an older choreography helper) |
| Data validation | Pydantic 2.7 (`core_engine/force_schema.py`: `ForceScript` / `ForceBeat`) |
| LLMs | OpenAI Python SDK 2.52 with strict JSON-schema structured outputs and `reasoning_effort`. Model `gpt-5.6-sol` for writer, editor, topic check, director and critic (earlier: `gpt-5.6-terra` writer, `gpt-5.6-luna` director) |
| Voice | ElevenLabs SDK 2.60, `eleven_multilingual_v2`, convert-with-timestamps (character alignment), WAV 24 kHz. Voices auditioned: Taksh, Raju, Kanika, Ananya, Rudra, Yatin and others (`outputs/voice_audition/`) |
| Video post | ffmpeg (bloom/vignette/grain filter graph, voice mux, frame extraction for QA) |
| Config / secrets | python-dotenv; `.env` needs `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID` (`agentic/config.py` fails fast if any is missing). `.env` also has a Groq key that no code uses. |
| Infra | Renders run locally on the owner's laptop (about 6 min per video, one chained background command). An earlier phase used a rented GPU pod ("RTX 3090" in `utils/swarm.py`), retired 2026-09-17 (`docs/decisions.md`: "No GPU credits; the pod is retired"). |
| Dev workflow | Git + GitHub (`gh` CLI, stacked PRs), Claude Code as the AI pair-programmer, with a project skill (`.claude/skills/fix_session`), a custom judge agent (`.claude/agents/match-judge.md`) and a graphify knowledge graph (`graphify-out/`) |

Code size (counted from the repo, excluding venv): about 19,400 lines of production Python (agentic 4.5k, engine
core 1.9k, utils 7.6k, config 0.85k, atomic_functions 1.7k, tools 2.3k, entry points 0.6k), about 8,800 lines of tests,
332 lines of GLSL, 34 remaining specs (about 5,800 lines) and about 3,000 lines of living docs.

## Key technical decisions & tradeoffs (what was chosen, what alternatives, WHY — from decision logs/code)

1. **From shapes (nouns) to forces (verbs), mid-2026.** The first system (May–August 2026) had an LLM choose from 34
   "atomic functions" such as `Shatter()`, `Merge()` and `Orbit()`, which morphed geometry into fixed shapes. A frame
   analysis of shipped renders found that a video about weight never moved down ("nothing has ever fallen"), that
   7 of 8 palette colours were at full brightness so "heavy" was unrenderable, and that velocity was exactly zero at
   every beat boundary. The redesign doc argues: "Shape is a noun and demands interpretation; force is a verb and is
   felt directly." It replaced keyframed shapes with a persistent physics field (`Project_context/force_architecture.md`,
   git history). The old system was deleted outright on 2026-09-18, with no `_archive/` folder "(clutter Claude would
   still find)" (`docs/decisions.md`).
2. **The writer owns each line's "happening" and move** (specs/52). An earlier writer was told lines didn't need to
   describe anything physical, and 6 of 11 lines gave the body nothing to do. The fix makes the writer name, for every
   line, what happens to "you" and the move that shows it, from one shared vocabulary. Meaning still comes first: a
   version that forced a new move on every line produced poetry the owner "could not follow".
3. **An editor that judges as a first-time viewer, and "understood" must be 3/3.** Rule-based scores passed scripts
   the owner couldn't follow, so the editor never sees what the writer meant. It first writes what a stranger would
   take away (`docs/decisions.md` 2026-09-19).
4. **Keep the best draft, not the last,** and don't chase zero "flagged phrases". The critic always finds something,
   and chasing a zero threw away the best script (`EDITOR_MUST_BE_EMPTY` comment in `force_writer.py`).
5. **The director confirms rather than invents,** with at most 3 move changes, each needing a note. Paper grades and
   screens disagreed ("the paper said 8 of 10 while the screen showed 3"), so the critic now reads a code-written
   description of what actually renders, and since specs/83 the replay's measurements too.
6. **Teach the writer limits by category, not with a banned-word list.** Hindi has too many ways to say one thing, and
   pushing toward "dot words" produced abstract poetry. The categories: objects/places, other people's minds, two
   happenings in one line, two times compared (`docs/decisions.md` 2026-09-22).
7. **One body by default.** A second presence ("other people") appears only when a line is truly about someone else,
   on at most 3 lines. The owner rejected two dot types as "worst".
8. **The engine owns taste.** The director names registers and moves, and `config/palette.py` resolves the colour.
   A raw hex never comes from an LLM payload.
9. **Glide colours in OKLab.** RGB interpolation from orange to cyan passes through vivid green. OKLab passes through a
   soft grey. The chroma is also cut mid-transition for far hue changes (specs/75, 77). Cost accepted: the new colour
   looks paler for its first half second.
10. **Bloom as an ffmpeg post-pass, not in-engine.** Manim 0.18.1's OpenGL renderer has no post-FX hook, and patching it
    risked the GPU crashes seen on the pod. The post-pass has zero engine risk and is deterministic
    (`utils/post_bloom.py`).
11. **The method change (specs/83, 2026-09-23): prove it on the corpus, not two test videos.** About 50 correction
    rules had each been tuned on two scripts (jawab, waqt), and each new script broke something. Measured on 106
    scripts, only 9 passed every viewer guarantee. From then on, a change is kept only if it passes G1–G9 on the whole
    corpus and on renders of several different scripts, and no engine or agent file may name a specific script.
    `CLAUDE.md`: "If a change would help only one script, stop right there and tell the user."
12. **Measure, then choose from a table.** Many constants were set from grids of measured options, and the owner chose
    from the table. `FLOW_BASE_MAG` 2.8 was "the only value clearing both" constraints. `FADE_SECONDS` 0.6 s was "the
    longest value measured at which the line never carries more light than it began with". Dot-pressure gap 0.05 was
    chosen over 0.072 after watching six videos. Many rejected options are logged with their costs (for example a bigger
    spawn, a slower camera fit, holding opacity down after a fade).
13. **Hindi only, Devanagari only; captions added by hand.** `docs/decisions.md` 2026-08-04 and 2026-09-16.

## Hard problems solved / engineering highlights

- **Getting abstract particles to read as a specific action on a specific word.** This took the full chain: writer
  plans, director confirms, a deterministic compiler, then physics that arrives on the word. The move has to be under
  way within about 0.5 s of the line starting, and the previous move is braked in the pause between lines. The sentence
  timestamps come from ElevenLabs character alignment, so the timing is sample-accurate to the voice.
- **"The dots weld into a lump."** When the body shrinks, glowing dots merge into one blob and the picture stops
  reading as dots. The fix was a dot-size rule tied to the measured on-screen gap to the nearest neighbour, then a body
  size floor and a short-range dot pressure (specs/58, 59, 83, 85). Result on the jawab replay: lines whose dots weld
  went 6 → 0.
- **History-dependence.** "A move is not a fixed picture." The same move looks different depending on what the lines
  before it left behind. After two `gathering` lines, half the dots piled into a core the size floor couldn't open, and
  12 of 14 moves sat at the dot floor for the whole next line. It was diagnosed by replaying and changing one line at a
  time, and fixed with a local dot-to-dot pressure (specs/85, `utils/force_field.py dot_pressure`).
- **A squeeze that spreads.** The climax move (`crushed`) was the smallest picture in the video because anisotropy only
  ever pulled inward. It now pushes outward along the free axis, "pressed flat is a wide band". The peak went from
  2.29% to 3.96% of the frame and its light from 20.9 to 35.3 (specs/68).
- **The first frame has to stop the scroll.** A thin first frame was fixed by opening zoomed-in (1.1) and lit, and by
  seeding the first frame from the computed look rather than spawn leftovers. Frame-0 lit area went from 4.60% to
  8.18% (waqt) and from 5.57% to 7.99% (jawab), against a 6% target (specs/73, 78).
- **A hidden 0.33 s lag.** A shading "handoff" re-seeded itself every 2.3 s for the whole video, so every light and
  colour change reached the screen through a hidden ease. It was found by measurement and fixed so that the written
  colour equals the target on every frame (specs/79).
- **Camera axes in Manim's OpenGL renderer.** They were probed empirically (at phi 75°, theta −90°, world +X points
  at the viewer and screen-right is world −Y), and moves like swirl and flow were rebuilt on the true screen plane
  (`CLAUDE.md`, `utils/force_field.view_axis()`).
- **Building its own measurement system.** A headless replay that predicts renders (r = 0.97), an 846-script corpus,
  per-guarantee regression checks, an MP4-level scorecard and a blind judge agent. This is what turned "it looks
  better on this one video" into "it is no worse on any of 846 scripts".
- **Honest failure accounting.** `docs/mistakes_log.md` records each mistake that slipped through, why the method missed
  it, and the check that now catches it. For example, the director refusing a script was first blamed on the writer,
  and a replay proved it was an engine bug.

## Results, metrics, scale (numbers only if found in the repo)

- **Output spec:** 9:16, 1080×1920, 60 fps; 30–45 s; 8–12 lines of 5–13 words; 80 dots by default (500-node cap)
  (`config/settings.py`, `agentic/force_writer.py`, `CLAUDE.md`).
- **Line-to-picture match on the main test script (jawab):** about 3 of 10 lines shown on the first render of the new
  director. 5 of 10 after the director fixes. One render judged 2 yes / 3 partly / 5 no before the dot-readability fix.
  Later the blind critic gave 8 of 10 "yes" (render `video_20260922_0204`), and waqt passed the critic on its first
  attempt with 8 of 8 different pictures (`docs/decisions.md`, `docs/problem_scorecard.md` P22).
- **Robustness across scripts (specs/83):** before the change, 9 of 106 scripts passed every viewer guarantee. After it,
  on a final exam of 280 fresh scripts nothing was tuned on, **230/280 (82%)** passed, and 160/286 on the fixing corpus
  (`docs/mistakes_log.md`, 2026-09-24).
- **Writer quality (specs/84):** from 1 of 5 new topics passing the writer (round B) to **4 of 5**. The spec author's
  own read was about 5–6/10 → about 7–8/10 on passing scripts. Spend for that test: 190,604 OpenAI tokens.
- **Speed:** a full render takes about 6 min on the laptop. A headless replay takes about 4 s per script. The full
  corpus (846 scripts) takes about 80 min. The fast corpus subset (about 40 scripts) takes about 2.5 min.
- **Physics cost:** 0.126 ms/frame for the full force integrator at N=500, against 15.2 ms for naive pairwise repulsion
  (old design doc).
- **Typical per-video API spend (examples from logs):** ElevenLabs 528 characters (maaf) and 483 (shehar). Director
  about 22k OpenAI tokens (maaf). The writer uses about 15k–51k tokens per topic (specs/84). No dollar figures are in
  the repo on purpose: the rule is "never guess prices".
- **Latest render scorecard (maaf, `video_20260925_0134`):** G1, G3, G4 (peak ranked 1st of 11 by area), G5, G6 and G7
  pass. G2 fails on one line (2.32% against 2.5%). G8 fails (dot centres past the safe band on 5.6% of frames; slowest
  colour change 0.67 s against 0.6 s). Frame 0 is 8.30% lit. The voice is 43.28 s and matches the video.
- **Process scale:** 333 commits on the current branch (336 in total) between 2026-05-15 and 2026-09-25, 43 PRs,
  96 remote branches archived as 92 tags, about 85 numbered specs over the project's life (34 remain in `specs/`), and
  60+ rendered videos in `outputs/` (3.1 GB, not in git).

## Current status & timeline (done / in progress / planned; dates from git/docs)

| Period | What happened (git + `docs/branch_archive.md`) |
|---|---|
| 2026-05-15 → 06-03 | Repo created. Base setup, phases 2–4: JSON schema, timeline orchestrator, dispatcher, master controller, output management, safe-zone monitor, 500-node cap, atomic-function batches (CHANGELOG v0.5.0 on 2026-05-22: 23 functions). Switch to the OpenGL renderer, GPU testing and polishing. |
| 2026-06-29 → 08-29 | The agentic layer (LLM writer, voice, choreographer), "fixing_things" iterations on the shape path, bloom, then the **force engine** (relational forces, cohesion, a second presence) and the "nebula look" (`final_update`), which the owner rejected. |
| 2026-09-13 → 09-18 | The force engine with the older look restored. Viewer scorecard tool, one-problem-per-session fix loop (sessions S1–S27), the pod retired and renders moved to the laptop (09-17). **Old system deleted** (09-18). |
| 2026-09-19 → 09-22 | Root-cause reports (writer/director, visual engine). A new writer (specs/52), director (specs/53), and engine sub-steps (specs/54–60: the ruler, arrival, frame, dots that read, ten lines/ten pictures). The owner: "yaha humara system almost ready hogya tha" (branch `fix/46`). |
| 2026-09-22 → 09-23 | Render-by-render fixes (specs/66–82): fades, climax, first frame, OKLab colour, motifs, arc. |
| 2026-09-23 → 09-24 | **Method change (specs/83):** viewer guarantees on a 100+ → 846-script corpus, a final exam, and a mistakes log. Writer fixes (round B) and the writer's "depth" (specs/84, prompt tuning only). Branch cleanup on 2026-09-24: 6 branches kept, the rest archived as tags. |
| 2026-09-24 → 09-25 | specs/85 (dots never pile up; `fix/76`). New renders of maaf and raat. Voice audition: Kanika chosen by measurement (`.env` currently has Raju). |

**Status (per `docs/next_session.md`, 2026-09-25):** in active development, not finished. The current branch is
`fix/76-dots-never-pile-up`: its code is done but its tests are unfinished, and it is stacked on unmerged `fix/75` and
`fix/74`. **Nothing has been merged into `main` since 2026-05-15**; main holds essentially only a `.gitignore`. All
work lives on the stacked fix branches.

**Planned next (the owner's order: fix everything, then test once, then one full corpus run):**
- The look: "the dots look flat" (L1: no bright core or rim per dot); making each line independent of the lines before
  it; contrast between neighbouring lines; the energy arc; late colour; glow in the caption zone.
- The writer: pacing per voice (it plans 3.3 words/s, Kanika speaks about 2.5); an editor stricter than it is today.
- The director: full strength on nearly every line, so the peak can't stand out; too many accents.
- The owner's calls: the final voice, and whether the `fix/75` writer goes forward.

## Limitations & known issues

- **Not finished and not in production.** No video in the repo is marked as published. The main branch is empty, and
  three fix branches are unmerged with no PR open.
- **It doesn't pass all its own guarantees yet.** The latest maaf render fails G2 on one line and G8 (safe band, colour
  timing). The fresh-script exam passed 82%, not 100%.
- **Visual quality gaps the owner named:** dots look flat and alike (L1); neighbouring lines can look alike (N1); a weak
  build to the peak (N2); no whole-body "return" move (N4); after a very dark fade two lines can be nearly empty (N7);
  "brings you back" reads as closing (N8) (`docs/problem_scorecard.md`).
- **The headless predictor has drifted.** It correlates at r 0.86 with the newest renders (0.95 is required), so corpus
  size numbers are no longer fully trusted without renders.
- **Hindi only**, one narrator, captions added by hand, no automatic publishing.
- **Hardware limits:** renders take about 6 min each on a laptop, the full test suite can't run in one go (out of
  memory), and the full corpus takes about 80 minutes.
- **Paid APIs** (OpenAI + ElevenLabs) are needed for new scripts. Stages 3–4 are free and repeatable.
- **Legacy code still imported:** `atomic_functions/base.py`, `connection.py` and several `utils/` layers from the old
  engine (`docs/how_it_works.md` §5). There is also an open camera-convention inconsistency (P26: `camera_compat` uses
  the Cairo formula, 90° off).

## Demo assets (file paths to videos/images/screenshots/sample outputs; GitHub URL if any)

**GitHub:** `https://github.com/Hacke2367/CONTENT_2`. **This repo is PRIVATE** (checked with `gh repo view`) and its
`main` branch is essentially empty. The newest work is on `fix/76-dots-never-pile-up`.

**Best candidate videos (finished, with voice, 1080×1920 60 fps):**
- `C:\Project_Dmc\outputs\review_fix76\maaf_3_gap005.mp4` is the newest and strongest example: "not being able to
  forgive", 11 lines, 43 s, Kanika voice, peak ranked 1st.
- `C:\Project_Dmc\outputs\review_fix76\raat_3_gap005.mp4`: "scrolling the phone for hours before sleep", 11 lines,
  39 s.
- `C:\Project_Dmc\outputs\video_20260923_1840\dmc_render_final.mp4`: jawab, "the habit of replying late", 10 lines,
  38 s.
- `C:\Project_Dmc\outputs\video_20260923_1803\dmc_render_final.mp4`: waqt (time passing / birthdays), 8 lines, 31 s.
- `C:\Project_Dmc\outputs\video_20260922_0204\dmc_render_final.mp4`: the jawab render from the owner's "system almost
  ready" point.
- `C:\Project_Dmc\outputs\video_20260920_0445\dmc_render_final.mp4`: **the move catalogue**, 12 moves in a row, 36 s.
  A good "vocabulary" explainer clip.
- Before/after pairs for a technical story: `outputs\review_fix76\maaf_1_before.mp4` vs `maaf_3_gap005.mp4`, and
  `raat_1_before.mp4` vs `raat_3_gap005.mp4`.
- The last render of the old system, for an evolution story: `outputs\video_20260918_2302\dmc_render_final.mp4`.
- The render folders (`outputs\video_*\`) also hold a raw `dmc_render.mp4` without bloom/voice. There are 65
  `dmc_render_final.mp4` files in total.

**Images:**
- `outputs\video_<stamp>\scorecard\beats.png`: one frame per line, a contact sheet.
- `outputs\video_<stamp>\scorecard\match_test\beat_NN.png`: a 10-frame strip per spoken line. Good for showing
  "words → motion" side by side with the Hindi line.

**Sample text artefacts:**
- `outputs\s84_maaf\writer_plan.json`, `narration.txt`, `screenplay.txt`: a readable screenplay with per-line move,
  light and camera choices.
- `outputs\w30v4_jawab\` holds the main test script, with several screenplay/force-script versions.
- `outputs\video_20260925_0134\scorecard\report.md`: a full viewer-guarantee report.

**Audio:** `outputs\voice_audition\*.wav`, eight voice samples used to pick the narrator.

**Docs worth excerpting:** `docs\how_it_works.md` (a plain explainer), `docs\decisions.md`, `docs\mistakes_log.md`,
`specs\83_the_engine_guarantees_what_a_viewer_sees.md`.

## Why this impresses a recruiter (2 angles: non-technical impact, technical depth)

**Non-technical impact.**
- It automates a whole creative production chain end to end: topic → script → voice → animated video, in one
  language-specific pipeline (Hindi), for real platforms (Shorts, Reels, TikTok), with their UI safe zones built in.
- It is product-minded: the viewer's experience is the only yardstick. `CLAUDE.md`: "A metric that passed never
  overrides what the viewer would see." Every render is watched line by line before any number is reported.
- The discipline is visible: every decision is written down with its reason and date, costs are reported after every
  paid step, nothing merges without sign-off, and mistakes are logged with the fix to the *process*, not just the
  symptom.

**Technical depth.**
- A multi-agent LLM system (writer, editor, topic check, director, blind critic) with strict JSON schemas, code gates
  between agents, best-of-N selection and targeted revision. The agents are tied to a deterministic compiler and a
  physics simulation, so the LLMs choose *meaning* and code guarantees *behaviour*.
- A custom real-time particle physics engine on Manim/OpenGL: vectorised numpy, O(N) neighbour forces, viscous (not
  flocking) dynamics, glided parameters with inter-line braking, OKLab colour, per-dot shading and an ffmpeg bloom
  pipeline.
- Evaluation engineering: a headless replay that predicts renders (r = 0.97), an 846-script regression corpus with
  explicit viewer guarantees and a "no script gets worse" rule, pixel-level MP4 scoring, and a blind judge agent. This
  is the same kind of eval-driven development used for ML systems, applied to a creative pipeline.
- An architecture pivot driven by data: measured frame analysis showed the shape-based design couldn't express
  emotion, which led to a rebuild as a force-based design.

## Likely recruiter Q&A (8-15 question/answer pairs the chat agent should be able to answer, grounded in the repo)

1. **Q: What is Project DMC in one sentence?**
   A: An automated content factory that turns a topic into a 30–45 s Hindi-narrated vertical video, in which one body of
   glowing dots acts out each spoken line at the moment it is spoken (`docs/project_end_goal.md`).

2. **Q: Why dots instead of stock footage or AI video generation?**
   A: The design is deliberately abstract: "abstract glowing dots only", no literal shapes, no clip-art (`CLAUDE.md`).
   The idea is that emotion is carried by motion, light and colour (sinking, pressing, opening, fading) rather than by
   literal images. The repo doesn't compare this with AI video generators; that choice is in the original blueprint.

3. **Q: How does the system know what the dots should do for each line?**
   A: The writer LLM plans, for every line, what happens to "you" and picks one of 15 named moves (for example `heavy`,
   `opening`, `dissolving`). The director LLM confirms it and sets colour mood, strength, peak and camera. A
   deterministic compiler turns the move into force parameters for the physics engine (`config/gestures.py`,
   `agentic/screenplay_compiler.py`).

4. **Q: How is the animation synced to the voice?**
   A: ElevenLabs returns character-level timestamps with the audio. A segmenter splits the audio into one beat per
   written line (it checks the count and the text match exactly), and each beat's forces start on the line's first
   word. The move is under way within about 0.5 s, and the previous move is braked in the pause.

5. **Q: Which AI models/APIs does it use?**
   A: OpenAI (`gpt-5.6-sol` for writer, editor, director and critic, with strict JSON-schema outputs and high
   reasoning effort) and ElevenLabs `eleven_multilingual_v2` for the Hindi voice. The render and physics steps use no
   AI and cost nothing.

6. **Q: What was the hardest technical problem?**
   A: Making it work for *any* script, not just the test scripts. A move looks different depending on what the lines
   before it left behind, and about 50 hand-tuned correction rules broke on new scripts: only 9 of 106 scripts passed
   every viewer guarantee. The fix was methodological: explicit viewer guarantees measured headlessly on a growing
   corpus (now 846 scripts), plus a final exam on fresh scripts. 82% of those passed (specs/83).

7. **Q: How do you test something visual?**
   A: At three levels. A headless replay of the real engine measures every line in about 4 s and predicts renders at
   r = 0.97. A corpus check enforces guarantees G1–G9 with "no script gets worse". A scorecard measures the finished MP4
   pixels. On top of that, a blind judge agent grades frame strips against the Hindi lines, and the owner watches every
   render. There are 25 test files with about 180 check functions.

8. **Q: Did the architecture change over time?**
   A: Yes, fundamentally. It started with 34 "atomic functions" that morphed geometry into shapes. Frame analysis showed
   this couldn't express emotion: nothing ever fell, there was no dim register, and motion stopped dead at each beat.
   It was rebuilt as a force-based physics engine, and the old system was deleted on 2026-09-18.

9. **Q: Is it finished? Can I see it live?**
   A: It's in active development. The owner's latest session (2026-09-25) lists fixes still to do: the dot look, the
   energy arc, writer pacing per voice. The GitHub repo is private, and nothing has been merged into main yet. Rendered
   sample videos exist locally (see Demo assets).

10. **Q: How long does one video take and what does it cost?**
    A: A render takes about 6 minutes on the owner's laptop. API usage per video in the logs is roughly 500
    ElevenLabs characters, about 15–50k OpenAI tokens for the writer and about 22k for the director. The project
    deliberately doesn't record dollar prices ("never guess prices").

11. **Q: What role did AI coding assistants play?**
    A: The project was built with Claude Code as a pair-programmer. About 246 of 333 commits carry a Claude co-author
    trailer. The owner set the product goals, approved every spec before code, judged every render and made the
    decisions (quoted in `docs/decisions.md`). Custom tooling was built for the workflow: a `/fix_session` skill and a
    `match-judge` agent.

12. **Q: How do you prevent the LLM from producing bad scripts?**
    A: There are layered checks. A code gate rejects anything countable: line count, words per line, duration,
    characters the voice can't align, hook wording, move variety. An LLM editor that never sees the writer's intent
    must fully understand the script on one hearing and score 2+ on craft and "depth" (a thought, not a tip). The best
    draft is kept, and when only a few lines fail, only those lines are rewritten.

13. **Q: What did you learn / what would you do differently?**
    A: From `docs/mistakes_log.md` and `docs/next_session.md`: judge on the video, not the tests ("a headless measure
    can pass what a video fails"); replay and change one line before naming a cause; re-measure writer rules when the
    engine changes; and fix what the viewer sees first. A week of motion fixes didn't change how a single dot looks.

14. **Q: How big is the codebase?**
    A: About 19k lines of production Python, about 8.8k lines of tests, custom GLSL shaders, 34 current specs and a set
    of living docs (decisions, scorecard, branch log, mistakes log), built over about 4.5 months (May–Sept 2026).

## Open questions for the owner (things you couldn't determine)

1. **Has any DMC video been published** on YouTube Shorts, Reels or TikTok? Are there view/engagement numbers or
   channel links? Nothing in the repo says so.
2. **Can the repo or a demo be shared?** `Hacke2367/CONTENT_2` is private and `main` is essentially empty. Should the
   portfolio link a public mirror, a demo video only, or nothing?
3. **Which video is the "hero" demo?** The best candidate is `outputs/review_fix76/maaf_3_gap005.mp4`, but there is no
   exported/trimmed portfolio version or thumbnail. Should one be made, maybe with English subtitles for non-Hindi
   recruiters?
4. **What does "fabe report" / branch `fabe_model/report` (2026-06-29) refer to?** It isn't described in the docs.
5. **Laptop hardware.** Renders run locally, but the GPU/CPU specs aren't recorded. Which GPU pod provider was used
   before 2026-09-17?
6. **Which voice is final:** Kanika (chosen by measurement), Raju (currently in `.env`), or Taksh (in the end-goal doc)?
7. **Should the owner's own role be phrased as "architect/product owner directing an AI coding agent"?** Most commits
   are Claude co-authored, and how the portfolio should describe authorship is the owner's call.
8. **Are there actual dollar costs per video** the owner is willing to share? The repo records only tokens and
   characters.
9. **Is the project still going after `fix/76`,** or is it paused? What's the target date for a first published video?
10. **The model name `gpt-5.6-sol`:** confirm this is the exact public model name to cite. It appears as-is in the code.
