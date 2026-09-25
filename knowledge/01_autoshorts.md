# AutoShorts

## Pitch
AutoShorts is a software "video factory": give it a topic, and it researches real data on the web, writes a Hindi-English ("Hinglish") voice-over script with AI, records the narration with an AI voice, and renders a finished, animated, vertical (9:16) data-infographic video ready for YouTube Shorts or Reels. No video editor involved — everything is generated in code.

## Problem
"Faceless" data/infographic Shorts (rankings, comparisons, market-share breakdowns, maps, animated "race" charts) are popular, but making each by hand is slow: research numbers, write a script, record audio, animate charts, sync every animation to the voice, add sound effects, music and captions. That doesn't scale to publishing many videos regularly.

AutoShorts generates premium, high-retention "faceless" infographic shorts in bulk, following a "Build > Buy/Wrapper" philosophy — deep custom engineering over a thin wrapper around a video API, aiming for pixel-perfect sync. It's built as the engine behind a planned data-Shorts YouTube channel, targeting Hindi/English ("Hinglish") short-form viewers.

## What it does
- Two halves that run independently, joined by a shared per-video job folder.
- Content pipeline: AI brainstorms data-backed topic ideas checked against real web sources; a person approves one; the system extracts a structured dataset, writes a tagged script in a chosen persona (e.g. "savage roast"), generates AI narration, and hands off in a renderer-ready format.
- Video renderer: validates the job, trims voice clips to real lengths, renders one of seven templates at 1080×1920, builds a mixed audio track (narration, sound effects, optional music, ducked under the voice), muxes the final video, and can burn in styled captions.
- Seven templates share one dark, neon "cyber/data" visual identity (HUD, timer, footer branding): ranked bar chart, "butterfly" comparison, animated line "race," world/US map, tiered "sort" cards, multi-round "VS" cards, and a market-share donut.
- Operations tooling: parallel batch rendering (RAM-capped), cloud-render scripts, an LLM spend dashboard, and the replay harness.

## How it works
The content pipeline and video renderer are two independently runnable halves that agree on one filesystem contract: a job folder holding the script, audio, extracted dataset, and a job description with timing/mix settings.

```
DATA PIPELINE
 topic ─► Discovery: AI ideation ─► web-data check ─► AI scoring
        ─► feasibility gate ─► ranked candidates ─► HUMAN APPROVAL
       ─► Extraction: search ─► scrape ─► AI extract (strict schema)
       ─► Scripting: Python timing budget ─► AI draft ─► rewrites
          ─► guarded "script doctor" polish
       ─► Voice: AI TTS ─► trim silence ─► measure ─► package
       ─► Handoff ─► job folder (description, script, audio, data)
                              │
VIDEO RENDERER              ▼
 1. Validate job  2. Normalize voice (trim, rewrite timeline)
 3. Render animation template (reads timeline for sync)
 4. Build audio: voice ─► SFX ─► music  5. Mix (ducking, limiter)
 6. Mux: video length wins ─► optional captions ─► finished video
```

Pipeline internals: a single AI entry point normalizes two providers' response shapes and raises a loud error instead of silently returning empty text. Six AI call types each run at a tuned reasoning-effort level, with separate retry strategies for ordinary errors, rate limits, and must-succeed calls, plus a rate limiter, circuit breaker and per-run cost logging. Extraction runs as a small state-machine graph (search, scrape, extract, retrying search if empty), reusing source links discovery already proved contain data. Scripting has Python compute a character budget per segment from the template's minimum animation time and the voice's speaking rate; only failing segments get targeted rewrites; an optional final "doctor" pass is discarded if it changes any number, breaks structure, or ends a sentence badly. A dedicated normalizer converts numbers into spoken Hinglish for correct pronunciation.

Renderer internals: each template reads real per-segment audio durations and uses absolute-clock scheduling, waiting for the scene clock to reach a precomputed segment end time so overruns are absorbed at the next boundary instead of compounding. Early finishes get subtle, fault-tolerant "alive" hold effects instead of a frozen frame. The engine never plays audio itself — it logs sound-effect timestamps that a later stage turns into precisely timed, mixed effects, keeping the render deterministic and the mix changeable without re-rendering. Custom label placement and a custom map coordinate table replace heavier third-party libraries.

## Stack
- Language: Python
- Animation/rendering: Manim Community, Cairo/Pango/ManimPango, pycairo, skia-pathops, av
- Audio/video: FFmpeg/ffprobe (concat, trim, delay, mix, compressor, sidechain ducking, limiter), pydub
- LLMs: OpenAI Responses API (all routes on gpt-5.6-luna, gpt-5.6-terra as an escalation tier), Google Gemini (gemini-2.5-flash / gemini-2.5-pro) as a per-route secondary provider
- Web research: Tavily; Text-to-speech: ElevenLabs (eleven_multilingual_v2)
- Orchestration: LangGraph (extraction state machine), asyncio with aiohttp, tenacity retries
- Data/validation: Pydantic v2, pydantic-settings, pandas, numpy, PyYAML
- Subtitles: ASS generation with FFmpeg burn-in
- Infra: a local machine plus cloud CPU instances for parallel batch rendering, with pinned dependencies and bundled fonts
- Testing: pytest with fakes, offline end-to-end mode, snapshot tests, a replay harness
- Dev tooling: Git/GitHub, AI coding agents (Claude Code, Codex) directed by Abhishek, a code knowledge graph

## Key decisions
- Two halves joined by a filesystem contract, not one monolith: the renderer only needs a complete job folder however it got there, and each half is testable alone. Tradeoff: several file lists (segments, order, timeline, script) must stay in sync by convention, which caused real bugs.
- Code-driven animation with Manim, not video-editor templates or heavy GIS/animation libraries: matches "build, don't wrap," giving exact, data-driven, bulk-repeatable control. Tradeoff: single-threaded, CPU-bound, memory-hungry rendering.
- Sound effects logged as timestamps rather than played during rendering, and absolute-clock timeline scheduling instead of fixed run-times: both keep rendering deterministic and let overruns be absorbed at the next boundary instead of accumulating.
- "Alive" hold animations instead of frozen frames when narration outlasts the animation, aimed at viewer retention; each hold layer fails independently so one broken effect can't break the hold.
- Trim audio before rendering and let video length win the final mux, instead of trimming at final merge as originally built: fixed a bug where every video silently lost part of its ending (see Engineering highlights).
- Migrated default AI provider from Gemini to OpenAI, using reasoning effort as the quality dial instead of a larger model: the chosen tier bought roughly 8x more reasoning per dollar than the Gemini tier it replaced, validated with a replay harness against archived inputs first.
- Python, not the AI, computes segment timing budgets; secrets stay separate from all other configuration, which lives in typed code — both keep behavior deterministic and testable.
- A data-feasibility gate rejects topics without provable published data, and ideation over-generates candidates, because a strong hook can't make up for missing data.
- Kept a human-approval step for topic selection, ahead of automating the rest, so a person is in the loop before extraction spends money.
- Rendering runs on many-core CPU machines, not GPUs, with exactly pinned dependencies and bundled fonts: the renderer is CPU-bound, and unpinned versions were found to silently change how frames render.
- Several planned features (automated visual QA, a creative-direction spec, generative assets, a job queue, auto-publishing) are parked as over-engineering before there's real audience data.

## Engineering highlights
- Diagnosed and fixed an audio/video tail-truncation bug by measurement: voice trimming happened after the animation had rendered against untrimmed timing, so the final merge silently cut 0.76–6.08 seconds off the end across 10 sampled jobs, losing an entire ending scene once. Fixed by trimming audio first, rewriting the timeline to match, then rendering; all seven templates now match audio length exactly.
- Found and fixed a silent naming-mismatch bug: hand-made and AI-generated jobs named script segments differently, so some templates missed timeline entries and drifted up to 24 seconds ahead of the voice. Fixed by making the lookup accept both naming styles.
- Measured real animation cost instead of guessing, by instrumenting the engine to time every animation against the scene clock in a dry run; found one template overrunning narration by 3.75 seconds every job and corrected the timing data from the measured values.
- Built a drift-free sync architecture where each segment's precomputed absolute end time absorbs overruns at the next boundary, plus a full audio mix in FFmpeg filter graphs (compressor, sidechain ducking, limiter, safe fallbacks with no sound cues).
- Hardened the multi-provider AI client with tolerant response parsing across two providers' shapes, an error taxonomy so bad requests are never blindly retried, and cost accounting that avoids double-counting reasoning tokens.
- Wrapped every creative AI step in deterministic guardrails (structure, length, number-preservation, sentence-ending checks) so a bad pass falls back to the last good script; also built a Hinglish number normalizer.
- Made pipeline state crash-safe and idempotent, and used frame-probe screenshots and before/after image comparisons to find and fix visual bugs across all seven templates without a full video re-review each time.
- Tuned cloud batch rendering to the hardware, and built a replay harness that validates changes cheaply by re-scoring archived inputs instead of spending fresh money each test.

## Numbers
- Full automatic run: 30 AI calls, ~$0.036 total. Scripting-only runs: ~$0.011–$0.029 (3–6 calls) per job.
- Codebase: about 120 Python files, ~32,400 total lines (~23,900 non-blank, non-comment); main renderer entry point 1,149 lines.
- Tests: 25 modules, ~190 test functions; last recorded run 3/3 scripting, 20/21 discovery, one known fixture bug.
- 7 production templates; 23 automatic-mode job runs plus per-template job folders.
- 12 current finished videos (plus captioned variants), 29–95 seconds, 1080×1920, H.264; 106 archived render versions.
- Sync accuracy after the fix: all seven templates match audio length exactly (0.00s delta), vs. 0.76–6.08s of tail loss across 10 jobs before it.
- One template's corrected timing: one segment moved from 2.6s to 4.07s, another from 2.2s to 4.93s.
- Codebase knowledge graph: 2,668 nodes, 4,326 edges, 225 communities.
- Git history: 50 commits by one author over ~8 months.
- Render memory: ~2–2.5 GB per process, setting the cloud worker cap.

## Status
Done: the full pipeline from discovery through captioned final video, all seven templates, the OpenAI-based setup with a Gemini fallback, cost tracking, batch/cloud rendering, a visual polish pass, and an audio/video sync fix verified across all seven templates (most recent work: a template-by-template visual QA pass confirming exact sync).

Next: a motion B-roll visual layer is planned but not built. Parked until there's real audience data to justify them: an automated AI quality check on rendered frames, a unified creative-direction spec, additional formats, automatic thumbnails, and a job-queue/auto-publishing model. The YouTube channel this engine is built for hasn't launched yet, so fully unattended, continuously-running production is the next milestone.

## Limitations
- No audience or performance data yet — the demonstrated value so far is the engineering, not proven performance.
- Captions use equal-split word timing, not forced speech alignment, so karaoke/word-reveal timing is approximate.
- Rendering is heavy and slow (single-threaded, ~2–2.5 GB RAM per process), hence the cloud rendering tooling.
- Topic approval is a deliberate manual step, and a couple of templates rely on manually supplied images.
- Most tests use fake AI/voice services, so correctness relies on frame checks and manual review, not automated visual regression.
- Some legacy, commented-out code remains in a few template files, and a few small settings inconsistencies exist (e.g. a configured frame rate that differs from the one used in current renders).

## Code & demos
Code is available on request — contact Abhishek. Demo outputs include finished 9:16 vertical videos across all seven templates, plain and captioned versions, animated preview clips, before/after image comparisons from the visual-polish work, and an interactive visualization of the codebase's own architecture.

## Recruiter Q&A

Q: What is this project in one sentence?
A: A Python pipeline that turns a topic into a finished 9:16 data-infographic short video: AI finds a data-backed topic, extracts real numbers, writes a Hinglish script, generates the voice-over, and a custom animation engine renders and mixes the video.

Q: Is it fully automatic?
A: Almost, by design. A person approves the AI's chosen topic before extraction spends money; everything after runs as one automated command. A couple of templates use manually supplied images.

Q: Which AI models and services does it use?
A: OpenAI's Responses API on every route (gpt-5.6-luna at varying reasoning-effort levels, gpt-5.6-terra as an escalation option), Gemini as a per-route fallback, Tavily for web research, and ElevenLabs for text-to-speech.

Q: Why did it move from Gemini to OpenAI, and how much does one video cost?
A: Cost-to-quality — the chosen OpenAI tier bought roughly 8x more reasoning per dollar than the Gemini tier it replaced, validated with a replay harness before going live. Only AI-model costs are logged: a full automatic run recorded 30 calls totaling about $0.036; scripting-only runs cost roughly $0.01–$0.03. Web-search and voice costs aren't in these logs yet.

Q: What was the hardest technical problem?
A: Sync. Every video was silently losing 0.76–6.08 seconds off its ending because voice was trimmed after the animation rendered against untrimmed timing. Fixed by trimming first, rewriting the timeline to real durations, then rendering, with the video's length winning the final merge.

Q: How do the animations and sound effects stay synced to the voice?
A: Each template precomputes each segment's absolute end time from real audio durations and waits for the scene clock to reach it, so overruns are absorbed at the next boundary. Sound effects are logged as timestamps, then placed precisely and ducked under the voice during the mix.

Q: How do you stop the AI from making things up or breaking the format?
A: A feasibility check drops topics without real published data, extraction must fit a strict schema with a source trail, Python (not the AI) sets each segment's character budget, and a final AI polish pass is discarded if it changes any number or breaks structure.

Q: Why Manim instead of a video editor or video-generation API, and how does it scale?
A: "Build, don't wrap" — code-driven animation is data-driven, exactly timed, and repeatable in bulk. The tradeoff is a single-threaded, CPU-bound renderer, so throughput comes from a batch script running many renders in parallel (capped by memory) and tooling that ships jobs to a many-core cloud machine with pinned dependencies to match local output.

Q: How is it tested?
A: About 190 test functions, mostly with fake AI/voice services so tests run without live API access, plus an offline audio mode and a replay harness. The last recorded run passed 20/21 discovery and 3/3 scripting tests, with one known fixture issue.

Q: Is it finished? What's next?
A: The core pipeline, all seven templates, the OpenAI migration, cloud rendering and a full sync QA pass are done. A motion B-roll layer is next; bigger features are parked until there's real audience data to build them against.

Q: Did Abhishek use AI coding tools to build it?
A: Yes. Abhishek designed the architecture and made the engineering decisions, then directed AI coding agents (Claude Code and Codex) that wrote most of the code; he reviewed and tested their output.
