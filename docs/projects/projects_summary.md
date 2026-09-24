# Projects Summary

This is a short overview of the 5 portfolio projects. The full write-ups, which serve as the
agent's knowledge base, are in the same folder as `0N_*.md`. All facts come from the repos as
read on 2026-09-25; nothing inside the projects was modified.

| # | Public name (proposed) | Folder | Repo | Status |
|---|---|---|---|---|
| 1 | AutoShorts | `C:\MANIM_VIDEOS_CODE_TEMPALTE` | `Hacke2367/Auto_shorts_engine_1` (public) | Working; latest branch not pushed |
| 2 | Project DMC | `C:\Project_Dmc` | `Hacke2367/CONTENT_2` (private) | Active dev, `main` empty |
| 3 | DOT_TO_IMAGE | `C:\DOT_TO_IMAGE` | `Hacke2367/DOT_TO_IMAGE` (private) | Working; CI failing (2 tests) |
| 4 | AI Cartoon (near-zero cost) | `C:\AI_CARTOON_0_COST` | `AI_CARTOON_O_COST` (visibility unknown) | Episode 004 done; not unattended |
| 5 | AI Lawyer: Legal Flight Simulator | `C:\AI_LLM_LAWYER` | `Hacke2367/AI_LAWYER` (private) | In progress: 4/20 steps |

---

## 1. AutoShorts (`01_manim_code_video_template.md`)
- **What it does:** turns a topic into a finished 9:16 Hinglish data-video Short. It works in
  two halves that hand off through a `jobs/<id>/` folder.
- **AI pipeline:** OpenAI (`gpt-5.6-luna`, with Gemini as fallback), Tavily web research, a
  LangGraph extraction step, guarded script writing, and ElevenLabs voice.
- **Renderer:** Manim with 7 chart templates, FFmpeg mixing (SFX plus ducked music), and
  burned-in captions. Rendering runs in parallel on RunPod CPU pods.
- **Stories worth telling:**
  - Every video was losing 0.76–6.08 s at the end; fixed by trimming audio before rendering.
  - Visuals ran up to 24 s ahead of the voice because segment names did not match.
  - The switch to OpenAI was made on cost and verified with a replay harness.
- **Numbers:** ~120 files and ~32k lines, 190 tests, 12 finished videos (29–95 s), 106 older
  renders. One full AI run took 30 LLM calls and cost about **$0.036**.
- **Timeline:** Jan–Sep 2026, 50 commits.
- **Demo assets:** `VIDEOGIF/` (4 GIFs, April, made before the September fixes) and
  `jobs/*/output/`.
- **Issues:**
  - **SECURITY:** `demo_output_result.txt` on the public `main` appears to contain an API key.
    Revoke the key and purge the file from git history.
  - GitHub `main` still holds the April version.
  - Finished videos are 15 fps, but the config says 30.

## 2. Project DMC (`02_project_dmc.md`)
- **What it does:** turns a topic into a 30–45 s Hindi-narrated 9:16 video. One body of 80
  glowing dots acts out each spoken line as it is spoken.
- **Pipeline:**
  - 5 LLM roles (topic check → writer → editor → director → blind critic) using
    `gpt-5.6-sol`, strict JSON output, and code gates between the roles.
  - ElevenLabs voice with per-character timestamps, a segmenter, and a compiler with no LLM.
  - A custom numpy physics engine, rendered in Manim OpenGL at 1080×1920 and 60 fps, with an
    ffmpeg bloom pass for the glow.
- **Engineering story:**
  - The shape-based design was rebuilt as a force-based physics design, driven by frame
    measurements.
  - An 846-script test corpus with a headless replay predicts renders at r=0.97.
  - Only 9 of 106 scripts passed every viewer guarantee at first; now 82% of 280 fresh scripts
    pass. The writer went from 1 in 5 topics passing to 4 in 5.
- **Numbers:** ~19k lines of code, ~8.8k lines of tests, custom GLSL shaders, 333 commits
  (2026-05-15 to 2026-09-25), 43 PRs.
- **Hero demo:** `outputs\review_fix76\maaf_3_gap005.mp4`.
- **Issues:**
  - The repo is private and `main` is empty.
  - The latest render still fails 2 of the 8 guarantees.
  - Work sits on the stacked, unmerged branches `fix/74`–`fix/76`.

## 3. DOT_TO_IMAGE (`03_dot_to_image.md`)
- **What it does:** a CLI, `d2d`, turns AI art, photos, patterns or mazes into print-ready dot
  puzzles with 1,000–3,000 dots. Each puzzle goes through 30 automated checks and a human
  review, then becomes a KDP book or an A2/A3 poster.
- **Algorithms:** Chinese Postman stroke routing (chosen over TSP) and simulated annealing
  for number placement with no overlaps. The same input always gives byte-identical PDFs.
- **Numbers:**
  - 39 clean posters, with a record of 2,763 dots on one poster.
  - A 10×3 product catalogue and a Kids KDP book.
  - ~573 AI image generations for about **$5.38** in total.
  - 79 modules (~23.8k lines), 1,180 tests, 198 commits.
- **Feature lines:**
  - `_character`: a sketch guide plus stained-glass character puzzles.
  - `_challenge`: Artist Challenge Books.
  - `_flipbook`: flipbooks from AI video, with an agent that repairs bad frames.
  - `v31-maze-a3`: A3 mazes, awaiting the owner's approval.
- **Issues:**
  - CI on `main` is failing: 2 `--help` colour-code tests.
  - All ~11 GB of outputs exist only on this laptop.
  - The repo is private.

## 4. AI Cartoon, near-zero cost (`04_ai_cartoon_0_cost.md`)
- **What it does:** turns a one-line premise into a short vertical Hindi thriller.
  - Claude writes the story, the character bible and the shot plan.
  - Qwen-Image and Wan2.2 run through ComfyUI on rented RunPod GPUs.
  - A Claude vision "motion director" writes each clip's motion prompt, and a vision "judge"
    checks each clip, with up to 2 retries.
- **"0 cost":** means near-zero cost per video. Self-hosted open models replace per-clip APIs,
  which cut the target from ₹1,500+ to ₹30–50 per video. Development and tests run offline at
  ₹0, and caching avoids paying twice.
- **Engineering:**
  - Character consistency and audio/video sync are guaranteed by design, not by prompt tuning.
  - No agent framework, by choice.
  - Runs resume after a crash without paying again.
  - Licences are tracked per model.
  - The A100 bake-off result was overturned by the owner's blind ratings.
  - 463 tests need no GPU, including a fake ComfyUI server.
- **Headline result:** episode 004 is 43.4 s at 1080×1920. It took 62 min on 2 GPUs and was
  rated 4/5. It costs about $7–8.
- **Numbers:** 72 commits (2026-08-16 to 2026-09-17), 51 decisions, 4 specs.
- **Demo assets:** `episodes\004\final.mp4`, `episodes\004\frames\contact_sheet.jpg`,
  `RESULTS\bakeoff\r1\compare.html`, and `RESULTS\voice_samples\`. All media is gitignored.
- **Issues:**
  - The Anthropic key returns 401, so the pipeline cannot yet run unattended.
  - 62 min per short against the owner's 20 min target.
  - Episode 004 is silent.
  - The video-model licence check is open and blocks monetized publishing.

## 5. AI Lawyer: Legal Flight Simulator (`05_ai_llm_lawyer.md`), work in progress
- **What it does:** lets users practise an Indian highway traffic-police stop against AI
  characters (officer, magistrate, witness), in English or Hinglish. It is educational only:
  no legal advice, no document drafting, and law is always shown verbatim.
- **What's built:**
  - The Motor Vehicles Act is downloaded from the official source, verified by checksum, and
    split into 1,107 verbatim chunks.
  - A 100-question test set, half English and half Hinglish.
  - Hybrid search reaches recall@10 of **0.90** committed and 0.925 in a prototype, against a
    0.805 keyword baseline.
- **Citation checker (no LLM):** 81 of 81 fake citations caught, and 0 of 4,943 real citations
  wrongly flagged. 1,082 offline tests.
- **Design:** 44 logged decisions, at most 3 LLM calls per turn, PostgreSQL over SQLite, and
  scope cut after a self-commissioned feasibility critique.
- **Status:** 4 of 20 steps merged (Sep 14–19). Step 05 (the Qdrant index) is blocked on
  downloads, memory and Docker. Step 06 (the citation checker) is in review. There is no
  LLM, UI or game logic yet; only `/health` runs.
- **Red lines:** never legal advice and never an invented law. The portfolio agent must say
  the same.

---

## Cross-project patterns
- **AI-assisted development:** most commits in all 5 projects carry a Claude or Codex
  co-author, and the decision logs name the AI as the implementer. Proposed framing:
  *"Architect & product owner. Designed systems, made decisions, directed AI coding agents."*
- **Visibility:** 3 repos are private. The only public repo has a leaked-key issue.
- **Shared strengths:** cost discipline ($0.036/run, $5.38 for ~573 images), measurement-driven
  decisions, large offline test suites, and decision logs.

## Open questions for the owner
1. Resume content source (philosophy, skills, education, experience, contact).
2. The LLM provider/key for the portfolio agent.
3. How to show the private repos: "available on request"?
4. Whether the AI-assisted framing above is OK.
5. Whether the public names in the table are OK.
6. Hero demo per project: OK to publish the media? English subtitles for the Hindi videos?
7. Whether any video or product is published or sold (views, sales)?
8. Whether model names (`gpt-5.6-sol`, `gpt-5.6-luna`) can be quoted as they are.
9. Whether the AutoShorts key has been revoked and the latest branch pushed.
