# Project DMC

## Pitch

Project DMC turns a single topic into a finished short-form video: it writes a short Hindi
voice-over, records it with a natural AI voice, and animates a body of glowing dots that
physically acts out each line as it is spoken. When the narration says someone is sinking, the
dots sink; when it says someone finally lets go, they loosen and fade. Nobody edits anything by
hand except adding captions.

## Problem

Short-form "reflective" content — calm narrated reels about habits, regret, loneliness,
forgiveness — normally takes a lot of manual work: writing a script, recording a voice, then
finding or hand-animating visuals that fit each sentence. Stock footage and generic motion
graphics don't follow what's being said. Project DMC is built for a Hindi-language short-form
creator publishing to YouTube Shorts, Instagram Reels and TikTok, with one goal: the picture
should do what the words say, literally, at the moment they're said. The look is deliberately
restrained — only abstract glowing dots in a dark void, never clip-art, emojis, faces or literal
objects — aiming for a calm, high-quality feel.

## What it does

Given a topic, an AI writer drafts 8-12 short Hindi lines and decides, for every line, what
physically "happens" and which of 15 named movement types portrays it (for example "heavy" — the
body sinks and darkens, or "dissolving" — it loosens, floats up and fades). The script is voiced
by an AI narrator with word-level timing. A director AI then confirms or fine-tunes each line's
movement, picks a color mood, and sets intensity, accents, the emotional peak and camera
behavior. A deterministic compiler turns those decisions into physics parameters, and a
rendering engine simulates 80 glowing dots reacting to those forces in real time, producing a
finished 30-45 second, 9:16 vertical video (1080x1920, 60 fps) with the AI voice mixed in and a
cinematic bloom pass applied. The only manual step left is adding captions.

For example, on a video about forgiveness, the dots visibly widen, lift and brighten on the line
"forgiveness doesn't erase their mistake, it frees you from that day" — the video's emotional
peak.

## How it works

```
 topic
   v
 WRITER (AI) -> checks -> EDITOR (AI, first-time-viewer read) -> best draft kept
   v
 VOICE GEN (word-level timestamps) -> SEGMENTER (one audio "beat" per line)
   v
 DIRECTOR (AI: movement, color, intensity, peak, camera) -> rule checks
   -> headless replay -> BLIND CRITIC (AI) -> best attempt kept
   v
 COMPILER (deterministic, no AI): movement name -> physics force recipe
   v
 RENDERING ENGINE: 80 dots simulated frame-by-frame under a real-time
   force field (gravity, turbulence, repulsion, flow, cohesion...), 1080x1920 @ 60fps
   v
 POST-PROCESSING (bloom/vignette/grain) -> voice muxed in -> FINISHED MP4
   v
 QA: scored against "viewer guarantees", line-by-line review frames generated
```

Key technical points:
- Stages hand off through saved files, so any stage can be re-run alone without repeating earlier
  (paid) stages. Voice generation is never repeated for an unchanged script; if text is edited
  after voicing, the stale timing is detected and rejected.
- Every AI call uses strict, schema-validated JSON output, with usage measured after each run.
  Voice output is ground truth for timing: timestamps are verified aligned character-for-character
  with the script, and duration is measured from the audio file itself.
- The animation is a continuous physics simulation, not hand-placed keyframes: every frame, a
  velocity is computed for every dot from a stack of active forces (rendered as a single
  point-cloud object, fully vectorized), so shape emerges rather than being authored directly.
  Motion carries across line boundaries by design, and each movement starts within about half a
  second of its line beginning, with a short braking transition between lines.
- Color transitions are calculated in a perceptual color space (OKLab) rather than RGB, because
  RGB blending between some colors visibly passes through the wrong hue; a video uses at most 4
  colors. A safe-zone system also keeps key motion out of the margins where a platform's UI
  (header, captions, share buttons) sits.
- A failed audio mux intentionally fails the whole run rather than producing a silent finished-
  looking video; a watchdog reports genuine render stalls instead of killing on a timer.

**Quality measurement layer.** A fast headless replay of the real simulation predicts a full
render in seconds rather than minutes; a growing script corpus is checked against explicit
"viewer guarantees" (dots stay readable, the body is visibly lit, the climax is the strongest
image, the camera stays calm, fixed bugs stay fixed); a scorecard tool analyzes the finished
video's pixels; and a custom AI judge agent grades whether each line's visuals match its words.

## Stack

- Language: Python, with custom GLSL shader code for point-sprite rendering
- Rendering: Manim Community Edition (OpenGL renderer only), output at 1080x1920, 60 fps
- Math/physics: NumPy (vectorized force simulation), SciPy; data validation via Pydantic
- AI models: OpenAI SDK, model gpt-5.6-sol, strict JSON-schema structured outputs, for the
  writer, editor, director and critic roles
- Voice: ElevenLabs SDK, eleven_multilingual_v2 model, with character-level timestamp alignment
- Video post-processing: ffmpeg (bloom/vignette/grain pipeline, audio muxing, QA frame extraction)
- Dev workflow: Git and GitHub, with Claude Code and Codex used as AI coding agents, plus custom
  project tooling

## Key decisions

- **Physics-based motion, not fixed shapes.** Rejected: an earlier version where an AI chose from
  about 34 preset shape animations. Why: frame analysis showed the shape system couldn't express
  feeling — nothing ever fell, most colors sat at full brightness, motion stopped dead at every
  line boundary. Replaced outright with a continuous force simulation.
- **The writer must specify a concrete "happening" and movement for every line.** Rejected:
  free-form poetic lines. Why: early scripts left the dots nothing to portray; forcing a
  different movement on every line, conversely, produced text that was hard to follow — meaning
  comes first.
- **A separate AI "editor" grades scripts as a first-time viewer, keeping the best draft across
  attempts rather than the last one, and the director confirms movement choices rather than
  inventing freely.** Rejected: rule-based scoring alone, chasing a zero-flag score, and giving
  the director full creative freedom. Why: rule-based checks let through scripts a real viewer
  couldn't follow, a critic can always find something to flag, and written descriptions
  disagreed with on-screen results — so review was changed to grade what the code renders.
- **Color is a named mood resolved to values in code, never chosen directly by an AI, and blends
  in OKLab rather than RGB.** Rejected: letting the AI output raw color values, and standard RGB
  interpolation. Why: keeps visual consistency under deterministic control (capped at 4 colors
  per video), and RGB blending between some color pairs visibly passes through an incorrect hue.
- **Every change is validated against a large, growing script corpus rather than a couple of
  familiar test cases.** Rejected: hand-tuning correction rules against two known scripts. Why:
  dozens of rules tuned that way kept breaking on new scripts.

## Engineering highlights

- Getting abstract particles to read as one specific action tied to one spoken word required the
  full chain — writer, director, compiler and physics — working together, arriving within about
  half a second of each line starting.
- Solved dots visually "welding into a blob" when the body shrinks, with a dot-size rule tied to
  measured on-screen spacing, a minimum body size, and short-range repulsion between dots.
- Solved "history-dependence," where the same movement looked different depending on what prior
  lines left behind (dots piling into a dense core after repeated "gathering"), fixed with local
  dot-to-dot repulsion.
- Fixed a climax movement that was counterintuitively the visually smallest moment in the video,
  because its force only pulled inward; changed to also push outward, roughly doubling the peak
  frame's lit area and brightness.
- Fixed weak opening frames — important for stopping the scroll on short-form platforms — by
  starting the camera zoomed in and lit from frame one instead of leftover spawn positions.
- Built a full internal measurement system from scratch — headless prediction, a large regression
  corpus, pixel-level scoring, and a blind AI judge — turning "this looks better on one video"
  into "this is no worse across hundreds of scripts."

## Numbers

- Output format: 9:16 vertical, 1080x1920, 60 fps; 30-45 seconds; 8-12 lines per script, 5-13
  words per line; 80 dots by default (500-dot cap); 15 named movement types.
- Codebase: about 19,400 lines of production Python, about 8,800 lines of automated tests (25
  test files, about 180 test functions), 332 lines of custom GLSL shader code.
- Physics: 0.126 ms/frame for the full force simulation at 500 dots, versus 15.2 ms/frame for a
  naive (non-vectorized) approach.
- Headless prediction correlates with real renders at r = 0.97, running in about 4 seconds per
  script versus a full render (about 6 minutes; the full 846-script corpus check takes about
  80 minutes).
- Regression corpus: 846 scripts checked against 9 viewer guarantees. Before a methodology
  change, only 9 of 106 scripts passed every guarantee; afterward, on a final exam of 280 fresh
  scripts, 230 (82%) passed.
- Writer quality: 1 of 5 new topics passing quality checks before a round of fixes, 4 of 5 after.
- Typical per-video AI usage: roughly 500 characters of narration audio and tens of thousands of
  OpenAI tokens; the project tracks token/character usage, not dollar cost.
- Built over about 4.5 months of active development (May-September 2026).

## Status

**Done:** the full four-stage pipeline (write, direct, compile, render) works end to end and
produces finished narrated vertical videos. A full quality-measurement system is built and in
use: headless prediction, a large regression corpus, pixel-level video scoring, and a blind AI
judge. The system went through one full architecture rebuild, from fixed-shape animation to
continuous physics, after measurement showed the first approach couldn't express emotion.

**In progress:** the newest renders pass most but not all internal quality guarantees (one recent
render fell short on a light-coverage check on a single line, and on a camera/color-timing
check). A fresh-script quality exam currently passes 82%, not 100%. Visual polish items are
identified but not yet fixed (dots can look flat and similar to each other, neighboring lines can
look too alike, the build toward the emotional peak can be weak), and narrator voice selection is
not yet finalized.

**Next:** finish the remaining visual and pacing fixes, run one full test pass, then one full
corpus validation run, before treating the pipeline as release-ready. Still in active
development, not yet released — no video has been published externally yet.

## Limitations

- Hindi narration only, one narrator per video, and captions are still added by hand; no
  automatic publishing to platforms.
- Does not yet pass all of its own internal quality checks (82% on the most recent fresh-script
  exam, not 100%).
- Known visual gaps: dots can look flat and similar to each other, neighboring lines can look
  alike, and the buildup to the emotional peak can be weak.
- The fast headless prediction tool has drifted in accuracy against the newest renders and is no
  longer fully trusted on its own without a real render to confirm.
- Rendering is compute-heavy (about 6 minutes per video), and the full test suite cannot run in a
  single pass on that hardware due to memory limits.
- Generating new scripts depends on paid third-party AI services; rendering and physics use no AI
  and are free to re-run. Some code from an earlier architecture version is still in use.

## Code & demos

Code is available on request — contact Abhishek. Demo outputs that exist: finished Hindi-narrated
9:16 vertical videos (1080x1920, 60 fps, 30-45 seconds) on topics like forgiveness and nighttime
phone-scrolling habits; a "move catalogue" demo showing all 15 dot movements back to back;
before/after comparison clips showing specific fixes; and frame-by-frame contact sheets used for
quality review.

## Recruiter Q&A

**Q: What is Project DMC in one sentence?**
A: An automated content pipeline that turns a topic into a 30-45 second Hindi-narrated vertical
video, where a body of glowing dots physically acts out each line as it's spoken.

**Q: Why dots instead of stock footage or AI-generated video?**
A: The look is deliberately abstract — only glowing dots in a dark void, no clip-art, faces or
literal objects — so emotion is carried through motion, light and color instead of literal
imagery.

**Q: How does the system decide what the dots should do for each line?**
A: A writer AI plans what happens to "you" for every line and picks one of 15 named movement
types. A director AI confirms or adjusts the choice and sets color mood, intensity and camera. A
deterministic compiler converts that into physics parameters for the rendering engine.

**Q: How is the animation synced to the voice?**
A: Voice generation returns character-level timestamps with the audio. A segmenter splits the
audio into one "beat" per written line, and each beat's motion begins on that line's first
spoken word, typically within about half a second.

**Q: What was the hardest technical problem?**
A: Making the system work reliably on any script, not just the ones it was tuned on — at one
point only 9 of 106 test scripts passed every quality check. The fix was methodological: explicit
"viewer guarantees" checked against a large, growing corpus of 846 scripts, not a couple of
familiar examples.

**Q: Did the architecture change over time?**
A: Yes, substantially. The original version had an AI choose from a fixed set of preset shape
animations; frame analysis showed this couldn't express emotion, since motion stopped dead
between lines. It was rebuilt as a continuous physics simulation, where motion carries meaning
instead of fixed shapes.

**Q: Is it finished? Can I see it live?**
A: Still in active development, not yet released. Abhishek has a specific list of visual and
pacing fixes in progress before a first full validation pass. Finished sample videos exist and
can be shared on request.

**Q: How long does one video take to produce, and what does it cost?**
A: Rendering takes about 6 minutes per video on a laptop. Generating the script and voice for a
new topic uses tens of thousands of AI tokens and a few hundred characters of narration audio;
the project tracks usage rather than dollar cost.

**Q: What role did AI coding assistants play in building this?**
A: Abhishek designed the system, made the product and architecture decisions, and directed AI
coding agents (Claude Code and Codex) that wrote most of the implementation code; he reviewed
and tested every change before accepting it.

**Q: How do you keep the AI writer from producing bad scripts?**
A: Layered checks — a rule-based gate rejects anything countable (line count, words per line,
duration, unusable characters), and a separate AI "editor" that never sees the writer's intent
must fully understand the script on one read. The best of several drafts is kept, and when only a
few lines are weak, only those are rewritten.
