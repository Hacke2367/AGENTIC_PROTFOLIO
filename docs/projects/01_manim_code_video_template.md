# AutoShorts: AI-to-Video Shorts Engine (repo folder: `manim_code_video_template`)

> **Naming note:** the local folder is `C:\MANIM_VIDEOS_CODE_TEMPALTE` (the typo is in the folder name). Inside the repo the project is called **AutoShorts** (`CLAUDE.md`, `OVERVIEW.md`, `RUNBOOK.md`). The GitHub repo is **`Hacke2367/Auto_shorts_engine_1`**. The on-screen brand used by the video intros is **"BIGDATA LEAK"** (`src/templates/Bar_chart/bar_chart.py`, `IntroManager.play_intro(... brand_title="BIGDATA LEAK", brand_sub="SYSTEM BREACH DETECTED")`).
>
> **Related folder:** `C:\manim_pracstice` holds one file, `manim.py`, dated 17–18 Dec 2025. It is a small Manim practice exercise (Circle → Square → Triangle `Transform`). It looks like the owner's Manim warm-up about a month before this repo started (repo created 17 Jan 2026). It is not part of the project.

---

## One-line pitch (plain language, for a non-technical recruiter)

A software "video factory": give it a topic (or let it find a trending one), and it researches real data on the web, writes a punchy Hindi-English voice-over script with AI, records the narration with an AI voice, and renders a finished, animated, vertical (9:16) data-infographic video ready for YouTube Shorts or Reels. There is no video editor involved; everything is generated in code.

---

## Problem & who it's for

**Problem.** "Faceless" data/infographic Shorts (rankings, "X vs Y" comparisons, market-share breakdowns, maps, "race" charts) are a popular format. Making each one by hand is slow: research the numbers, write a script, record audio, animate the charts in After Effects or similar, sync every animation to the voice, and add sound effects, music and captions. That doesn't scale to publishing many videos.

**Goal (from the repo's own docs).** "To generate premium, high-retention, 'faceless' infographic shorts in bulk" (`technical_refactor_document.md`). The philosophy is written as **"Build > Buy/Wrapper"**: deep custom engineering instead of a thin wrapper around a video API, with "pixel-perfect sync."

**Who it's for.**
- Primarily the owner, as the engine behind a planned data-Shorts YouTube channel. `docs/future_feature_roadmap.md` (Aug 2026) says the channel "isn't launched" yet and parks later features "until the channel is live and generating data."
- The architecture docs also describe a possible future as a multi-tenant "content factory" SaaS (Pillar 4 in `docs/future_feature_roadmap.md`). This is explicitly parked, not built.

**Audience of the videos.** Hindi/English ("Hinglish") speaking short-form viewers. Scripts are written in Hinglish persona voices (for example "savage_roast_master"), and the TTS defaults are tuned "for natural, punchy Hinglish narration" (`src/agents/core/config.py`, `TTSConfig`).

---

## What it does (user-facing features / workflow)

The system has two halves that can run independently. They share a job folder (`jobs/<job_id>/`) as the hand-off point.

### A. The AI content pipeline (Phases 1–3 + Handoff)
Driven by a master CLI: `python -m src.cli.autoshorts <command>` (`src/cli/autoshorts.py`). Subcommands: `new`, `phase1-discover`, `phase1-approve`, `phase1-extract`, `phase2`, `repair`, `phase3`, `handoff`, `render`, `run`.

1. **Phase 1A: Topic discovery (auto mode).** An LLM brainstorms topic ideas, seeded with live trend context. Ideas already produced or rejected are filtered out using a topic archive. Each surviving idea is checked for real published data with Tavily web search. An LLM then scores every candidate on hook potential, novelty, visual fit, data feasibility and freshness. Candidates are ranked and saved to `candidates.json`. A **human approves** one candidate (`phase1-approve`), so this step is semi-automatic by design.
2. **Phase 1B: Data extraction.** For the approved topic and a chosen chart template, the system searches and scrapes sources with Tavily and asks the LLM to extract a structured dataset that matches the template's schema. The result is saved as `data/<template>_dataset.json` with an audit trail.
3. **Phase 2: Script writing.** Python first computes a per-segment "character budget" from the template's minimum animation times and the voice's speaking rate. The LLM then writes a tagged, segmented monologue (HOOK, SETUP, ITEM_1…, WINNER, OUTRO) in a chosen persona. Segments that are too long or too short get targeted rewrites. An optional **"script doctor"** pass then polishes the whole script into one flowing performance. The doctor's output is thrown away if it breaks any rule.
4. **Phase 3: Voice.** Each segment is synthesized with ElevenLabs TTS (`eleven_multilingual_v2` by default). Silence is trimmed, real durations are measured, and audio files are packaged. A `repair` command loops Phase 2 → Phase 3 when audio comes out too short ("UnderRunError").
5. **Handoff.** Converts the pipeline's internal files into the exact `job.json` format the renderer expects (`src/agents/final_handoff/handoff.py`).

### B. The video renderer (Phase 4)
`python main.py --job jobs/<id> --template <name> -q h` (`main.py`)
- Validates `job.json` with Pydantic.
- Trims the voice clips **before** rendering and rewrites the timeline to their real lengths.
- Renders the chosen Manim animation template at 1080×1920.
- Builds the audio: concatenated voice, a sound-effects track built from timestamps the animation logged, and optional background music. Music and SFX are "ducked" under the voice.
- Muxes the final `output/final.mp4`.
- Optionally generates styled subtitles (ASS format; plain / word-reveal / karaoke modes) and burns them in (`final_captioned.mp4`).

### Seven animation templates
Registered in `templates.json` (merged over a built-in map in `main.py`):

| Key | Scene class | What it shows |
|---|---|---|
| `bar_chart` | `BarChartTemplate` | Ranked horizontal bars with winner banner |
| `butterfly_chart` | `ButterflyChart` | Two-sided head-to-head metric comparison |
| `scan_race` | `CinematicLineRace` | Animated line "race" over time with a live ranking HUD |
| `geo_universal` | `GeoUniversalMap` | World/US map with nodes, alliances, choropleth-style data |
| `sort_card` | `SortCardTribunalFinal` | Items sorted into tiers ("tribunal") |
| `vs_card` | `VsCardFinal` | Multi-round "A vs B" card battle with photos |
| `donut_breakdown` | `DonutBreakdownFinal` | Market-share donut with callout chips |

All share one visual identity: a dark "cyber / data-leak" look with neon cyan and pink, glassmorphism, a HUD with REC dot and timer, a "CONFIDENTIAL // VERIFIED" footer, and floating particles (`src/utils.py`, `src/config.py`).

### Operations tooling
- `render_batch.py`: renders many jobs in parallel. Worker count is capped by free RAM.
- `tools/runpod_render.ps1`, `tools/runpod_bootstrap.sh`, `tools/runpod_quickstart.sh`: ship code and jobs to a many-core RunPod CPU pod, render there, and pull the videos back.
- `tools/audio_duration(s).py`: checks audio durations against the timeline.
- `tools/cost_report.py`: LLM spend dashboard across all jobs.
- `scripts/replay_harness.py` + `scripts/compare_report.py`: replay archived inputs against new LLM settings to validate a model migration cheaply.
- `scripts/llm_smoke.py`: live LLM smoke test.

---

## How it works (architecture, pipeline, data flow)

### High-level architecture

```
                    ┌──────────────────────── DATA PIPELINE (src/agents, src/cli) ────────────────────────┐
 topic / niche ───► │ Phase 1A Discovery                     Phase 1B Extraction (LangGraph)              │
                    │  LLM ideation (2.5x over-provision)     search ─► scrape ─► LLM extract             │
                    │  ─► archive filter (TTL memory)          (Tavily)  (Tavily)  (strict schema)        │
                    │  ─► Tavily evidence check                  ▲ retry search if 0 URLs (max 2)         │
                    │  ─► LLM scoring (parallel, rate-limited)                                            │
                    │  ─► data-feasibility gate ─► ranked candidates.json ─► HUMAN APPROVAL               │
                    │                                                                                     │
                    │ Phase 2 Scripting                        Phase 3 Audio                              │
                    │  Python timing plan (chars/sec budget)   ElevenLabs TTS (async, bounded concurrency)│
                    │  ─► LLM draft (persona, Hinglish)        ─► silence trim ─► measure ─► package      │
                    │  ─► rewrite loop for failing segments    ◄── `repair` loop on UnderRunError         │
                    │  ─► "script doctor" (guarded)                                                       │
                    │                                  Final Handoff ─► job.json (renderer schema)        │
                    └────────────────────────────────────────────┬────────────────────────────────────────┘
                                                                 │  jobs/<job_id>/  (the contract)
                                                                 ▼   job.json · script/ · audio/ · data/
                    ┌──────────────────────── VIDEO RENDERER (main.py, src/templates, src/sync …) ─────────┐
                    │ 1. Pydantic-validate job.json                                                        │
                    │ 2. Normalize voice FIRST: trim silence, rewrite timeline to real durations           │
                    │ 3. Manim render (subprocess) of the template Scene                                   │
                    │      Scene reads timeline ─► Timeline.schedule() absolute-clock anchors              │
                    │      animations + sync_hold()/hold_breathing() "alive" holds                         │
                    │      SFXEngine writes output/sfx_marks.json (timestamps only, no audio)              │
                    │ 4. FFmpeg: concat voice ─► build SFX track (adelay+amix) ─► optional BGM             │
                    │ 5. FFmpeg mix: voice compressor, sidechain-ducked SFX/BGM, limiter                   │
                    │ 6. FFmpeg mux: video copy + audio, apad + -shortest (video decides length)           │
                    │ 7. Captions (optional): script ─► timeline ─► ASS styles ─► burn-in                  │
                    └──────────────────────────────────────────────────────────────────► output/final.mp4 ┘
```

### The `jobs/<id>/` contract
The one source of truth that both halves agree on (`CLAUDE.md`, "Architecture: The jobs/<id>/ Contract"):
```
jobs/<job_id>/
  job.json               # template_id, video w/h, audio.segments + audio.order, timeline{seg: seconds},
                         # gains, sfx, bgm, mix (preset/ducking), captions config
  script/script.json     # per-segment voice lines (Phase 2)
  audio/                 # per-segment mp3/wav (+ audio/_raw originals after normalization)
  data/                  # CSV/JSON dataset (Phase 1B)
  output/                # final.mp4, subtitles.ass, final_captioned.mp4, sfx_marks.json, renders/ history
  media/                 # Manim intermediates
  logs/cost.jsonl        # per-call LLM cost records
  .pipeline_state.json   # idempotency flags per phase step (atomic writes)
  discovery/, attempts/  # auto-mode only
```
Invariants the renderer relies on: `audio.segments[].name`, `audio.order[]`, `timeline` keys and `script.json` segment names must all line up. The docs call drift between these lists "the most common source of render failures."

### Data pipeline internals (`src/agents/`)
- **`core/llm_client.py`: the single LLM entry point.** `call_llm` / `call_llm_raw` sit on top of an **OpenAI Responses API adapter** and a **Gemini adapter**. The provider is chosen **per route** by `PhaseModel.provider`. The module exists to contain two response-shape traps:
  - OpenAI puts a *reasoning* item first in `output[]`.
  - Gemini can split text across several parts, some of which are "thought" parts.

  Both adapters scan for the right item and **raise instead of returning `""`**, "because a silent empty string downstream becomes an empty script rather than a loud error."
- **`core/config.py`** has two strictly separated layers:
  - `SystemSettings`: **secrets only**, from `.env` (`TAVILY_API_KEY` required; `OPENAI_API_KEY`; optional `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`).
  - `AppConfig` / `APP_CONFIG`: **all operational settings in code**, i.e. per-route model routing, reasoning effort, verbosity, RPM limit, retry profiles, timeouts, TTS voice settings, the feasibility gate and authority domains.
- **Six LLM routes:** `discovery_ideation`, `discovery_scoring`, `extraction`, `scripting_draft`, `scripting_rewrite`, `scripting_doctor`. All six are configured to OpenAI **`gpt-5.6-luna`** with different `reasoning_effort` settings: low / low / medium / medium / low / high. A Gemini route table (`gemini-2.5-flash` / `gemini-2.5-pro`) is kept for A/B tests or rollback. A run-wide `--llm-provider gemini` flag overrides everything.
- **`core/retry.py` + tenacity:** separate retry profiles for normal network errors, 429 rate limits (long backoff), and "patient" profiles for the calls a whole run depends on (ideation, extraction, scripting: 6 attempts, 4–45 s waits).
- **`core/rate_limiter.py`:** token bucket plus circuit breaker. **`core/cost_tracker.py`:** provider-neutral cost accounting, one JSONL file per run. **`core/job_manager.py`:** creates the folder tree and writes state atomically (temp file → `os.replace`), tolerating a corrupted state file. **`core/llm_schemas.py`:** strict Structured Outputs JSON schemas for the three Phase 1 JSON routes.
- **`phase1_discovery/`:** `discovery_runner.py` (idea-first flow, feasibility gate), `scourer.py` (Tavily trend context + evidence validation + dedupe), `candidate_score.py` (concurrent LLM scoring), `archive_manager.py` (topic memory with **produced = 60-day cooldown, rejected = 14-day cooldown, saved_queue = reusable**, atomic writes, schema migration).
- **`phase1_extraction/graph.py`:** a **LangGraph `StateGraph`**: `START → search → (retry search if 0 URLs, max 2) → scrape → extract → END`. It reuses "seed URLs" that discovery already proved contain data, so the first attempt doesn't search again from scratch.
- **`phase2_scripting/`:**
  - `timing.py` does "all timing math" from YAML registries (`.agent/context/template_timing_registry.yaml` gives each template's minimum natural duration per tag; `voice_profiles.yaml` gives `voice_cps = 20` characters per second).
  - `llm_writer.py` handles draft → rewrite loop → script doctor. `xml_parser.py` parses tagged output.
  - `num_normalizer.py` converts numbers to spoken Hinglish, e.g. 14.3 % → "chaudah point teen percent", 2,500,000 → "do lakh pachaas hajar" (sic, as written in the module docstring; mathematically 2,500,000 is "pachchees lakh", so the example may be a doc typo).
- **`phase3_audio/`:** `tts_client.py` (async ElevenLabs with 429/5xx handling), `trimming.py` (threshold-based silence trim with a 40 ms lead pad, a 200 ms trail pad, and internal pauses capped at 260 ms), `duration.py`, `packager.py` (atomic writes), `offline_e2e.py` (runs without the TTS API).
- **Prompt/persona assets** live in `.agent/context/`: personas (`savage_roast_master`, `hyper_analyst`, `witty_strategist`) with system prompts, `commentary_mode.md` (a live sports-commentator style for the continuous `scan_race` template), `scoring_rubric.md`, `archive_policy.md`, `template_visual_rules.md`, and `master_pipeline_edd_v6.md` (the pipeline design doc).

### Renderer internals
- **`main.py`** (~1,150 lines): template registry loading, Pydantic validation (`src/sync/job_config.py`), pre-render voice normalization (`src/sync/audio_normalize.py`), the Manim subprocess (`--disable_caching`, with `JOB_JSON_PATH`/`JOB_DIR` env vars), then FFmpeg stages:
  - `concat_audio_ffmpeg`
  - `build_sfx_mix_ffmpeg` (`adelay` + `volume` per event + `amix`)
  - `build_bgm_track_ffmpeg`
  - `mix_voice_sfx_bgm_ffmpeg` (voice `acompressor`; `sidechaincompress` ducking of SFX/BGM keyed on the voice; "punchy"/"balanced" presets; light/medium/strong duck amounts; `alimiter`)
  - `mux_av_ffmpeg`
- **`src/sync/`:**
  - `timeline.py`: `Timeline` budgets per segment, plus **`schedule()` / `target_elapsed()`** for drift-free absolute-clock anchoring, plus `numbered_segments()`.
  - `retention_base.py`: `hold_breathing`, `sync_hold`, `banner_scan_hold`.
  - `retention_accents.py`: one idle-animation accent per template.
  - `audio_trim.py`: the single shared silence-trim filter.
  - `audio_normalize.py`, `job.py`, `job_config.py`.
- **`src/sfx/`:** `engine.py` (`SFXEngine.mark("scan_tick")` records scene time + event into `sfx_marks.json`) and `registry.py` (event key → WAV variants + default volume; 14 WAVs in `assets/sfx/`).
- **`src/captions/`:** `pipeline.py`, `script_loader.py`, `timeline_resolver.py`, `styles.py` (`modern_clean`, `modern_premium`), `ass_renderer.py` (plain / reveal_words / karaoke), `burn_in.py`, `aligner.py` (equal-split word timing). `translator.py` is a stub.
- **`src/utils.py` / `src/config.py`:** the shared brand layer: `Brand`/`Theme` palette, safe-frame helpers, `IntroManager`, `get_cinematic_overlay` (HUD/vignette), `make_floating_particles`, `add_cinematic_background` (gradient atmosphere), `build_result_banner` (shared end card). Fonts are registered through `manimpango` so titles don't silently fall back to a default font (bundled Montserrat, Space Grotesk, Anton).
- **Frame:** 1080×1920 pixels, Manim frame 9 × 16 units (`src/config.py`).

---

## Tech stack

| Area | Technology |
|---|---|
| Language | Python (docs say 3.11+; the render lock file notes the laptop runs 3.10.11) |
| Animation / rendering | **Manim Community** (0.19.1 pinned for rendering), Cairo / Pango / ManimPango, pycairo, skia-pathops, `av` |
| Audio/video processing | **FFmpeg / ffprobe** (filter graphs: concat, silenceremove-style trim, adelay, amix, acompressor, sidechaincompress, alimiter, apad), **pydub** |
| LLMs | **OpenAI Responses API** (all routes set to `gpt-5.6-luna` in the repo config; `gpt-5.6-terra` named as the escalation tier), **Google Gemini** (`gemini-2.5-flash` / `-pro`) as a per-route secondary / A/B provider |
| Web research | **Tavily** search and extract APIs |
| Text-to-speech | **ElevenLabs** (`eleven_multilingual_v2`, tuned voice_settings) |
| Orchestration | **LangGraph** (extraction state machine), asyncio + **aiohttp**, **tenacity** retries |
| Data / validation | **Pydantic v2**, pydantic-settings, pandas, numpy, PyYAML |
| Subtitles | ASS subtitle generation + FFmpeg burn-in |
| Infra | Local Windows laptop; **RunPod CPU pods** over SSH for parallel batch renders (network-volume bootstrap, exact-pinned `requirements-render.txt`, fonts shipped with the bundle) |
| Testing | pytest with fakes and fixtures (fake LLM, fake TTS, dummy Phase 1 outputs), offline end-to-end mode, request-snapshot tests, replay harness |
| Dev tooling | Git/GitHub, PyCharm (`.idea`), AI coding agents: Codex (`CHANGELOG_CODEX.md`, `AGENTS.md`) and Claude Code (`CLAUDE.md`, co-authored commits), graphify code knowledge graph (`graphify-out/`) |

---

## Key technical decisions & tradeoffs

1. **Split the system into two halves joined by a filesystem contract (`jobs/<id>/`)** rather than one monolith.
   *Why:* the renderer "only needs a fully-formed `jobs/<id>/` directory; how that directory got there (manual or pipeline) does not matter" (`CLAUDE.md`). Hand-made jobs and AI-generated jobs render the same way, each half is testable alone, and the roadmap notes the contract "maps almost 1:1 onto a job-queue architecture" (S3 for artifacts, Postgres for state) if it ever becomes a service.
   *Tradeoff:* four name lists (segments, order, timeline, script) must stay in sync by convention. This caused real bugs (see Hard problems).

2. **Code-driven animation with Manim instead of video-editor templates.** The repo's stated philosophy is "Build > Buy/Wrapper … Custom Math > Libraries" (`technical_refactor_document.md`). For example, labels use custom 2D bounding-box repulsion and the map uses its own lat/lon coordinate table (`src/geo_data/map_coords.py`) instead of heavy GIS dependencies.
   *Tradeoff:* Manim's Cairo renderer is single-threaded, CPU-bound and memory-hungry (~2–2.5 GB per render at 1080×1920, per `render_batch.py`).

3. **The animation engine never plays audio. It writes SFX *timestamps* instead.** Templates call `sfx.mark("impact_soft")`, which records the scene clock into `sfx_marks.json`. FFmpeg later places each sound with `adelay` and mixes them. This keeps rendering deterministic and lets the audio mix (gains, ducking, presets) change without re-rendering.

4. **Timing comes from the narration, not hardcoded `run_time`s.** Animations are sized as fractions of each segment's real audio duration. The "delta-time" rule measures `self.time - t0` per segment. Later came **absolute-clock anchoring**: `Timeline.schedule(order)` precomputes each segment's absolute end time, and `sync_hold()` waits until the scene clock reaches it. The code explains why: per-segment accounting "drifts when a template plays animations that escape its accounting (intros, inter-segment transitions) … any overrun is absorbed at the next boundary instead of accumulating" (`src/sync/timeline.py`).

5. **"Alive" holds instead of frozen frames.** When an animation finishes before its narration does, `hold_breathing()` fills the gap with subtle layers: a breathing glow ring on the focus object, a Reels-style progress tick, an optional key-phrase lower-third, and a per-template accent. Each layer is independently `try/except`-wrapped with LIFO cleanup, "so a failure in one never breaks the hold" (`src/sync/retention_base.py`). The aim is viewer retention in short-form video.

6. **Trim the audio *before* rendering, and let the video decide the final length.** See Hard problems #1. The mux uses `apad` + `-shortest` so "`-shortest` can only ever land on the video's own end" (`main.py`, `mux_av_ffmpeg`).

7. **LLM provider migration from Gemini to OpenAI, with "effort, not model tier" as the quality dial.** Every route runs the cheaper `gpt-5.6-luna`. Quality is raised by walking `reasoning_effort` (high → xhigh) before switching to the pricier `gpt-5.6-terra`. The config's reasoning: luna's output price ($1.20/1M, as noted in the config) "buys roughly 8x more reasoning than gemini-2.5-pro's ($10.00/1M) at the same spend", and "a single terra doctor call costs more than an entire luna Phase 2 run" (`src/agents/core/config.py`, `LLMConfig`). Gemini stays available per route for A/B tests or rollback. The migration was validated with a **replay harness**: archived Gemini-era inputs are fed to the new routes and scored with the pipeline's own validators, so only OpenAI tokens are spent (`scripts/replay_harness.py`). It was merged on 17 Aug 2026 (`03c5fe4a Merge gpt_compitabel: OpenAI provider migration`).

8. **Secrets in `.env`, all behaviour in code.** Model routing, timeouts and retries live in typed Pydantic config, not environment variables. LLM keys are checked at *call* time so importing modules (and running the offline tests) never needs keys.

9. **Python owns timing math; the LLM only writes words.** Segment character budgets come from YAML timing registries (minimum natural duration per tag) and the voice's characters-per-second. Failing segments get *targeted* rewrites ("Do NOT rewrite passing tags"). The final "script doctor" pass is **guarded**: its output is discarded if tags are missing, any segment is out of budget, **any number changed**, or a segment ends on a dangling conjunction (`src/agents/phase2_scripting/llm_writer.py`).

10. **Data-feasibility gate plus over-provisioning in discovery.** A viral topic with no real published data is "worthless downstream". A strong hook can't compensate, because feasibility is only 20% of the weighted score. So candidates with `data_feasibility_score < 5.0` are dropped, and ideation over-provisions `max(top_n + 4, ceil(top_n × 2.5))` ideas, since in some niches ~70% get gated. Each extra idea costs about $0.001 (`src/agents/core/config.py`).

11. **Human-in-the-loop topic approval.** Discovery returns ranked candidates, and a person approves one (`phase1-approve`) before extraction spends money.

12. **LLM timeout raised to 180 s on purpose.** A reasoning model at medium effort can exceed 60 s. If the client gives up, "the server still finishes and still bills … then tenacity retries — turning one slow call into six paid-for-and-discarded ones" (`src/agents/core/config.py`).

13. **Render on many-core CPU pods, not GPUs.** "Manim's Cairo renderer is single-threaded and CPU-bound, so throughput comes from running many renders at once – not from a GPU" (`tools/runpod_render.ps1`). Worker count is capped by **free RAM** (2.5 GB/worker) and cgroup CPU limits (`render_batch.py`). Render dependencies are **exactly pinned** because an unpinned Manim "silently changes how frames rasterize" (`requirements-render.txt`). Fonts are shipped in the bundle because Linux Pango would otherwise substitute fonts silently. Phase 4 needs no API keys, so ".env never leaves this machine."

14. **Scope discipline (explicit YAGNI).** The roadmap (Vision-model QA loop, "Director" spec, generative assets, SaaS job queue, auto-publish + analytics flywheel) is parked: "Building these now … would be massive over-engineering before product-market fit" (`docs/future_feature_roadmap.md`). The visual polish pass was scoped to the **shared layer** so "one change upgrades all 7 templates at once", with a "sync-safety guarantee" that no timed animations are added (`docs/current_implementation.md`).

15. **Extensible template registry.** New templates go in `templates.json` (merged over built-ins) without editing `main.py`. `job.json` is validated with Pydantic before an expensive render starts.

---

## Hard problems solved / engineering highlights

1. **Audio-video tail truncation, found by measurement and fixed by reordering the pipeline.** Originally the voice was trimmed at concat time, *after* Manim had rendered against the untrimmed timeline. The mux then cut the video to the shorter audio. The owner measured that "every job was losing its tail … (−0.76 s to −6.08 s measured across 10 jobs)". `jobs/sort_job` lost 6.3 s, including the whole winner tail and outro. Whether a video survived "came down to luck": jobs were spared only when a late SFX cue propped the audio length up. The fix in `src/sync/audio_normalize.py`:
   - Trim first.
   - Rewrite `job["timeline"]` to the real durations.
   - Only then render.
   - Keep originals in `audio/_raw/` and always re-derive from them, so the step is idempotent and can't trim twice.

   After the fix, `sum(timeline) == len(voice track)`. The final commit reports "all seven scenes match audio length (delta 0.00s)". In the repo, `jobs/auto/auto_12` has a timeline sum of 95.14 s and its `final.mp4` measures 95.2 s.

2. **Silent drift from a naming mismatch.** Hand-made jobs name segments `item_1`, while the AI handoff emits `item1`. Templates that matched only one spelling missed every timeline entry and fell back to default durations: "bar/donut/geo visuals ran up to 24s ahead of the voice." Fixed with `numbered_segments()`, which accepts both spellings (`src/sync/timeline.py`, commit `8fa3e037`).

3. **Measuring real animation cost to fix overruns.** The geo template overran its narration by +3.75 s on every job. The owner measured this "by wrapping Scene.play/wait and timing every animation against the scene clock, dry-run, no video written". The timing registry was then corrected, e.g. SETUP 2.6 → 4.07 s measured, WINNER 2.2 → 4.93 s (`.agent/context/template_timing_registry.yaml`).

4. **Drift-free sync architecture:** absolute-clock segment anchoring (`schedule` / `target_elapsed` / `sync_hold`), so overruns are absorbed instead of adding up, plus "ghost padding" loops that consume audio segments with no matching visual (`technical_refactor_document.md`, Phase 2).

5. **Professional audio mix in pure FFmpeg filter graphs.** A voice compressor, SFX and BGM EQ, **sidechain ducking keyed on the voice** (three duck strengths, two presets), a limiter, safe silence fallbacks when there are no SFX marks, and per-event delays and gains (`main.py`).

6. **Hardened multi-provider LLM client.** Response-shape parsing that tolerates reasoning items and split parts; a leaf exception taxonomy where `LLMBadRequestError` is never retried; `temperature` stripped for gpt-5.x (it "is rejected with HTTP 400"); and a clear **cost contract** so reasoning tokens are never double-counted across providers (`src/agents/core/llm_client.py`, `cost_tracker.py`).

7. **Guarded LLM output.** Deterministic validators (tags, length budgets, number preservation, dangling-ending checks) wrap every creative LLM pass. A failed polish falls back to the last good script instead of shipping a broken one.

8. **Hinglish number normalizer.** It stops the LLM or TTS from mispronouncing figures by giving the model exact spoken forms of each number (`src/agents/phase2_scripting/num_normalizer.py`, with tests in `tests/phase2_scripting/test_num_normalizer.py`).

9. **Crash-safe, idempotent pipeline state.** Atomic temp-file → `os.replace` writes, tolerance of corrupted state files, per-step completion flags, and a topic archive with TTL-based cooldowns and schema migration.

10. **Visual QA at scale without a video editor.** Frame probes (`save_last_frame` at chosen timestamps) and before/after PNG comparisons were used to fix overlaps, stray marks, placeholder text and kerning across all seven templates. Examples: a small-text kerning patch that lays out at 48 pt and scales down, a donut callout-overlap resolver, and a shared end-card banner (commits `8fa3e037`, `0d98c677`; probe images under `jobs/donut_job/output/`).

11. **Cloud batch rendering tuned to the hardware.** RAM-aware parallelism, cgroup CPU detection, exact dependency pins so pixels match the laptop, and a network-volume bootstrap so later pods start "render-ready in seconds" (`render_batch.py`, `tools/runpod_*`).

12. **Cheap, safe model-migration validation.** The replay harness reuses archived Tavily sources and Gemini answers and scores new outputs with the pipeline's own validators (`scripts/replay_harness.py`, `tests/core/test_replay_harness.py`).

---

## Results, metrics, scale

*All figures are measured from the repository on 2026-09-25. No audience or view metrics exist in the repo.*

- **Codebase size:** ~120 Python files, ~32,400 lines total (~23,900 non-blank, non-comment lines) across `src/`, `tests/`, `scripts/`, `tools/`, `main.py`, `captions.py` and `render_batch.py`.
  - The 7 template files are 1,040–1,725 lines each, with roughly 650–1,340 active (non-comment) lines. Several keep large commented-out legacy blocks.
  - `main.py` is 1,149 lines.
- **Tests:** 25 `test_*.py` modules with ~190 `test_*` functions, under `tests/core`, `tests/phase1`, `tests/phase2_scripting`, `tests/pipeline` and `tests/fixtures`. Most use fakes, so they run without API keys. The last recorded run in `OVERVIEW.md` (June 2026) was Phase 2 3/3 passing and Phase 1 20/21, with one known test-fixture bug. Tests were not run for this write-up.
- **Templates:** 7 production scene templates, each with its own retention accent.
- **Pipeline runs:** 23 auto-mode job folders (`jobs/auto/auto_2` … `auto_24`) plus per-template job buckets.
- **Rendered outputs in the repo:** 12 current `final.mp4` videos (plus captioned variants), 29 s to 95 s long, 1080×1920, H.264. There are also **106** archived render versions under `jobs/*/output/renders/`, showing the iteration history.
- **LLM cost per video (from `logs/cost.jsonl`):**
  - **Full auto run `jobs/auto/auto_12`:** discovery ideation, 25 scoring calls, script draft, 2 rewrites and the doctor pass = **30 recorded LLM calls, ≈ $0.036 total**. The biggest items were scoring (≈ $0.022) and the script doctor (≈ $0.008).
  - **Per-job scripting runs:** ≈ $0.011–$0.029 in LLM spend (3–6 calls).
  - Tavily and ElevenLabs costs are **not** in these logs, and no extraction call appears in auto_12's cost log (see Open questions).
- **Sync accuracy after the fix:** "all seven scenes match audio length (delta 0.00s)" (commit `0d98c677`). In the repo, `auto_12` shows a 95.14 s timeline vs a 95.2 s rendered video. Before the fix, 10 jobs lost 0.76–6.08 s of tail.
- **Codebase knowledge graph** (graphify, built from `0d98c677`): 2,668 nodes, 4,326 edges, 225 communities (`graphify-out/GRAPH_REPORT.md`).
- **Git:** 50 commits on the active branch by one author, 17 Jan 2026 → 16 Sep 2026. 13 remote branches.

---

## Current status & timeline

**Timeline (from git history and dated docs):**

| When | Milestone |
|---|---|
| 17–18 Dec 2025 | Manim practice in `C:\manim_pracstice` (learning Transforms) |
| 17–18 Jan 2026 | GitHub repo created; initial commit |
| Jan–early Feb 2026 | First templates built and debugged (visibility fixes, bar chart, vs_card design); "dynamic audio 1st" (7 Feb) |
| 15–22 Feb 2026 | "prototype" → "prototype 2" |
| 18–23 Feb 2026 | Codex-assisted audit and polish batch: audio-duration tooling, silence trim in concat, retention + captions premium polish, geo sync hotfixes, delta-time sync refactor (`CHANGELOG_CODEX.md`, `technical_refactor_document.md`) |
| 28 Feb – 9 Mar 2026 | Agentic pipeline design docs: `master_pipeline_edd_v6.md`, Phase 1/2 implementation contracts, Phase 3 plan, scoring rubric, archive policy |
| Mar 2026 | Phase 1 testing ("phase 1 testing pending", "phase1 have flaw") |
| 26 Apr 2026 | "sample video"; the 4 demo GIFs in `VIDEOGIF/`. **This is still the head of `origin/main` on GitHub** |
| 22 May – 5 Jun 2026 | Expert code reviews + refactor plans for all agent modules (`CODE_REVIEW_*.md`, `REFACTOR_PLAN_*.md`); 46 refactor items applied (`polish8`, 3 Jun) |
| 5–13 Jun 2026 | Edge-case hardening, video polishing parts 1–4, donut/sort fixes, "search engine fixed", "phase1 complete" |
| 19–20 Jun 2026 | First end-to-end renders ("going to render") |
| 5 Aug 2026 | Visual Premium Pass plan, Motion B-roll plan, future roadmap docs; TTS/trim tuning |
| 11–18 Aug 2026 | OpenAI provider migration (merged 17 Aug); full auto run `auto_12` (costs logged 11 Aug, rendered 18 Aug). Last push to GitHub: 18 Aug (`origin/workhere`) |
| 24–25 Aug 2026 | RunPod cloud render tooling, pinned render requirements |
| 16 Sep 2026 | Commits: RunPod tooling + pre-render voice normalization; template visual QA across all 7 templates; "all seven scenes match audio length (delta 0.00s)". On local branch `fixing_visal_mismtch`, **not pushed** |

**Done:**
- The full pipeline (discovery → extraction → script → TTS → handoff → render → mix → captions).
- 7 templates.
- The OpenAI migration with Gemini fallback.
- Cost tracking.
- Batch and cloud rendering.
- The Visual Premium Pass. The doc says "no code written yet", but the code now has `add_cinematic_background` in the templates and font registration in `src/config.py`, so it appears implemented.
- The sync/QA pass.

**Planned / not started:**
- Motion B-roll layer (`docs/motion_broll_plan.md`; no `src/broll/` exists).
- Translation / multilingual captions (`translator.py` stub).
- Everything in `docs/future_feature_roadmap.md`: Vision-model QA loop, Director spec + style skins, new formats (time-evolution bar race, top-10 countdown, tier list), auto-thumbnails, SaaS job queue, auto-publish + analytics feedback flywheel.

**Channel status:** per `docs/future_feature_roadmap.md` (Aug 2026) the YouTube channel had not launched yet.

---

## Limitations & known issues

- **No published results yet.** There is no audience, view or retention data. The value so far is the engineering, not proven channel performance.
- **The public GitHub default branch is stale.** `origin/main` is at 26 Apr 2026 ("sample video"). The newest pushed work is `origin/workhere` (18 Aug). The latest work (16 Sep) exists only locally on `fixing_visal_mismtch`. A recruiter opening the repo would see an old version.
- **Security hygiene:** a git-tracked log file, `demo_output_result.txt`, which is present on the public `origin/main`, appears to contain an API key inside a logged request URL. The key should be revoked or rotated and the file purged from history. Other committed debug files (`traceback.txt`, `err.txt`, `repair_err.txt`, etc.) clutter the root.
- **No README.md.** Documentation is spread across `CLAUDE.md`, `AGENTS.md`, `OVERVIEW.md`, `RUNBOOK.md`, `PLANS.md` and many review/plan files.
- **Legacy code left in place.** Templates keep large commented-out legacy versions; for example about 890 of `bar_chart.py`'s 1,545 lines are comments or blank. `src/utils.py` has a legacy header block. Some templates still carry a local `SFXMarksWriter` alongside the shared `src/sfx/engine.py`.
- **Captions are approximate.** Karaoke and word-reveal timing is an equal split across words, not forced alignment (`src/captions/aligner.py`, `ass_renderer.py`).
- **Heavy, slow rendering:** single-threaded Cairo, ~2–2.5 GB RAM per render process. This is why the cloud batch tooling exists.
- **Semi-automatic by design:** topic approval is manual, and the VS/sort templates rely on manually prepared image assets (`assets/images/`).
- **Most tests use fakes.** Rendering correctness is checked with compile checks, frame probes and manual review, not automated visual regression tests. One known Phase 1 test-fixture failure was recorded in June; current pass status is unknown.
- **Small inconsistencies:** Python version (docs say 3.11+, the render lock notes the laptop at 3.10.11). `src/config.py` declares `FPS = 30` but never applies it to Manim's frame rate, and the rendered finals in `jobs/` are 15 fps.
- **Earlier code reviews in the repo rated some core modules low**, e.g. `cost_tracker.py` 4/10 in `CODE_REVIEW_CORE.md`. According to `OVERVIEW.md`, the refactor plans that followed were applied.

---

## Demo assets

**GitHub:** https://github.com/Hacke2367/Auto_shorts_engine_1 (public; default branch `main` is from Apr 2026, see Limitations)

**Animated GIF previews** (tracked in git; 26 Apr 2026, earlier visual version, 9:16):
- `C:\MANIM_VIDEOS_CODE_TEMPALTE\VIDEOGIF\template1.gif`: head-to-head comparison ("WHO WILL DOMINATE?", Item A vs Item B, SPEED / HANDLING rounds)
- `C:\MANIM_VIDEOS_CODE_TEMPALTE\VIDEOGIF\template2.gif`: donut breakdown ("MARKET SHARE 2025 – Global smartphone shipments")
- `C:\MANIM_VIDEOS_CODE_TEMPALTE\VIDEOGIF\template3.gif`: geo map ("GLOBAL ALLIANCE MAP", with burned-in captions visible)
- `C:\MANIM_VIDEOS_CODE_TEMPALTE\VIDEOGIF\template4.gif`: line race ("GDP GROWTH RACE", live ranking HUD). This early GIF shows a label/badge overlap that the Sep 2026 QA commit says it fixed

**Finished videos** (1080×1920, H.264; newest are best; Hinglish narration):
| File | Template | Length | Rendered |
|---|---|---|---|
| `jobs\auto\auto_12\output\final.mp4` | vs_card (fully AI-generated, "Rome vs Han China") | 95.2 s | 18 Aug 2026 |
| `jobs\job_0001\job_bar_chart_3\output\final.mp4` | bar_chart (top-10 wealth) | 72.7 s | 16 Sep 2026 |
| `jobs\butterfly_job\output\final.mp4` | butterfly_chart | 29.2 s | 16 Sep 2026 |
| `jobs\vs_card\vs_card_3\output\final_captioned.mp4` | vs_card ("Gold vs Bitcoin", captioned) | 56.3 s | 18 Aug 2026 |
| `jobs\geo_job\output\final_captioned.mp4` | geo_universal (captioned) | 39.3 s | 18 Aug 2026 |
| `jobs\geo_universal\geo_universal_1\output\final.mp4` | geo_universal (student-loan debt by state) | 55.5 s | 18 Aug 2026 |
| `jobs\donut_job\job_donut_breakdown_1\output\final.mp4` | donut_breakdown (gold) | 44.8 s | 18 Aug 2026 |
| `jobs\scan_job\output\final.mp4` | scan_race | 34.1 s | 18 Aug 2026 |
| `jobs\sort_job\output\final.mp4` | sort_card | 74.1 s | 18 Aug 2026 |
| `jobs\sort_card\sort_card_1\output\final.mp4` | sort_card ("payment innovations") | 48.0 s | 19 Jun 2026 |

(All paths are relative to `C:\MANIM_VIDEOS_CODE_TEMPALTE\`. The 16 Sep 2026 renders reflect the latest QA fixes; the others predate them.)

**Iteration history / before-after material:**
- `jobs\*\output\renders\final_<timestamp>.mp4`: 106 archived renders (e.g. `jobs\butterfly_job\output\renders\`, `jobs\donut_job\output\renders\`)
- `jobs\donut_job\output\_BEFORE_donut_10s.png` / `_AFTER_donut_10s.png` (also 16 s), and `_AB_with_background_20s.png` / `_AB_without_background_20s.png`: visual-polish before/after comparisons
- Frame-probe stills: `jobs\donut_job\output\_t*.png`, `_rev_*.png`, `_chk_*.png`; `jobs\butterfly_job\output\_verify.png`

**Architecture / code visuals:**
- `graphify-out\graph.html`: interactive knowledge-graph visualization of the codebase (2.3 MB)
- ASCII data-flow diagram in `RUNBOOK.md` ("Data Flow Diagram" section)

**Sample inputs:** `data\*.csv` (e.g. `market_share.csv`, `race_data.csv`, `vs_data.csv`), `jobs\topic_archive.json`, and persona files in `.agent\context\personas\`

---

## Why this impresses a recruiter

**Non-technical impact angle.** The owner built, alone, a working "video factory" that turns a topic into a finished, branded, narrated, captioned short video. That work normally needs a researcher, a scriptwriter, a voice artist and a motion designer. A full AI-driven run (topic discovery through final script) cost about **4 US cents** in LLM fees in the logged example. The owner also showed product judgment:
- kept a human approval step where it matters;
- deliberately parked "cool" features until real audience data exists;
- measured problems before fixing them (e.g. exactly how many seconds each video was losing).

**Technical-depth angle.** This is a real multi-stage system, not a single API call:
- an agentic LLM pipeline (LangGraph state machine, structured outputs, retry/rate-limit/circuit-breaker, per-route multi-provider routing, cost accounting, replay-based model-migration validation);
- deterministic guardrails around every creative LLM step;
- a custom programmatic animation engine (7 Manim templates, ~24k active lines of Python overall) with a clock-anchored audio-visual sync design;
- an event-driven SFX system and a broadcast-style FFmpeg mix (sidechain ducking, limiter);
- ASS subtitle generation;
- hardware-aware parallel cloud rendering with pinned, reproducible dependencies.

The debugging stories (tail truncation, the 24-second drift from a naming mismatch, measuring animation cost by instrumenting the scene clock) show root-cause engineering rather than patching symptoms.

---

## Likely recruiter Q&A

**Q1. What is this project in one sentence?**
A: AutoShorts is an end-to-end Python pipeline that turns a topic into a finished 9:16 data-infographic short video. AI finds a trending, data-backed topic, extracts real numbers from the web, writes a Hinglish script, generates the voice-over, and a custom Manim animation engine renders and mixes the final video (`CLAUDE.md`, `main.py`, `src/cli/autoshorts.py`).

**Q2. Is it fully automatic?**
A: Almost, by design. Discovery ranks candidate topics and a person approves one (`phase1-approve`) before money is spent on extraction. Everything after that can run with a single `run` command (Phase 2 → Phase 3 → handoff → render). Some templates, such as VS cards, use manually supplied images.

**Q3. Which AI models and APIs does it use?**
A: OpenAI's Responses API on all six LLM routes (configured to `gpt-5.6-luna` at different reasoning-effort levels), with Google Gemini (2.5 Flash/Pro) kept as a per-route fallback or A/B option. Tavily handles web search and scraping, and ElevenLabs (`eleven_multilingual_v2`) does text-to-speech (`src/agents/core/config.py`).

**Q4. Why did it switch from Gemini to OpenAI?**
A: Cost-to-quality. The config records that the chosen OpenAI tier's output price buys about 8× more reasoning than gemini-2.5-pro for the same spend. So the owner raises quality through the "reasoning effort" setting instead of paying for a bigger model. The switch was validated with a replay harness that re-ran archived inputs and scored outputs with the pipeline's own checks, spending only OpenAI tokens (`LLMConfig` docstring, `scripts/replay_harness.py`; merged 17 Aug 2026).

**Q5. How much does one video cost to generate?**
A: Only LLM costs are logged. A full automatic run (`jobs/auto/auto_12`: ideation + 25 topic-scoring calls + scripting with rewrites and a polish pass) recorded 30 calls and about $0.036. Scripting-only runs were about $0.01–$0.03. Tavily search and ElevenLabs voice costs aren't in these logs.

**Q6. What was the hardest technical problem?**
A: Keeping animation perfectly in sync with narration. One example: every video was silently losing 0.76–6.08 s at the end, because the voice was trimmed *after* the animation had been rendered against the untrimmed timing, and the final merge cut the video down. The fix was to trim first, rewrite the timeline to the real durations, and then render. The merge was also changed so the video, not the audio, decides the length. After the fix all seven templates match audio length exactly (`src/sync/audio_normalize.py`, `main.py`, commit `0d98c677`).

**Q7. How do the animations stay synced to the voice?**
A: Each template reads per-segment audio durations from `job.json`. `Timeline.schedule()` precomputes each segment's absolute end time, and `sync_hold()` waits until the scene clock reaches it, so any overrun is absorbed at the next boundary instead of adding up. When an animation finishes early, `hold_breathing()` keeps the screen alive with subtle glow, progress-bar and accent animations instead of a frozen frame (`src/sync/timeline.py`, `src/sync/retention_base.py`).

**Q8. How are sound effects synced?**
A: Manim never plays audio. Templates call `sfx.mark("event")`, which logs the exact scene time to `sfx_marks.json`. FFmpeg then places each sound effect with a precise delay, mixes them, and ducks SFX and background music under the voice using sidechain compression (`src/sfx/engine.py`, `main.py`).

**Q9. How do you stop the AI from making things up or breaking the format?**
A: Several guardrails:
- A data-feasibility gate drops topics without provable published data.
- Extraction must fit a strict per-template schema, with an audit trail of sources.
- Python, not the LLM, computes how many characters each segment may have.
- Failing segments get targeted rewrites.
- The final "script doctor" polish is thrown away if it changes any number, breaks tags, exceeds length budgets, or leaves a sentence dangling (`discovery_runner.py`, `llm_writer.py`).

**Q10. Why Manim and not After Effects or a video API?**
A: The project's stated philosophy is "Build > Buy/Wrapper". Code-driven animation makes videos data-driven, repeatable and producible in bulk from a JSON/CSV input, with exact control over timing. The tradeoff is slow, CPU-heavy rendering, which the owner handled with parallel cloud rendering (`technical_refactor_document.md`, `render_batch.py`).

**Q11. How does it scale rendering?**
A: Manim's renderer is single-threaded, so throughput comes from running many renders at once. `render_batch.py` launches parallel renders, capped by free RAM (~2.5 GB each) and container CPU limits. PowerShell/bash tooling ships the code to a many-core RunPod CPU pod, renders there, and pulls the videos back. Render dependencies are exactly pinned so frames look identical to the laptop's.

**Q12. How is it tested?**
A: About 190 pytest test functions across core, Phase 1, Phase 2 and pipeline suites, mostly using fake LLM/TTS clients so they run without API keys. There is also an offline end-to-end mode for audio, request-snapshot tests for the LLM client, and a replay harness. Visual correctness is checked with frame-probe screenshots at chosen timestamps. The most recent recorded run (June 2026) was 20/21 Phase 1 and 3/3 Phase 2, with one known fixture bug.

**Q13. What templates/formats can it produce?**
A: Seven: ranked bar chart, butterfly (two-sided) comparison, line "race" over time, geo/world map, tier-sorting cards, multi-round VS cards, and a market-share donut. All share one neon "BIGDATA LEAK" brand look and add captions and SFX automatically (`templates.json`).

**Q14. Is it finished? What's next?**
A: The core pipeline, all seven templates, the OpenAI migration, cloud rendering and a full visual/sync QA pass are done (latest commit 16 Sep 2026). Planned next: a motion B-roll layer. Parked until the channel has real data: a vision-model QA loop that grades rendered frames, a "director" spec for one-file creative control, new formats (bar race over time, top-10 countdown, tier list), and eventually a SaaS job queue with auto-publishing and an analytics feedback loop (`docs/`).

**Q15. Did you use AI coding tools to build it?**
A: The repo shows an AI-agent-assisted workflow. `CHANGELOG_CODEX.md` logs Codex steps, `AGENTS.md` and `CLAUDE.md` are agent instruction files, and recent commits are co-authored with Claude. The owner wrote the architecture/design docs, implementation contracts, code-review/refactor plans and QA passes that directed that work. (How the owner prefers this framed is an open question below.)

---

## Open questions for the owner

1. **Channel launch & results:** has the channel (brand "BIGDATA LEAK"?) gone live? Are there published video links, view counts, retention or CTR numbers to showcase?
2. **Best showcase video(s):** which rendered `final.mp4` should the portfolio feature, and is it OK to publish them? The GIFs in `VIDEOGIF/` are from April and predate the September visual fixes; should new GIFs be cut from the 16 Sep renders?
3. **GitHub state:** `origin/main` is from 26 Apr 2026 and the latest work (16 Sep, branch `fixing_visal_mismtch`) is unpushed. Do you plan to merge/push before linking the repo on the portfolio? Should the repo stay public?
4. **Security:** `demo_output_result.txt` (tracked, present on public `origin/main`) appears to contain an API key in a logged URL. Has that key been revoked or rotated? Do you want the file purged from history?
5. **Solo vs team:** all 50 commits are by you. Does the "sandeep claude" commit (5 Aug 2026) mean a collaborator was involved, or is that just a label?
6. **Frame rate:** rendered finals are 15 fps although `src/config.py` declares `FPS = 30`. Is 15 fps intentional (e.g. low-quality preset for speed), or should final renders be 30 fps?
7. **End-to-end cost & time:** what does a full video cost including Tavily and ElevenLabs, and how long does a render take locally vs on RunPod (and RunPod cost per batch)? None of this is logged. Also, `auto_12`'s cost log has no extraction entry. Was extraction reused from cache or just not logged?
8. **Model naming:** the repo configures OpenAI `gpt-5.6-luna` / `gpt-5.6-terra` with specific prices. Confirm these are the exact model names and prices you want quoted publicly.
9. **Project name for the portfolio:** "AutoShorts", "Auto Shorts Engine", or "manim_code_video_template"?
10. **AI-assisted development framing:** how do you want the use of Codex/Claude Code described (e.g. "architected and directed AI coding agents")?
11. **Current test status:** does the full suite pass today (the June run had one failing Phase 1 fixture)?
12. **Visual Premium Pass status:** `docs/current_implementation.md` says "no code written yet", but the code contains `add_cinematic_background` and font registration. Is the pass complete?
13. **Number-normalizer example:** the docstring says 2,500,000 → "do lakh pachaas hajar" (that reads as 2.5 lakh = 250,000). Is that a doc typo, or does the function behave that way?
