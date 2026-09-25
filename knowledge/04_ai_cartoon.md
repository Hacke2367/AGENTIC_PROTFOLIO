# AI Cartoon

## Pitch
Type one sentence, such as "a detective finds a body," and the system writes a Hindi thriller
story, draws every scene with consistent characters, animates it, adds narration, and outputs a
finished vertical video. It runs on rented cloud GPUs and self-hosted open models instead of
paid per-clip video APIs, so each video costs a few dollars. Abhishek designed and built it as a
one-person Hindi YouTube animation studio.

## Problem
Abhishek wanted to run a Hindi YouTube animation channel alone, with no team, across two planned
looks: a dark noir thriller style and a warm, Ghibli-like parallax style. Many story channels are
cheap AI-image slideshows with a voiceover; the goal was cinematic motion that stands out. Paid
video APIs would cost roughly ₹1,500+ per video, against a target of ₹30–50 on self-run GPUs,
under a ₹5,000/month budget. The harder constraints turned out to be hardware (a laptop with no
CUDA GPU, 7.7 GB RAM) and YouTube's policy against mass-produced content. Current target: a
30–60 s vertical Hindi thriller from a one-line premise, no manual steps.

## What it does
One command turns a premise into a finished episode:
- Writes a Hindi script in scenes, one sentence per line, with sound-effect cues.
- Builds a "story bible" — one locked English description per character/location/prop, so
  characters stay visually consistent.
- Records narration first, sentence by sentence (ElevenLabs, a self-hosted Hindi voice, or
  silence for offline tests) — each shot's length is set by its spoken sentence.
- Plans each shot, then draws it as a 9:16 image with Qwen-Image on a cloud GPU.
- A "motion director" (Claude vision) picks how to animate each frame — plain video, a
  first/last-frame clip, or cheap parallax — and writes a motion prompt plus checks.
- Animates shots with Wan2.2 on rented GPUs in parallel; a "judge" (Claude vision) scores each
  clip 1–5, retrying failures up to twice, then ships flagged for review if it never passes.
- Assembles the final MP4 with ffmpeg, synced to narration, saving state each stage so a killed
  run resumes without redoing or re-paying for work.

Each episode also outputs a contact sheet of frames, a clip filmstrip, every raw attempt with
its judge verdict, and a full audit log.

## How it works
A laptop "planner" (no GPU) pairs with a rented GPU pod as a "batch oven" — boots, drains its
queue, shuts down.

```
premise -> A1 script (Hindi) -> A2 story bible (locked appearance text)
  -> TTS per sentence (duration measured from audio)
  -> A3 shot list (character/location IDs, not prose)
  -> validators (pure Python) -> prompt compiler (deterministic, no LLM)
  -> Qwen-Image -> frames (928x1664)
  -> motion director (Claude vision) -> Wan2.2 video generation (parallel GPUs)
  -> judge (Claude vision, retries) -> ffmpeg assemble -> final.mp4
```
State is written atomically after every stage for resumability.

Design invariants:
- Shot planner outputs IDs only, never appearance text; a deterministic compiler (no LLM) pastes
  in the bible's locked description, so a character's look can't drift.
- Audio is generated before shots are planned; duration is measured from the WAV, never
  LLM-assigned; cumulative-rounding frame counts match video length to audio within half a
  frame, by construction.
- Shot-motion budgets are enforced in plain Python, never left to the LLM.
- Every frame/clip/audio segment is content-addressed, so nothing is regenerated or paid for
  twice; narration/music/effects stay separate stems, and Hindi text is never baked into a
  frame, so an English dub is just a swapped audio track.

The only code calling the Anthropic API is one client wrapper. It logs token usage, checks for
safety refusals (thriller violence can trigger a refusal that looks like a normal empty
response) before reading content, and retries once on a fallback model.

Simple shots get cheap CPU-based parallax; "hero" shots get full AI motion via a hybrid recipe —
a few full-quality early steps, then fast distilled steps. Every clip passes 7 automated guards
(playability, geometry, codec, motion liveness, a blank-output check, and more) before reaching
the judge.

Offline-first: every expensive stage has a permanent stand-in, so the pipeline and test suite
run with no GPU and no spend, including a full episode rehearsal before any GPU pod is rented.

## Stack
- Python 3.10, about 12,000 lines of source, about 7,500 lines of tests; Pydantic v2 schemas.
- Plain Python orchestration — deliberately no LangChain, LangGraph, CrewAI, or MCP.
- Anthropic API: claude-opus-5 (story/continuity), claude-sonnet-5 (shot planning, motion
  direction, vision judge), claude-opus-4-8 (refusal fallback). Structured outputs, prompt
  caching.
- Qwen-Image (Apache-2.0) for frames, Qwen-Image-Edit-2511 + Lightning LoRA for end frames.
- Wan2.2-I2V-A14B (Apache-2.0) + Lightning LoRAs for video; SeedVR2-7B and RIFE for optional
  upscale/interpolation; Depth Anything V2 Small + a custom rasterizer for parallax.
- ElevenLabs (hosted) and IndicF5 (AI4Bharat, MIT, self-hosted) for Hindi narration; fal.ai
  Kling 2.5 turbo as an optional paid video lane, user-named shots only.
- FastAPI/ComfyUI on RunPod GPU pods (RTX A6000, A100 80GB, RTX PRO 6000 96GB used so far);
  ffmpeg/Pillow for assembly; pytest, 463 tests passing, with fake GPU/LLM services.
- Git + GitHub, spec-driven development, a 51-entry decision log, Claude Code as an AI
  pair-engineer.
- Dev machine: Windows laptop, Intel i5-1235U, 7.7 GB RAM, no CUDA GPU — all inference in the
  cloud.

## Key decisions
- No agent framework, vs. LangChain/LangGraph/CrewAI: rejected — no model-decided branching, tool
  calls, or retrieval to justify one. A future "tripwire" was named for reconsidering; when it
  arrived, it became a bounded Python loop instead.
- ID-based character consistency, vs. prompting the model to "remember": the shot planner emits
  IDs only, a deterministic compiler pastes in the locked description — fixed seeds plus locked
  text judged enough for shorts.
- Audio generated before shots are planned, vs. the reverse: duration comes from real audio,
  removing the need for forced-alignment tooling.
- Renting GPUs and self-hosting, vs. paid video APIs: about $5–11 per short on paid APIs vs.
  about $1.7 on four rented GPUs; a paid API was added later, only on request.
- Strict permissive-license discipline, vs. the best model regardless: only Apache-2.0/MIT-class
  weights used; several attractive models excluded for restrictive licenses.
- Trusting Abhishek's own blind review, vs. Claude's initial recipe pick: still frames can't show
  motion quality — this led to the judge sampling multiple frames per clip, calibrated against
  his ratings, plus a motion director that writes each prompt from the rendered frame after
  diagnosis showed most failures started there, not in the video model.
- A "hybrid" motion recipe, vs. full quality or full speed: full quality was too slow and the
  fast recipe visibly lost motion, so early full-quality steps plus fast steps became the
  middle ground.
- A firm 20-minute speed target, vs. maximum quality: led to pausing the optional upscale step
  and shipping at a slightly lower resolution.
- ElevenLabs as a third narration engine, vs. recording Abhishek's own voice first: faster to
  ship, needed no GPU pod.

## Engineering highlights
- Character consistency by construction: a contact sheet shows one character recognizable across
  12 separately generated frames.
- Audio/video sync guaranteed by cumulative-rounding math, not manual tuning.
- Reproducibility without sampling-parameter control (the pinned story model rejects a
  temperature setting), via pinned model IDs, per-shot seeds, and hashed prompts.
- Safety-refusal handling: a refusal on thriller content returns a normal-looking empty
  response, so the client checks for it before reading content.
- Crash-safe, resumable, cost-audited runs: atomic state saves and content-addressed caching,
  proven on a real pod where a killed run resumed and reused all finished work at zero added GPU
  time.
- Parallel multi-GPU execution: one rendering service per GPU, work spread across GPU,
  CPU-parallax, and optional paid-API lanes.
- Real debugging (each with a fix and a test): broken "grey mush" video output, a camera
  geometry bug, a motion-detection threshold recalibrated against real clips.
- A pod boot script downloading roughly 107 GB of pinned weights in parallel batches, online in
  about 6 minutes; no heavy ML libraries run on the 7.7 GB RAM laptop (enforced by a test).

## Numbers
- Target: ₹30–50 per video self-hosted vs. ₹1,500+ via paid APIs; ₹5,000/month budget ceiling.
- Dev machine: Intel i5-1235U, 7.7 GB RAM, no CUDA GPU.
- About 12,000 lines of source, about 7,500 lines of tests, 463 tests passing, 51 logged
  decisions.
- First full LLM-layer run: 11 shots, LLM cost about $0.26.
- First fully AI-motion-directed short: 12 shots, all AI motion, 1080x1920, 24fps, 43.4 s,
  silent, rated 4/5 by Abhishek — his first AI-motion output rated above 3. That run: 62 minutes
  wall time on two single-GPU pods, 6,256 seconds (1.74 GPU-hours) of GPU time, cost about $7–8;
  5 of 12 shots passed the judge first try, 4 more after one retry, 3 flagged for human review.
- Motion-recipe comparison: full quality about 3,282 s (55 min) per 5 s clip vs. a fast recipe
  at about 160 s — roughly 20x faster but clearly worse in blind review.
- Planning estimate (not yet measured): roughly ₹1,950/month at daily upload cadence against
  the ₹5,000 ceiling. No YouTube upload, view, or revenue numbers exist yet.

## Status
**Done:** the full pipeline from premise to finished video; the AI motion director and judge
with retries; the hybrid motion recipe; parallel multi-GPU rendering; a production pod boot
script; ElevenLabs narration; a complete offline test rehearsal path. A first fully
AI-motion-directed short was produced and rated 4/5.

**In progress:** the CPU-parallax path and the optional paid-API lane on a real GPU pod;
calibrating judge rules for parallax-only shots; rendering episodes that already have narration.

**Next:** fully unattended end-to-end runs are the next milestone, then colour grading,
hitting the 20-minute target, remaining narration, sound effects and music, and longer episodes
once per-video GPU time comes down.

## Limitations
- Not yet fully unattended end to end; hands-off operation from premise to video is the next
  milestone, not a completed feature.
- Current run time and cost for a short (about an hour, several dollars) exceed the 20-minute
  target; speeding this up is active work.
- Motion quality is good but imperfect even on the best output (4/5): extra people can appear in
  a clip, small props can vanish, hand-object contact can break, water can't rise, and a
  moonlight reflection can render as a flat square.
- Text inside a frame sometimes renders as gibberish; a negative prompt reduces but doesn't
  prove-fix this.
- Post-production polish isn't built yet: no colour grading, no music, no sound effects; the
  one finished AI-motion-directed short is currently silent.
- Training-data provenance of the underlying open models isn't fully checked, needed before
  monetized publishing; commercial-use terms for the hosted narration service need confirming.
- The AI judge's calibration to date stood in for Abhishek's own ratings, not an independent
  blind test, and every real test run needs a paid GPU pod since the laptop can't run any model
  locally.

## Code & demos
Code is available on request — contact Abhishek. Demo outputs include episode 004, a 43.4 s
vertical (1080x1920) silent Hindi thriller short and the first fully AI-motion-directed episode,
rated 4/5; a contact sheet showing one character consistently rendered across 12 frames; a
filmstrip of all 12 clips; every raw generation attempt with its AI-judge review sheet, showing
the generate-judge-retry loop; two Hindi narration samples from ElevenLabs; before/after clips
documenting the parallax path and an early broken video output later fixed; a blind side-by-side
comparison page used to pick the motion recipe; and two earlier, less-polished 16:9 episodes
from before the AI-motion-directed path was built.

## Recruiter Q&A

**Q: What is this project?**
A: A pipeline turning a one-line premise into a short Hindi animated thriller video — Claude
plans the story, open models run on rented GPUs, and a vision judge checks every clip.

**Q: Why "AI Cartoon 0 Cost"? Is it actually free?**
A: Not literally — near-zero marginal cost per video, self-hosting open models on rented GPUs
instead of paying per clip (roughly ₹30–50 per video targeted vs. ₹1,500+ via paid APIs).
Development is free via offline stand-ins; real runs cost money — the first short cost about
$7–8 — against a ₹5,000/month budget.

**Q: How do you keep characters looking the same across shots?**
A: A continuity agent writes one locked description per character. The shot planner references
characters only by ID; a deterministic compiler (no LLM) pastes that description into every
prompt, with a fixed seed.

**Q: How are audio and video kept in sync?**
A: Narration is generated first, and each clip's measured length becomes that shot's length —
duration is never AI-decided. Frame counts use cumulative rounding so video length matches
narration within half a frame.

**Q: Why no LangChain, LangGraph, or CrewAI?**
A: No model-decided branching, tool calls, or retrieval — the things that would justify a
framework. Plain Python is easier to debug and lighter on a low-memory laptop; a future trigger
was named for reconsidering, and when it arrived it became a simple bounded loop.

**Q: What was the hardest problem you solved?**
A: Making AI motion look publishable, fast enough. Most failures traced back to the prompt or
starting frame, not the video model — so Abhishek added a motion director that writes each
prompt from the rendered frame, an AI judge with retries, and a hybrid recipe balancing quality
and speed. The first short built this way was rated 4/5.

**Q: How do you know the AI judge is any good?**
A: Calibrated against clips Abhishek rated himself in a blind comparison: no false passes on the
worst clips, agreement on the best, the same defect named on at least 10 of 13. Judge logic
matched 12 of 13, scored within one point on all 13; pass/fail is plain code, not the model.

**Q: How fast and expensive is it, and why rent GPUs instead of a commercial API?**
A: The first fully AI-motion-directed short took 62 minutes on two rented GPUs, costing about
$7–8, against a 20-minute target. A cost check found roughly $5–11 per short on commercial APIs
vs. $1.7 on four rented GPUs; a commercial API stays wired in only as a fallback.

**Q: How did you think about licensing for eventual monetization?**
A: Only permissively licensed weights were used, tracked with pinned versions; several
attractive models were excluded for restrictive licenses. One gap remains: confirming
training-data provenance.

**Q: How is it tested without a GPU on the dev machine?**
A: Every expensive stage has a permanent offline stand-in, plus fake AI clients and a fake
rendering server, so a full episode rehearsal runs with no GPU or spend — 463 tests must pass
before any commit.

**Q: Did Abhishek build this alone?**
A: He is the sole human contributor. He designed the systems, made the architecture and product
decisions, and directed AI coding agents (Claude Code and Codex) that wrote most of the
implementation, reviewing and testing it himself. Decisions, including ones overriding the AI's
own recommendation, are recorded in a 51-entry decision log.
