# AI Cartoon 0 Cost: a one-person Hindi AI animation studio

> Local repo: `C:\AI_CARTOON_0_COST` · GitHub: https://github.com/Hacke2367/AI_CARTOON_O_COST (the GitHub name uses the letter "O" in `O_COST`) · Researched 2026-09-25 from the repo at `feature/elevenlabs-voice` @ `c4ec051` (2026-09-17). Every claim below cites a repo file. Numbers are only the ones written in the repo or computed directly from its `state.json` files.

---

## One-line pitch (plain language, for a non-technical recruiter)

You type one sentence, such as "a detective finds a body", and the system writes a Hindi thriller story, draws every scene with the same characters, animates the scenes, adds narration, and puts out a finished vertical video. It runs on rented cloud GPUs and open-source AI models, so each video costs a few dollars. Paid AI video services cost a lot more per video.

## Problem & who it's for

- **Who it's for:** one creator (the owner) who wants to run a **Hindi YouTube animation channel alone**, with no team or studio. The plan covers two series: **Suspense Thriller** (a dark noir "motion comic" look) and **Motivational Journey** (a warm, Ghibli-like 2.5D parallax look). Sources: `project_context.md`, `project_end_goal.md`.
- **The market gap the owner describes:** many YouTube story channels are "cheap slideshows" of AI images with a voiceover. The owner wants cinematic motion so the videos stand out (`project_context.md` §2).
- **The cost problem:** paid video APIs such as Runway or Luma would cost about **₹1,500+ per video**. The original target was **₹30–50 per video** on self-run cloud GPUs, so daily uploads stay affordable (`project_context.md` §2). The whole studio has a **₹5,000/month budget ceiling** (`project_end_goal.md`, `CLAUDE.md` "Hard constraints").
- **The real constraints found during planning:** money was not the hardest limit. The hardest limits were (a) a small laptop (Intel i5-1235U, **7.7 GB RAM, no CUDA GPU**) that cannot edit 80-layer timelines, and (b) YouTube's "inauthentic / mass-produced content" policy. The design answers both (`claude_project_context.md` "Hardware reality", risk register R1–R8).
- **End goal (north star):** a scalable, automated, profitable Hindi animation studio that one person runs. It makes 5–10-minute animated stories, with uploads up to daily. **The current target is shorts first:** a 30–60 s vertical 9:16 Hindi thriller, made from a one-line premise with no manual steps (`project_end_goal.md`, D-035, D-037 in `decision.md`).

## What it does (user-facing features / workflow)

The command:

```
python make_episode.py "detective finds a body"      ->  episodes/NNN/final.mp4
python make_episode.py "<premise>" --fresh           # start a new episode instead of resuming
python make_episode.py "<premise>" --episode-id 004 --fal-shots 3,7   # remake chosen shots on a paid API
python make_episode.py "<premise>" --pause-after {a1,a2,directed,probe}  # inspection stops
```
(`CLAUDE.md` "Commands", `make_episode.py:parse_args`)

What happens, in the user's terms:
1. **Writes the story:** a Hindi script in scenes, one sentence per narration line, with sound-effect cues (Agent A1).
2. **Builds a "story bible":** each character, location and prop gets one locked English visual description. That description keeps the same woman in the same saree across every shot (Agent A2).
3. **Records the narration first,** one sentence at a time. It uses the ElevenLabs voice "Viraj", a self-hosted IndicF5 Hindi voice, or silence for offline tests. Each shot then lasts as long as its spoken sentence.
4. **Plans the shots:** which character, which location, how important the motion is, and a visual prompt for each shot (Agent A3).
5. **Draws each shot** as a 9:16 image (928×1664) with the Qwen-Image model on a cloud GPU.
6. **A "motion director" (Claude vision) looks at each drawn frame** and decides how to animate it. It picks a plain image-to-video clip, a first-and-last-frame clip for a change of state, or a cheap 2.5D parallax camera move when nothing in the picture needs to move. It writes the motion prompt and 3–5 visible checks.
7. **Animates each shot** with the open-source Wan2.2 video model on rented GPUs, several shots in parallel.
8. **A "judge" (Claude vision) watches 16 frames of each clip** and scores it 1–5 against the checks. Failures are retried up to 2 times with a new seed or a rewritten prompt. A shot that never passes ships its best attempt and is flagged for a human.
9. **Assembles the final MP4** with ffmpeg, in sync with the narration.
10. **Everything is saved after every stage** (`episodes/NNN/state.json`). A killed run resumes where it stopped, and no finished frame or clip is paid for twice.

Artifacts per episode: `authored_story.json` (when hand-written), `frames/` + `contact_sheet.jpg`, `clips/` + `motion_sheet.jpg`, `clips/attempts/` (every raw attempt with its judge sheet and verdict), `needs_human/` (shots to review), `final.mp4`, and `state.json` (full audit: LLM token usage, GPU seconds per frame and clip, seeds, hashes, verdicts).

## How it works (architecture, pipeline, data flow)

### Big picture: a laptop "planner" and a cloud-GPU "batch oven"

```
LAPTOP (no GPU: plans, validates, assembles)                 RUNPOD GPU POD ("batch oven": boot, drain queue, shut down)
─────────────────────────────────────────────                ───────────────────────────────────────────────────────────
premise
  │
  ▼  A1 Narrative        claude-opus-5   → Script (Hindi, 1 sentence per line)
  ▼  A2 Continuity       claude-opus-5   → StoryBible (LOCKED English appearance_prompt per character/location/prop)
  ▼  TTS, per sentence   silence | ElevenLabs API | IndicF5 ──────────────────► services/indicf5_server.py (FastAPI)
  │     durations MEASURED from the WAV on disk (this becomes each shot's length)
  ▼  A3 Shot Director    claude-sonnet-5, one call per scene, bible prompt-cached
  │     → ShotDrafts that carry IDs (char_ids, location_id), never appearance prose
  ▼  validators.py       ID checks, T2 quota, audio-word ban, ID-leak ban, bible hygiene (pure Python)
  ▼  prompt_compiler.py  deterministic: style + locked appearance + location + shot text
  │     → CompiledJob, job_id = sha256(prompt|negative|seed|workflow_version)
  ▼  comfy_client.py ──────────────────────────────────────────────────────► ComfyUI: Qwen-Image fp8 → frames (928×1664)
  ▼  motion director     Claude vision per frame → recipe i2v | flf | parallax, motion prompt, 3–5 checks
  ▼  motion_directed.py  one thread per GPU worker (COMFY_WORKERS) + parallax lanes + optional fal lane
  │      ┌─ flf only: end frame ──────────────────────────────────────────► Qwen-Image-Edit-2511 + Lightning LoRA (~10–22 s)
  │      ├─ Wan clip (HYBRID recipe) ──────────────────────────────────────► Wan2.2-I2V-A14B, 720×1280, 49/65/81 frames
  │      ├─ judge: Claude vision on 16 sampled frames → verdict + score 1–5
  │      ├─ retry ≤2 (reseed, or director rewrite) → best attempt
  │      ├─ optional finish (paused by default) ───────────────────────────► SeedVR2-7B ×1.5 + RIFE ×3
  │      ├─ parallax lane ─────────────────────────────────────────────────► services/parallax_server.py (Depth Anything V2 Small, CPU)
  │      └─ fal lane (only shots the user names) ──────────────────────────► fal.ai Kling 2.5 turbo (~$0.21/clip)
  ▼  conform (ffmpeg) + 7 stream guards
  ▼  assembler.py        ffmpeg concat of clips + concat of audio stems + mux → final.mp4
state.json is written atomically after EVERY stage (resume, audit, cost)
```
Sources: `make_episode.py` (module docstring and `run_pipeline`), `schema.py`, `motion_directed.py` docstring, `CLAUDE.md` "Architecture".

### Stage ladder and state

`schema.py` defines one ordered stage ladder: `init → script → bible → audio → shots → validated → compiled → rendered → directed → animated → assembled`. `EpisodeState` (Pydantic) holds everything. It is saved with an atomic `os.replace` write after every stage (`make_episode.py:save_state`). A corrupt state file is renamed aside, not crashed on (`load_state`). Every stage is a plain function over the state, with no framework.

### The load-bearing design invariants (why it works)

From `CLAUDE.md`, `AGENT_ARCHITECTURE.md` (its "12 traps") and the code:

1. **The shot planner outputs IDs, never character descriptions.** `ShotDraft` has `char_ids: ["kamla_villager"]`. `prompt_compiler.py` (with "NO LLM IN THIS FILE" in its docstring) builds the final image prompt from the bible's locked `appearance_prompt`. The model is never asked to describe a character, so it has no way to drift one. `lint_continuity` then checks that every compiled prompt with a character carries that character's locked text.
2. **Audio before shots; `Shot` has no `duration` field.** An LLM-assigned duration "sums to 6 minutes against 9 minutes of narration". Durations come from the measured length of each sentence's WAV. `motion.allocate_frames` uses **cumulative rounding**, so the total video length matches the audio within half a frame by construction (`motion.py:192`). This also removes the need for forced alignment tools (WhisperX/MFA).
3. **Python enforces budgets, never the LLM.** A3 emits `motion_importance` (0–1). Python ranks the shots and demotes the overflow past `max_t2_shots`. Real evidence: in episode 001, **A3 proposed 6 AI-motion shots and Python kept the top 2** (warning in `episodes/001/state.json`).
4. **One A3 call per scene, with the bible prompt-cached.** Context stays the same size, so shot #80 is as grounded as shot #1, and the chunks are independent. Caching is a byte-exact prefix match, so bibles are serialized with `sort_keys=True` and no timestamps or IDs go in the prefix. Episode 001's usage log shows the cache working: the first A3 call wrote 3,820 cached tokens, and each later call read 3,820 from cache.
5. **Hindi narration, English prompts.** Every shot carries `narration_hi` (Devanagari) and `visual_prompt_en`.
6. **Hindi text is never baked into a frame.** Narration, music and SFX stay separate stems. An English dub is then a swapped audio track, not a re-render. The negative prompt bans text, signage, Devanagari, logos and number plates, because Qwen-Image drew gibberish Hindi signs (`config.yaml` `style.negative` comments).
7. **Every result is content-addressed.** Frames, audio clips, end frames, raw clips and finished clips all have IDs that hash their inputs, so a rerun skips work already on disk. Identity hashes (`render_identity`, `motion_identity`) stop a resume if a workflow or setting changed without a version bump (`make_episode.py:_preflight_render/_preflight_motion`).
8. **Checks run before money is spent.** Preflight checks the API key, ffmpeg, the TTS pod (model revision, sample rate), the ComfyUI workers (node classes and model files via `/object_info`) and the parallax service version. It all runs before the first paid token or GPU second.

### The LLM layer (`agents/`)

- `agents/_client.py` is **the only file that imports `anthropic`**. Every call goes through `call_structured()`. It (1) calls `client.messages.parse(output_format=PydanticModel)`, (2) logs token usage before any branching, (3) checks `stop_reason == "refusal"` before touching content, because thriller violence can trigger safety refusals that return HTTP 200 with empty content, (4) checks `stop_reason == "max_tokens"`, and only then (5) returns the parsed output. A refusal gets one retry on a fallback model. `usd_total()` prices the usage log.
- Pinned models (`config.yaml`): `claude-opus-5` for the narrative and continuity agents, `claude-sonnet-5` for the shot director, motion director and judge, and `claude-opus-4-8` as the refusal fallback. Model aliases are never used, so a new model release cannot silently change the output. Opus 5 rejects temperature, so reproducibility comes from pinned IDs, logged seeds and hashed prompts.
- Structured-output schemas are strict: `extra="forbid"` on every model, and no `dict[str, X]` fields (lists plus Python-side indexes instead), because structured outputs need `additionalProperties: false` (`schema.py` banner).
- Validators (`validators.py`, six pure-Python checks): ID existence, T2 quota, continuity lint, audio vocabulary kept out of visual prompts, bible IDs or names leaking into prompts (they would be drawn as text), and bible hygiene. A failed chunk is retried with the error fed back, at most `max_chunk_retries: 2`, then written to `needs_human/`.

### The image layer

`comfy_client.py` (993 lines) talks to ComfyUI's HTTP API. It binds values into exported workflow JSON, submits, polls, downloads, retries, detects blank frames, and logs pod seconds per frame (`GpuRecord`). The model is Qwen-Image fp8 (Apache-2.0), 30 steps, CFG 4, 928×1664 (`config.yaml` `render`). Workflows are **exported from ComfyUI, never hand-written**. Claude exported the Wan workflow headlessly by loading ComfyUI's frontend in Playwright and calling `app.graphToPrompt()`, the same call behind the menu's Export (API) (D-018).

### The motion layer: three generations

1. **M4 (Aug 2026), a tiered design.** T1 is 2.5D parallax: a depth map, a split into 3 layers by depth percentile, disocclusion fill, and a planned camera move with eased crop and a two-sine handheld shake (`services/parallax_server.py`). T2 is AI image-to-video for "hero" shots. The laptop decides the full camera plan (`CameraPlan`), and the pod runs it exactly, with no defaults (`schema.py`, `motion.py`). Every clip goes through **7 guards**: playable, frame count, geometry, fps, codec, liveness (motion delta, calibrated against real clips) and a T2 content guard that catches "grey mush" output (`motion.py:1199`).
2. **M4.5 plus the motion bake-off (Sept 14–15).** T2 moved from Wan2.2-TI2V-5B to **Wan2.2-I2V-A14B with 4-step Lightning LoRAs**. A RunPod bake-off then compared recipes (details under decisions and results).
3. **The "directed" path (Sept 16–17), the current production path** (`motion_directed.py`, `motion_graphs.py`, `agents/motion_director.py`, `judge.py`):
   - **HYBRID sampling recipe** (8 steps at 720×1280, 16 fps): steps 0–2 run the high-noise expert with **no LoRA at CFG 3.5**, where motion gets decided. Step 2–3 runs the same expert **with** the 4-step LoRA at CFG 1. Steps 3–8 run the low-noise expert with its LoRA at CFG 1. The design keeps full-quality motion from the early steps and distilled speed for the rest (D-039, `04f_first_short_plan.md` §4).
   - Graph builders **find binding targets by following the exported graph's links**, not by hard-coded node-ID tables (D-039). Only core ComfyUI nodes are used, no custom nodes (D-008).
   - Workers: one ComfyUI per GPU. Each shot runs its whole loop (end frame → clip → judge → retries → finish) on one GPU thread. Parallax renders run in separate CPU lanes (D-041, D-049).
   - Judge policy is **plain Python**: a clip passes only on `verdict: pass` with **no high-severity issue**. Attempts are ranked by pass, then score, then fewer high-severity issues. A refusal or an unparseable reply becomes a `human` verdict, so the loop always ends (`judge.py`, D-040).

### Audio layer

`tts_client.py` (839 lines) has three engines behind one contract: `silence` (offline), `indicf5` (AI4Bharat IndicF5 on the pod via `services/indicf5_server.py`) and `elevenlabs` (hosted API, D-051). The contract: one request per sentence, **24 kHz mono 16-bit WAV** (asserted, never converted), a deterministic head and tail silence trim, and duration **measured from the file**. Clip IDs hash text, voice, model and settings, so a paid clip is never requested twice. IndicF5 calls are seeded, because an unseeded flow-matching TTS gives a different length each time and that would break shot-list reproducibility.

### Offline-first engineering ("₹0 development")

Every expensive stage has a permanent **offline stub backend**: `render.engine: placeholder`, `audio.engine: silence`, `motion.engine: still`. The whole pipeline and the test suite run on the laptop with no GPU and no API spend (`specs/03` Hard Rule 9, `specs/04` Hard Rule 10). `tests/fake_comfy.py` is a fake ComfyUI server that serves test-pattern files. `tests/test_rehearsal.py` runs a whole directed episode on two fake workers from `validated` to `final.mp4`, including manual hand-offs and a judge retry. A full-size rehearsal of episode 004 (12 shots, 37 graphs) finished offline before any pod was rented (D-045).

### "Manual mode" when there is no API credit

Since 2026-09-16 the `ANTHROPIC_API_KEY` returns HTTP 401 and the owner has no API credit (D-043). `director.mode` and `judge.mode` can be `manual` (`manual_handoff.py`). The run writes request files (frame sheets, `.request.json`), stops with **exit code 3**, and resumes with the same command once the answers (`directions.json`, `.verdict.json`) are written. The answers pass the same validation and drive the same retry loop. `seed_episode.py` puts a hand-written story through the A1–A3 checks, so Claude, working in the dev session, could stand in for the API roles (D-044).

## Tech stack (languages, frameworks, models/APIs, infra)

| Layer | Choice | Source |
|---|---|---|
| Language | Python 3.10 (about 12,000 lines of source, about 7,500 lines of tests) | `CLAUDE.md`, line counts |
| Data contracts | Pydantic v2 (`schema.py` is the contract every stage depends on) | `schema.py` |
| Orchestration | Plain Python fixed DAG. **No LangChain / LangGraph / CrewAI, no MCP in the pipeline** (deliberate) | `AGENT_ARCHITECTURE.md` |
| LLMs | Anthropic Claude via the `anthropic` SDK: `claude-opus-5` (story, bible), `claude-sonnet-5` (shot director, motion director, judge with vision), `claude-opus-4-8` (refusal fallback). Structured outputs, prompt caching, effort settings | `config.yaml`, `agents/_client.py` |
| Image model | Qwen-Image fp8 (Apache-2.0) + Qwen2.5-VL-7B text encoder, in ComfyUI | `MODELS.md` |
| End-frame editing | Qwen-Image-Edit-2511 + Lightning 4-step LoRA (Apache-2.0) | `MODELS.md` |
| Video model | Wan2.2-I2V-A14B (high/low-noise experts, fp8/fp16) + lightx2v 4-step Lightning LoRAs (Apache-2.0); first-last-frame (FLF2V) template | `MODELS.md`, `workflows/` |
| Upscale / interpolation | SeedVR2-7B (Apache-2.0), RIFE v4.26 (MIT), both inside ComfyUI core nodes | `MODELS.md` |
| Depth / parallax | Depth Anything V2 **Small** (Apache-2.0; Base and Large are non-commercial and deliberately excluded) + custom numpy/Pillow rasterizer | `services/parallax_server.py` |
| TTS | ElevenLabs `eleven_multilingual_v2` (hosted), IndicF5 (AI4Bharat, MIT weights) self-hosted | `tts_client.py`, `MODELS.md` |
| Optional paid video | fal.ai queue API, Kling 2.5 turbo, only for shots the user names | `fal_video.py` |
| Pod services | FastAPI + uvicorn (IndicF5 TTS on port 8001, parallax on port 8002), ComfyUI v0.35.2 (one per GPU, ports 8188+) | `services/`, `requirements-pod.txt` |
| Infra | RunPod GPU pods (RTX A6000, A100 80 GB, RTX PRO 6000 Blackwell 96 GB used so far); weights from Hugging Face at pinned revisions; SSH-driven pod setup; tmux; bash boot script | `branch_log.md`, `services/pod_boot_short.sh` |
| Media | ffmpeg/ffprobe (concat, mux, conform, minterpolate, guards), Pillow (contact sheets, judge sheets) | `assembler.py`, `motion.py`, `contact_sheet.py` |
| Testing | pytest (30 test files, 463 tests passing on the latest branch), fake ComfyUI server, fake LLM clients (no API spend in tests) | `tests/`, `branch_log.md` |
| Tooling / process | Git + GitHub (`gh`), spec-driven development (4 specs with about 100 numbered acceptance criteria), decision log (51 entries), branch log, Claude Code as the AI pair-engineer | `decision.md`, `branch_log.md`, `specs/` |
| Dev machine | Windows laptop, Intel i5-1235U, 7.7 GB RAM, Intel Iris Xe (no CUDA). All model inference runs in the cloud | `claude_project_context.md` |

## Key technical decisions & tradeoffs (what was chosen, what alternatives, WHY)

Each has a full entry (date, why, alternatives rejected) in `decision.md` (D-001…D-051) or the design docs.

1. **No agent framework: plain Python + Pydantic + direct SDK calls.** The rule: a framework earns its weight only with model-decided control flow, tool calling, or retrieval, and the story → bible → shots chain has none of the three. CrewAI was called "actively wrong" (non-deterministic chatter hurts reproducibility), and LangGraph "defensible but premature". The laptop's 7.7 GB of RAM and debuggability also counted. The named **"tripwire"** for adopting LangGraph was a vision feedback loop. When the judge loop was built, the team deliberately kept it as a **bounded `for` loop inside the fixed DAG** (`AGENT_ARCHITECTURE.md`, `judge.py`, `04e_judge_design.md`).
2. **Structural consistency instead of prompting for it.** The shot planner emits IDs, and a deterministic compiler assembles the appearance text. The rejected option was asking the model to "remember the character", with character LoRA training deferred. Fixed seeds plus locked text were judged enough for 10-shot shorts (`DEVELOPMENT_PLAN.md` M3).
3. **Duration is an audio fact.** TTS runs **before** shot planning (the obvious order is the reverse), and per-sentence TTS removes forced alignment (AGENT_ARCHITECTURE Trap 1).
4. **Rent GPUs and self-host open models instead of paying per clip for video APIs.** A price check on 2026-09-16 put a 45 s short at about **$5 on the cheapest API (Veo 3.1 Lite)** and **$8–11 on Kling 3.0 / MiniMax H3**, against an estimated **about $1.7 on 4× RTX PRO 6000** RunPod GPUs. RunPod stayed, with the rule that "an API comes back only if it is cheaper per usable clip" (D-035, `04f_first_short_plan.md` §3). A hosted API (fal.ai) was later added **on request only**, for shots the open model can't do (D-049).
5. **"The GPU is a batch oven, never a workbench."** Plan everything offline, boot, drain the queue, shut down, because idle pod time costs more than the hourly rate. Stub backends keep development at ₹0 (`CLAUDE.md` "Hard constraints").
6. **Licence discipline as a hard rule.** Only permissively licensed weights. FLUX [dev] is excluded (non-commercial). Depth Anything V2 is used at Small only, since Base and Large are CC-BY-NC. MiniMax H3's open weights were rejected because the licence forbids showing outputs in the US, EU, UK and Korea. LTX-2.x was rejected for its community licence. InsightFace weights and Ultralytics YOLO (AGPL) are avoided in the judge design. `MODELS.md` tracks weights and training-data licences separately, because a permissive weight licence can sit on a non-commercial corpus (`MODELS.md`, D-021, D-034, `04e`).
7. **Switching the video model (D-008).** The first T2 session gave "grey mush" at about 9 min per clip on Wan2.2-TI2V-5B, which has no ComfyUI distillation LoRA. The move to **Wan2.2-I2V-A14B + 4-step Lightning LoRAs** means 4 model evaluations per clip instead of 40. Rejected: staying on 5B, LTX-2.x (licence and camera instability), HunyuanVideo / FramePack (Tencent licence), and H100/H200 (the speedup doesn't match the price).
8. **The bake-off, and trusting the owner's blind review over Claude's own review.** Claude declared the fast recipe the winner (D-033). The owner's **blind** ratings on a shuffled comparison page overturned it (D-034), because 3–6 still frames per clip cannot show motion quality. Lesson recorded: the reviewer has to watch motion, which led to the judge sampling 16 frames and being calibrated against the owner's ratings.
9. **The HYBRID recipe** (a few full-guidance steps without the LoRA, then distilled steps) is the compromise. Full quality (PRO) took about 55 min per 5 s clip, and pure 4-step (FAST) lost motion ("moves the body by force", per the owner) (D-034, D-036, D-039).
10. **AI-written motion prompts plus an AI judge.** The owner's diagnosis after round 1: most failures started **before** the model ran. The start frame already showed the action's end (for example, the lantern was already raised), or the prompt asked for the artifact ("churning up white spray" made a speedboat wake). So a vision "motion director" writes each prompt from the actual frame, flags frames that already show the end state (re-rendered once), and picks the recipe (D-035, D-038).
11. **No second test round (D-036).** The owner chose "the first real short is the test" over another comparison round, to save time and money.
12. **Speed and cost targets set by the owner:** "speed first" (D-035), then **at most 20 minutes per short** (D-048). This led to pausing the SeedVR2 upscale (it was **21% of GPU time**, 111 s per clip) and delivering 720×1280. The code, graphs and weights were kept, not deleted (D-049). The director can also pick **CPU parallax** for still shots, with a Wan fallback if the judge rejects it (D-049).
13. **Model weights on the pod's local disk, not a network volume.** Round 1 lost **5–15 min per model load** reading weights off a RunPod network volume. The boot script refuses a network filesystem under `models/` (D-042, D-045).
14. **Rejected guidance and attention tricks, backed by measurements or source reading:**
    - **NAG** dropped: reading ComfyUI's source showed its core node patches an attention output that Wan never calls, so it would silently do nothing. Replaced by SLG + CFG-Zero* (D-026).
    - **CK int8 attention** sped the 2-pass PRO graph up by about 38% but made the 4-step FAST graph **7.5% slower** and changed a clip (SSIM 0.775), so it was dropped (D-033).
    - **SeedVR2 3B vs 7B:** 3B was no faster (140 s vs 145 s) and slightly softer, so 7B stayed (D-033).
15. **ElevenLabs as a third audio engine (D-051)** instead of first recording the owner's own voice for IndicF5. It is faster to ship and needs no pod. Tradeoffs are recorded: commercial use needs a paid ElevenLabs plan, and the key's plan tier could not be read.
16. **Process decisions:** a branch per feature, the full test suite gates every commit, a push only with the owner's OK, every decision logged in the same commit, and no merge or delete without the owner's go-ahead (D-002…D-007, D-022).

## Hard problems solved / engineering highlights

- **Character consistency across shots, by construction.** The episode 004 contact sheet (`episodes/004/frames/contact_sheet.jpg`) shows the same woman (`kamla_villager`: maroon saree, yellow dupatta, braid, lantern) across 12 separately generated 9:16 frames of a moonlit stepwell.
- **Audio/video sync, guaranteed by math, not tuning.** Cumulative-rounding frame allocation plus a minimum-length adjustment that keeps the total frame count exact (`motion.allocate_frames`, `_enforce_minimum`).
- **Reproducibility without sampling parameters.** Opus 5 returns HTTP 400 on `temperature`, so determinism comes from pinned model IDs, seeds (`base_seed + shot_index`), prompt and bible hashes, and sorted-ID prompt compilation (Go/No-Go criterion 6).
- **Safety refusals handled.** Refusals on thriller content come back as HTTP 200 with empty content. `stop_reason` is checked before the content is read, with a client-side fallback model. This is why the Batch API and server-side fallbacks were weighed against each other (`CLAUDE.md` "Claude API specifics").
- **Crash-safe, resumable, cost-audited runs.** An atomic `state.json` after every stage, content-addressed caches, and pod seconds logged per frame and clip (D-013). Kill-and-resume was proven on a real pod: episode 002 was killed after 4 clips, and the restart took shots 0–3 from cache at 0 s of pod time (`branch_log.md` 2026-09-15).
- **A vision-LLM quality gate with calibration.** The judge's gate against the owner's 13 rated bake-off clips requires no false pass on clips rated 1–2, the same winners, and the owner's defect named on at least 10 of 13. Claude's stand-in verdicts passed the gate: 0 false passes, the defect named on **12 of 13**, scores within one point on **all 13**. This was explicitly noted as **not blind** (D-043).
- **Parallel multi-GPU execution on commodity pods.** One ComfyUI per GPU, each with its own user, temp and database directories, a unique upload and output prefix per shot and attempt, and shot-level work stealing across GPU, parallax and fal lanes (D-041, D-042, D-049).
- **Debugging real GPU failures:**
  - the "grey mush" Wan output (the wrong model/node, plus a T2 content guard calibrated on the broken clips: stddev 11.2 vs a healthy 45.6);
  - a T1 pan/tilt geometry bug;
  - a liveness threshold calibrated from real clips (0.4, where the slowest real move measured 0.66);
  - a runner that miscounted ComfyUI's `LoadVideo` input as an output;
  - an untargeted `/interrupt` that killed another job;
  - an SSH key path with a space;
  - T1 timeouts on long shots.

  Each got a fix and usually a test (`branch_log.md`, D-018, D-019, D-046).
- **Production pod boot script** (`services/pod_boot_short.sh`):
  - downloads 14 pinned weight files (about 107 GB at fp8) four at a time;
  - starts the frame workers before the 77 GB of motion weights finish, so frames render during the download;
  - upgrades ComfyUI to v0.35.2 itself;
  - finds ComfyUI's venv Python (a `/proc/<pid>/exe` symlink pointed at the wrong Python);
  - forces LF line endings from a Windows checkout (`.gitattributes`).

  Boot took about 6 min on the real run (D-045, D-046).
- **Working inside a 7.7 GB RAM laptop.** No local torch (a test asserts that laptop modules import none of the pod dependencies), and no image bytes in `state.json`. Laptop-side watchers died twice from low memory during pod sessions, which became a working rule (`branch_log.md` 2026-09-15).
- **Test-suite hygiene.** A flaky test came from the laptop's `.env` leaking pod URLs into tests. An autouse fixture now stubs the `.env` loader (`tests/conftest.py`, `branch_log.md` 2026-09-17).
- **Knowing the model limits and writing stories around them.**
  - Neither Wan nor Qwen-Image-Edit can raise a water level.
  - Wan turns a moon reflection on still water into a "square block of light".
  - An end-frame edit that names what to keep **adds** objects.

  Story rules now avoid these (D-046, `04g_short_mix_handoff.md` §4).

## Results, metrics, scale (numbers only if found in the repo)

**Engineering scale**
- 72 commits from 2026-08-16 to 2026-09-17, 7 local branches, 6 on GitHub (`git log`, `branch_log.md`).
- About 12,000 lines of Python source and about 7,500 lines of tests in 30 test files; **463 tests passing** on the latest branch (`branch_log.md`, `feature/elevenlabs-voice`).
- 4 formal specs with about 100 numbered acceptance criteria (21 + 20 + 25 + 35 IDs), 51 logged decisions, 4 implementation plans plus 6 follow-on plans and handoffs (`specs/`, `decision.md`).

**Episodes produced** (from each `episodes/NNN/state.json`):
| Episode | What | Result |
|---|---|---|
| 001 "चालीस मिनट" (2026-08-18) | First run of the real LLM layer: 11 shots (9 T1, 2 T2 after the quota) | A1/A2/A3 ran on the pinned models, and a `final.mp4` was assembled from placeholder frames and audio. **LLM cost ≈ $0.26** (6 calls, computed from the usage log with the repo's price table) |
| 002 "आख़िरी सवारी" + 003 "तीन बजकर सात मिनट" (2026-09-15) | 11 shots each, real pod, stopped at clips | **22 frames + 22 clips** (RTX A6000). The owner judged the motion not publishable ("bahut jyada AI feel") (D-021) |
| 004 "सूखी बावड़ी" (2026-09-17) | **First directed 9:16 short**, 12 shots, all AI motion | `final.mp4` at 1080×1920, 24 fps, **43.4 s**, silent. **The owner rated it 4/5**, the first AI-motion output above 3 (D-047) |
| 005–008 (2026-09-17) | Seeded stories with directions written ahead; 007 and 008 narrated by ElevenLabs (34.8 s and 30.4 s, 142 credits) | Not rendered yet |

**Episode 004 run metrics** (D-046, `episodes/004/state.json`, `branch_log.md` Open problems):
- **Wall time: 62 min** from workers ready to `final.mp4`, on two 1-GPU RTX PRO 6000 pods; boot about 6 min before that.
- **GPU time: 6,256 s (1.74 GPU-h)**:
  - HYBRID clips: 20 at a 216 s mean;
  - finish (SeedVR2 + RIFE): 12 at 111 s;
  - frames: 13 at 37 s;
  - end frames: 5 at 22 s.
- Split: first-attempt clips 2,558 s, **retries 1,765 s** (860 s on shots that never passed), finishes 1,334 s, frames 487 s, end frames 113 s.
- **Judge loop:** 5 of 12 shots passed first time, 4 more after a retry, and 3 went to `needs_human` at score 3 (8 retries in all).
- **Cost to the owner: about $7–8** for the short (`04g_short_mix_handoff.md`).

**Motion bake-off, round 1** (2026-09-15, A100 80 GB at about $2/h; D-027–D-034):
- **PRO** (Wan full quality, 40 steps, CFG 3.5): **3,282 s (about 55 min) per 5 s clip**. Owner's blind score 4.
- **FAST** (4-step LoRAs): **about 160 s gen, about 6 min** for the full chain including the upscale, so **about 20× faster**. Blind scores 3, 3, 3, 1.
- **CAMF** (Fun-Camera): 2, 3, 1, 1. The old pipeline (V0): 2, 1, 1, 1.
- Lightning keyframes: **10 s vs 100 s** without the LoRA.
- Session: about 3 h 40 min of pod work, about **$7.40** estimated.

**Other measured numbers**
- Qwen-Image frame: about 91–105 s on an RTX A6000 (1664×928), 37 s mean on an RTX PRO 6000 (928×1664).
- A T1 parallax clip: 40.6 s of pod time (about 0.85 s per frame, CPU-bound).
- Wan A14B 4-step clip: 122–175 s on an A6000.
- Weights: fp8 set 106.5 GB, fp16 extras 68.5 GB, downloaded at about 500 MB/s (D-045, D-046, `04g` §5).

**Cost model (planning estimates, not measured):**
- GPU about ₹55 per 8-minute video; LLM layer about ₹72 per episode on Opus, about ₹25 with Sonnet + batching.
- About ₹1,950/month at daily cadence vs the ₹5,000 ceiling (`claude_project_context.md` §6, `AGENT_ARCHITECTURE.md` §4).
- Current estimates for the 20-minute target: about 28 min on 2 GPUs with a parallax/Wan mix, about 15–17 min on 4 GPUs, about $2–2.5 of GPU plus about $1 of API per short (D-048). **Not yet measured.**

**No audience metrics:** the repo has no YouTube upload, view, or revenue data.

## Current status & timeline (done / in progress / planned; dates from git/docs)

**Timeline**
- **2026-08-14:** vision document `project_context.md` (file date). **2026-08-16:** first commit, strategy and architecture docs.
- **2026-08-16 → 08-18:** M0 walking skeleton + M1 real LLM layer; episode 001 end to end with the real story, bible and shots (2026-08-18). M2 audio (IndicF5 server + client) built.
- **2026-08-19:** M3 first real pod render (Qwen-Image, 4 frames).
- **2026-08-22 → 08-25:** M4 first real motion session. T1 parallax works; T2 on TI2V-5B broken; geometry bug fixed.
- **2026-08-27:** M4.5 plan to switch to Wan2.2-I2V-A14B (committed 2026-09-14).
- **2026-09-13/14:** working rules, tracking files (decision log, branch log, end goal) and branch reorganization.
- **2026-09-15:** real pod session with episodes 002/003 (22 frames, 22 clips). Owner verdict: not publishable. The **motion bake-off** ran on an A100 the same day, and the owner's blind review overturned the fast recipe.
- **2026-09-16:** motion director, judge, parallel clip path and pod boot script built offline (tests 302 → 423). Manual hand-off mode added after the API key failed.
- **2026-09-17:** **first directed short (episode 004) rendered on 2 GPUs and rated 4/5.** Then built on `feature/short-mix`: parallax chosen by the director, fal.ai on request, the upscale finish paused. Episodes 005/006 seeded for a one-GPU $2 pod day. ElevenLabs narration added, with episodes 007/008 narrated (`feature/elevenlabs-voice`, **local only, not pushed**).
- No commits after 2026-09-17 as of this research (2026-09-25).

**Done:** M0–M3; M4/M4.5 motion runs on pods; the directed path (director, judge, HYBRID, parallel workers, boot script); a first short at 4/5; ElevenLabs narration engine; offline rehearsal tests.

**In progress / not yet run for real** (`04g_short_mix_handoff.md`):
- parallax in the directed path on a real pod;
- any fal.ai call (no `FAL_KEY`);
- the judge's parallax rules (uncalibrated);
- the narrated shorts 007/008 on a pod.

**Planned, in the owner's recommended order** (`04g` §2, D-047): API credit (unattended runs plus the API judge calibration) → colour grade LUT (M5) → the next short measured against the 20-min limit → narrator voice → SFX and music → long-form later. Long-form waits because an 8-minute episode at episode 004's rate would be about **19 GPU-h**, far over the 2 GPU-h per video "Scale" gate (D-047).

**Branch state:** nothing merged into `main` since 2026-09-14. The directed path lives on the stacked feature branches `m4.5 → motion-bakeoff → first-short → short-mix → elevenlabs-voice`. Merges wait for the owner's go-ahead (`branch_log.md` Layout).

## Limitations & known issues

- **Not yet unattended.** The Anthropic API key returns 401 and there is no credit, so for episodes 002–008 **Claude (in the dev session) wrote the stories, directions and judge verdicts by hand** through files. The "premise → MP4 with zero manual steps" gate item is **not met** for the current path. It was met only for the LLM stages in episode 001 (D-017, D-043, D-044, D-047).
- **Too slow and too costly for the owner's own bar:** 62 min and about $7–8 per 43 s short vs the **20-minute** limit (D-048).
- **Motion quality:** the best output is 4/5. Known model failures:
  - extra people appear in clips (episode 003: 3 of 7 clips);
  - a "hidden" face gets shown;
  - props vanish;
  - hand–object contact breaks;
  - water can't rise;
  - moon reflections turn square.

  Round 1 found no publishable recipe (D-034, `branch_log.md` Open problems).
- **Text in frames:** Qwen-Image still renders gibberish Devanagari or English text (plates, brands, UI). A negative prompt reduces it, but it isn't proven fixed.
- **Not built:** colour grade LUT, music, SFX; the only finished short (004) is **silent**.
- **Licensing gap that blocks monetized publishing:** the **training-data provenance** of Wan2.2, the Lightning LoRAs, Depth Anything V2, SeedVR2 and others is not investigated (`MODELS.md` O1). ElevenLabs needs a paid plan for commercial use, and the plan tier is unknown.
- **Judge calibration** was Claude's, **not blind**. The real API judge (`claude-sonnet-5`) has never run.
- **A keyframe fix can't be undone** except by hand-editing `state.json` (episode 004 shot 11) (D-046).
- **Human gates** after the story and bible are designed but off by default (MVP scope).
- The laptop can't run models locally, and every real test needs a paid pod.
- **Demo media is gitignored** (`episodes/`, `RESULTS/`), so GitHub holds code and docs only.

## Demo assets (file paths to videos/images/screenshots/sample outputs; GitHub URL if any)

**GitHub:** https://github.com/Hacke2367/AI_CARTOON_O_COST (code and docs; public or private not verified). Media folders are gitignored, so every asset below is **local only**.

Best picks:
- `C:\AI_CARTOON_0_COST\episodes\004\final.mp4`: **the first directed short**, "सूखी बावड़ी", 43.4 s, 1080×1920, silent, rated 4/5 (30 MB).
- `C:\AI_CARTOON_0_COST\episodes\004\frames\contact_sheet.jpg`: 12 frames with a **consistent character** across shots (strong visual for a portfolio).
- `C:\AI_CARTOON_0_COST\episodes\004\clips\motion_sheet.jpg`: a filmstrip of the 12 clips.
- `C:\AI_CARTOON_0_COST\episodes\004\clips\attempts\`: 97 files with every raw attempt (`*.raw.mp4`), its judge frame sheet (`*.sheet.jpg`), request and verdict JSON. This shows the judge/retry loop.
- `C:\AI_CARTOON_0_COST\RESULTS\voice_samples\episode_007_narration.wav`, `episode_008_narration.wav`: Hindi ElevenLabs narration for the two narrated thrillers. Also `voice_Viraj.wav`, `voice_Harsh.wav`, `voice_DanishKhan.wav`, `voice_AlokK.wav` (voice audition).

Process and "before/after" material:
- `C:\AI_CARTOON_0_COST\RESULTS\1_T1_parallax_GOOD.mp4`: a T1 2.5D parallax clip (note: it shows Devanagari signage, a known issue).
- `C:\AI_CARTOON_0_COST\RESULTS\2_T2_wan_BROKEN.mp4`, `3_T2_wan_BROKEN.mp4`: the early "grey mush" AI-motion failure (a good debugging story).
- `C:\AI_CARTOON_0_COST\RESULTS\5_pan_right_FIXED.mp4`: after the pan geometry fix. `RESULTS\4_all_camera_moves.jpg` and `RESULTS\0_filmstrip.jpg`: camera-move sheets.
- `C:\AI_CARTOON_0_COST\episodes\_smoketest\allmoves\*.mp4`: one parallax clip per camera move (push-in, pan, tilt, pull-out).
- `C:\AI_CARTOON_0_COST\RESULTS\bakeoff\r1\compare.html` + `blind\A_1.mp4 … D_3.mp4` (13 clips) + `verdicts.json` + `key.json`: **the blind A/B bake-off page** and the owner's ratings. `keyframes.html` shows the end keyframes. `RESULTS\bakeoff\r1up3b\*_7b_vs_3b_f40.jpg` compares the two SeedVR2 sizes.
- `C:\AI_CARTOON_0_COST\episodes\002\frames\contact_sheet.jpg`, `episodes\003\frames\contact_sheet.jpg`, and `episodes\002\clips\motion_sheet.jpg`: the earlier 16:9 episodes (boatman, mill watchman).
- `C:\AI_CARTOON_0_COST\episodes\001\final.mp4`: the M0/M1 walking-skeleton output (placeholder frames, 130 KB). It proves the chain, not the visuals.
- Story/JSON samples: `episodes\00N\authored_story.json`, `episodes\004\directions.json`, `episodes\004\state.json` (full audit trail).

Docs worth showing a technical reviewer: `AGENT_ARCHITECTURE.md` (design and 12 traps), `decision.md` (51 decisions), `04e_judge_design.md`, `04f_first_short_plan.md`, `MODELS.md` (licence audit).

## Why this impresses a recruiter (2 angles: non-technical impact, technical depth)

**Non-technical impact**
- One person built a working "AI film studio" pipeline. It turns a one-line idea into a narrated, animated vertical video in Hindi, with consistent characters, on a laptop with no graphics card, using rented cloud GPUs.
- It is run like a business. There is a monthly budget ceiling, costs are measured per video, paid APIs were compared with self-hosting before choosing, and speed and cost targets came from the owner (at most 20 minutes per short). The owner scored results in blind reviews and did not accept "good enough" (a 4/5 rating only came on the first directed short).
- Risk awareness beyond the tech: YouTube's "mass-produced content" policy, commercial licences for every AI model, voice-cloning consent, and "never bake Hindi text into the picture" so an English dub is just a new audio track.
- Disciplined execution: every decision written down with its reasons and rejected alternatives (51 entries), tests before every commit, and clear handoff documents.

**Technical depth**
- A production-style **multi-stage generative pipeline**: an LLM planning layer (structured outputs, prompt caching, refusal handling, token-cost logging) feeding self-hosted diffusion image and video models on multi-GPU ComfyUI workers, with a vision-LLM **generate → judge → retry** loop.
- Clear system thinking: character consistency and A/V sync are guaranteed **by construction** (ID-only planning plus a deterministic prompt compiler; audio-first timing with cumulative-rounding frame allocation), not by prompt tuning.
- Reliability engineering: content-addressed caching, atomic checkpoints, resume after a kill (proven on a real pod), identity hashes against config drift, preflight checks before paid work, 7 media guards, and a fake GPU server for offline rehearsal. **463 tests** run with no GPU and no API spend.
- Evidence-driven ML ops: a formal bake-off on a rented A100, measured per-stage timings, A/B tests of attention kernels and upscalers (kept or dropped on measured numbers), and reading ComfyUI's source to find a guidance node that silently did nothing.
- Deliberate architecture calls: no LangChain, LangGraph or CrewAI, a named "tripwire" for when a framework would be justified, and a bounded loop when that moment came.

## Likely recruiter Q&A (grounded in the repo)

1. **Q: What is this project in one sentence?**
   A: An automated pipeline that turns a one-line premise into a short Hindi animated thriller video. Claude writes and plans the story, open-source image and video models run on rented RunPod GPUs, and a vision-AI judge checks every clip (`project_end_goal.md`, `make_episode.py`).

2. **Q: Why is it called "0 cost"? Is it free?**
   A: Not literally. The idea is near-zero **marginal** cost. It self-hosts permissively licensed open models on rented GPUs instead of paying per clip for services like Runway or Luma (original target: ₹30–50 per video vs ₹1,500+ via APIs). All development and the whole test suite run at ₹0 through offline stub backends, and caching means nothing is paid for twice. Real GPU runs cost money: the first short cost about $7–8, and the budget ceiling is ₹5,000/month (`project_context.md`, `04g_short_mix_handoff.md`). The owner hasn't written down why they chose the name.

3. **Q: How do you keep the same character looking the same across shots?**
   A: A continuity agent writes one locked English description per character. The shot planner may only reference characters by ID, and a deterministic Python compiler, with no LLM, pastes the locked description into every image prompt. A linter checks that 100% of prompts carry it, and seeds are fixed per shot (`prompt_compiler.py`, `validators.py`). The episode 004 contact sheet shows the result.

4. **Q: How are the audio and video kept in sync?**
   A: Narration is generated first, one sentence at a time, and each WAV's measured length becomes that shot's length. The schema has no LLM-written duration field on purpose. Frame counts use cumulative rounding, so total video length matches total audio within half a frame (`schema.py`, `motion.allocate_frames`).

5. **Q: Why no LangChain, LangGraph or CrewAI?**
   A: The pipeline is a fixed linear DAG with no model-decided control flow, no tool calls and no retrieval. Those are the three things that justify a framework. Plain Python + Pydantic is easier to debug, reproducible and lighter on a 7.7 GB laptop. The team named a vision feedback loop as the "tripwire" for LangGraph. When the judge loop arrived, it was kept as a bounded `for` loop (`AGENT_ARCHITECTURE.md`, `judge.py`).

6. **Q: Which AI models does it use?**
   A: Claude Opus 5 (story and bible) and Claude Sonnet 5 (shot planning, motion director, judge) through the Anthropic SDK. Qwen-Image for frames, Qwen-Image-Edit-2511 for end frames, Wan2.2-I2V-A14B with Lightning LoRAs for video, SeedVR2 + RIFE for the optional upscale, Depth Anything V2 Small for parallax. ElevenLabs or IndicF5 for Hindi narration (`config.yaml`, `MODELS.md`).

7. **Q: What was the hardest problem?**
   A: Making AI motion look publishable, fast enough. The first clips were judged "too AI". A formal bake-off found full quality took about 55 min per 5 s clip and the 4-step fast recipe lost motion. The root-cause analysis showed most failures came from prompts and start frames, so the owner added an AI motion director that writes prompts from the actual frame, an AI judge with retries, and a HYBRID sampling recipe. The first short with this path scored 4/5 (D-021 → D-047).

8. **Q: How do you know the AI judge is any good?**
   A: It has a calibration gate against the owner's 13 blind-rated clips: no false passes, the same winners, and the owner's defect named on at least 10 of 13. Claude's stand-in verdicts passed it (12 of 13 defects named, scores within one point on all 13). The repo says honestly that this wasn't blind and that the real API judge still has to be calibrated once there is API credit (D-040, D-043). Pass/fail policy is in Python, not the model: any high-severity issue fails the clip.

9. **Q: How fast and how expensive is it right now?**
   A: The first short (43 s, 12 shots) took 62 minutes on two RTX PRO 6000 GPUs, 1.74 GPU-hours, about $7–8. The owner's target is 20 minutes, and the planned levers are more GPUs in parallel, CPU parallax for still shots, fewer retries, a paused upscale, and API mode instead of hand-answered steps. These are estimated at about 15–17 min on 4 GPUs but not yet measured (D-046, D-048, D-049).

10. **Q: Why rent GPUs instead of using a video API like Veo or Kling?**
    A: A price check on 2026-09-16 estimated about $5 per short on the cheapest API and $8–11 on Kling/MiniMax, against about $1.7 on four rented RTX PRO 6000s. Self-hosting also means no credit limits once workflows are set up. A paid API (fal.ai Kling 2.5 turbo, about $0.21/clip) is wired in only for specific shots the user names (D-035, D-049).

11. **Q: How did you handle licensing for a monetized channel?**
    A: Only permissively licensed weights (Apache-2.0 or MIT), recorded per model with pinned revisions in `MODELS.md`. FLUX [dev], Depth Anything V2 Base/Large, MiniMax H3 and LTX were excluded for their licences. Training-data provenance is tracked separately. It is still open for the motion models and blocks monetized publishing until it's checked.

12. **Q: How is it tested when the laptop has no GPU?**
    A: Every stage has a permanent offline backend (placeholder frames, silent audio, still clips), plus fake LLM clients and a fake ComfyUI server (`tests/fake_comfy.py`). A rehearsal test runs a whole directed episode on two fake GPU workers to `final.mp4`. There are 463 tests, and the suite gates every commit (`tests/`, `CLAUDE.md` Working rule 6).

13. **Q: What happens if a run crashes halfway, or a GPU pod dies?**
    A: State is saved atomically after each stage, and every frame and clip is content-addressed. Rerunning the same command resumes: finished work is reused at 0 GPU seconds, and only missing shots are sent to the pod. This was proven on a real pod with episode 002 (`make_episode.py`, `branch_log.md` 2026-09-15).

14. **Q: Is it finished? What's left?**
    A: The visual recipe for shorts is settled (4/5). It isn't yet unattended: the API key is invalid, so the AI roles were answered by hand. The remaining work is a colour grade, music and SFX, the 20-minute speed target, story rules for known model limits, the training-data licence check, and later, long-form episodes (D-047, `04g`).

15. **Q: Did you build this alone? What was the role of AI coding tools?**
    A: The owner is the sole human contributor (all 72 commits). The repo shows the work was done with Claude Code as an AI pair-engineer: 59 commits carry a Claude co-author trailer, and `decision.md` records the owner's directives (constraints, verdicts, strategy) and Claude's implementation and analysis. The owner set the product direction, the budget and speed limits, and made the quality calls through blind reviews. *(How the owner wants to frame this is an open question below.)*

## Open questions for the owner (things you couldn't determine)

1. **The name.** What does "0 cost" mean to you, and why is the GitHub repo `AI_CARTOON_O_COST` (letter O)? Is "near-zero marginal cost / ₹0 offline development" the right framing?
2. **Publishing.** Has any video been uploaded to YouTube or Instagram? Is there a channel name, or any views, subscribers or revenue? The repo has none.
3. **Progress after 2026-09-17.** Did the one-GPU pod day for episodes 005/006 or 007/008 happen? Are there newer rendered or narrated shorts that aren't in the repo?
4. **API credit.** Is the Anthropic API key working again? Has any run been fully unattended, and has the API judge been calibrated?
5. **Shareable assets.** Which videos or images can go on the portfolio? Should `episodes/004/final.mp4` get narration or a grade first? Is the GitHub repo public?
6. **AI-assisted development.** How do you want the Claude Code collaboration presented (59 of 72 commits co-authored by Claude; the decision log names Claude as the implementer)? What parts did you personally design or code?
7. **Total spend.** What have you spent to date across all pod sessions, APIs and ElevenLabs? The repo has only fragments: about $7.40 for the bake-off, about $7–8 for episode 004, and 142 ElevenLabs credits.
8. **Licensing.** Is the ElevenLabs plan paid (commercial rights)? Has the training-data check (`MODELS.md` O1) been done?
9. **Branches.** Do you plan to merge the directed path into `main`? And push `feature/elevenlabs-voice`, which is currently local only?
10. **Second niche.** Is the Motivational Journey (warm 2.5D parallax) series still planned, or is the focus thrillers only?
11. **Timeline start.** Did work start before 2026-08-14 (the vision doc date)? The older spike scripts (`testing_connection.py`, `image_testing.py`, SD 1.5 on RunPod) come before the plan.
