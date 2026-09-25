"""PROTOTYPE, throwaway: shared content for the step 02 front-page UI directions (?variant=...).

Remove once the owner picks a direction; the winning layout is rebuilt properly in the real
templates. Every fact here is taken from knowledge/0N_*.md or docs/resume.md.
Round 1 (a, b, c): owner kept B's structure, rejected A and C. Round 2 (d, e): B evolved into
an "agent console" with two skins.
"""

VARIANTS = {
    "d": ("Console: Geist, electric blue", "prototype_front_page/console.html"),
    "e": ("Console: Satoshi, saffron", "prototype_front_page/console.html"),
    "b": ("Round 1: Workbench", "prototype_front_page/b.html"),
}

PERSON = {
    "name": "Abhishek Maurya",
    "role": "AI/ML developer building generative AI pipelines and agent systems",
    "place": "Mumbai",
    "email": "abhishekmlen25@gmail.com",
    "profile": ("Research-driven AI/ML Developer focused on architecting production-grade "
                "Generative AI pipelines and robust microservices. A strong proponent of "
                "comprehensive system visualization and theoretical planning before execution, "
                "which enables the autonomous delivery of end-to-end, crash-resilient solutions. "
                "Driven by complex technical challenges, with a clear vision to build scalable, "
                "high-impact core technologies."),
    "cue": ("Every project here has its own agent. Ask it what the project does, how it's "
            "built, or what broke along the way."),
}

# Owner-approved tag ideas (2026-09-26); each needs a one-line proof from the knowledge files.
FLAGS = [
    ("--always-building", "5 projects: 4 working, 1 still being built."),
    ("--claude-code-power-user", "AutoShorts, DMC, AI Cartoon and this site were built by "
                                 "directing Claude Code as the coding team."),
    ("--cost-obsessed", "A full AI run in AutoShorts costs about $0.036."),
    ("--measure-before-trust", "DMC's headless replay predicts real renders at r = 0.97."),
    ("--1000+-tests", "1,180 tests in DOT_TO_IMAGE, 1,082 in AI Lawyer."),
    ("--hinglish-first", "4 of the 5 projects speak Hindi or Hinglish."),
]

# Draft by Claude; the owner will rewrite it later.
WHY_HIRE = {
    "serious": ("I take an idea all the way to a working system, and I measure before I trust "
                "it. AutoShorts turns a topic into a researched, voiced data video for about "
                "$0.036 of AI calls. DOT_TO_IMAGE runs 30 automated checks on every puzzle "
                "before a human signs off. AI Lawyer's legal search puts the right section in "
                "its top 10 results 90% of the time, in English and Hinglish. I direct "
                "AI coding agents the way a lead directs a team: I design the system, make the "
                "calls, and review what ships."),
    "fun": ("I already built five AI agents just to talk about my projects. Give me real "
            "problems before I build a sixth."),
}

NAV = [("/projects", "#projects"), ("/why-hire-me", "#why-hire-me"), ("/about", "#about"),
       ("/contact", "#contact"), ("/resume", "/static/resume.pdf"), ("/feedback", "#feedback")]

SKILLS = [
    ("Generative AI & LLMs", "LangChain, LangGraph, Hugging Face, Gemini, FAISS, Prompt Engineering, "
                             "Fine-tuning (PEFT, QLoRA, Unsloth), RAG Pipelines"),
    ("Machine Learning", "Scikit-learn, Regression, Classification, Clustering, Feature Engineering"),
    ("Deep Learning", "TensorFlow, PyTorch, CNN, ANN"),
    ("Backend & MLOps", "FastAPI, Flask, Docker, MLflow, DVC, CI/CD, REST APIs, Async Processing"),
    ("Programming & Data", "Python, SQL, MongoDB, NumPy, Pandas, Matplotlib"),
    ("Tools & Visualization", "Git, GitHub, Streamlit, Manim CE, Claude Code"),
]

EXPERIENCE = {
    "title": "AI Intern", "org": "Nullclass (remote)", "when": "Jun 2025 – Aug 2025",
    "points": [
        "Delivered 7 self-built, production-grade AI chatbot projects in the first month of a "
        "3-month internship.",
        "RAG pipelines, multilingual NLP, vector search and LLM reasoning with Hugging Face and "
        "LangChain.",
        "A medical Q&A bot on the MedQuAD dataset, with translation and chunk-based retrieval.",
        "Multimodal chat with Gemini (text and image), built on FastAPI and FAISS.",
    ],
}

EDUCATION = {"degree": "B.Sc. Information Technology",
             "school": "Tolani College of Commerce, Mumbai University", "when": "2022 – 2025",
             "note": "CGPA 8.0/10. Coursework in linear algebra, statistics and probability."}

CERTS = [
    ("Internship Certificate", "Nullclass", "3-month AI internship: 7 GenAI projects"),
    ("Internship Certificate", "Novadita Infotech, 2025", "3 ML projects under mentorship"),
    ("Course Completion", "Nullclass, 2025", "AI/ML: LLMs, NLP and RAG workflows"),
]

PROJECTS = [
    {"slug": "autoshorts", "name": "AutoShorts", "short": "AutoShorts", "status": "Working",
     "pitch": ("Give it a topic and it researches real data, writes a Hinglish script, records "
               "an AI voice-over and renders a finished 9:16 data-infographic Short. No video "
               "editor involved."),
     "stats": [("$0.036", "for a full AI run of 30 calls"),
               ("7", "animated chart templates"),
               ("0.00 s", "audio/video drift, down from up to 6 s")],
     "stack": ["Python", "LangGraph", "OpenAI", "ElevenLabs", "Manim", "FFmpeg"]},
    {"slug": "dmc", "name": "Project DMC", "short": "DMC", "status": "In active development",
     "pitch": ("A body of 80 glowing dots physically acts out each line of a Hindi voice-over "
               "at the moment it is spoken. When the narration says someone is sinking, the "
               "dots sink."),
     "stats": [("r = 0.97", "headless replay vs real renders"),
               ("846", "scripts in the regression corpus"),
               ("5", "LLM roles with code gates between them")],
     "stack": ["Python", "NumPy physics", "Manim OpenGL", "GLSL", "ElevenLabs"]},
    {"slug": "dot_to_image", "name": "DOT_TO_IMAGE", "short": "DOT_TO_IMAGE", "status": "Working",
     "pitch": ("Turns AI art or a photo into a print-ready connect-the-dots puzzle with 1,000 to "
               "3,000 numbered dots, checked by 30 automated tests before a human approves it."),
     "stats": [("2,763", "dots on the record A2 poster"),
               ("$5.38", "for ~573 AI image generations"),
               ("1,180", "automated tests")],
     "stack": ["Python", "Chinese Postman routing", "Simulated annealing", "PDF preflight"]},
    {"slug": "ai_cartoon", "name": "AI Cartoon", "short": "AI Cartoon", "status": "Working",
     "pitch": ("Type one sentence and it writes a Hindi thriller, draws every scene with "
               "consistent characters, animates it and adds narration, on rented GPUs instead "
               "of paid per-clip video APIs."),
     "stats": [("₹30–50", "target cost per video, vs ₹1,500+ on paid APIs"),
               ("1.74", "GPU-hours for a 12-shot all-AI-motion short"),
               ("463", "tests passing")],
     "stack": ["Python", "ComfyUI", "Open models", "Cloud GPUs", "ElevenLabs"]},
    {"slug": "ai_lawyer", "name": "AI Lawyer: Legal Flight Simulator", "short": "AI Lawyer",
     "status": "In progress, 4 of 20 steps",
     "pitch": ("A flight simulator for Indian traffic-police stops: practise against an AI "
               "officer, magistrate and witness in English or Hinglish. Educational only, "
               "never legal advice."),
     "stats": [("0.90", "recall@10 hybrid search, vs 0.805 keyword"),
               ("81 / 81", "fake citations caught"),
               ("1,107", "verbatim units of the Motor Vehicles Act")],
     "stack": ["Python", "FastAPI", "Qdrant", "BM25", "PostgreSQL (planned)"]},
]

COMMAND_NAMES = ("usp", "pipeline", "hardest-problem", "philosophy")

# Static answers for the project slash commands: instant, no LLM call, owner-approved later.
COMMANDS = {
    "autoshorts": {
        "usp": ("It doesn't wrap a video API. Every chart, voice cut and sound effect is "
                "generated in code, with the animation exactly in sync with the narration, for "
                "about $0.036 of AI calls per video."),
        "pipeline": ["Topic ideas, checked against real web data", "Human approves one topic",
                     "Search, scrape and AI data extraction", "Hinglish script on a Python timing budget",
                     "AI voice, trimmed and measured", "Manim render from 7 chart templates",
                     "Mix: voice, sound effects, ducked music", "Finished 9:16 Short, captions optional"],
        "hardest-problem": ("Every video was silently losing its ending: 0.76 to 6.08 seconds "
                            "cut across 10 sampled jobs, once a whole closing scene. Measurement "
                            "showed the voice was trimmed after the animation had rendered on "
                            "untrimmed timing. Fix: trim audio first, rewrite the timeline, then "
                            "render. All seven templates now match audio length exactly."),
        "philosophy": ("Build, don't wrap. Code-driven animation instead of editor templates or "
                       "a video API, so every video is exact, data-driven and repeatable in "
                       "bulk. Extras wait until there's audience data to justify them."),
    },
    "dmc": {
        "usp": ("The picture does exactly what the words say, at the moment they're said. 80 "
                "dots are driven by a real-time physics simulation, not keyframes, so shape and "
                "emotion emerge from forces."),
        "pipeline": ["Topic", "AI writer and editor draft the Hindi script",
                     "AI voice with word-level timing", "Director AI: movement, colour, peak, camera",
                     "Compiler, no AI: movement to physics forces",
                     "Physics render: 80 dots, 1080×1920, 60 fps", "Bloom pass and voice mux",
                     "QA against the viewer guarantees"],
        "hardest-problem": ("The first design, an AI picking from about 34 preset shape "
                            "animations, couldn't express feeling: frame analysis showed nothing "
                            "ever fell and motion stopped dead at every line. It was rebuilt as "
                            "a continuous force simulation, then validated on 846 scripts with a "
                            "headless replay that predicts real renders at r = 0.97."),
        "philosophy": ("Measure, don't eyeball. Every change is checked against hundreds of "
                       "scripts, not two familiar ones. And the AI never picks raw colours: "
                       "moods are resolved in code, so the look stays under deterministic "
                       "control."),
    },
    "dot_to_image": {
        "usp": ("Puzzles that artists hand-draw over weeks, built and quality-checked in "
                "minutes: 1,000 to 3,000 dots routed along the drawing's natural strokes, with "
                "30 automated checks before a human approves print."),
        "pipeline": ["Image: AI art, a photo or a maze", "Trace and reduce to a skeleton",
                     "Build a graph of the strokes", "Route it: Chinese Postman, not TSP",
                     "Place the dots", "Number them with simulated annealing",
                     "30 validation checks", "Vector PDF and human review",
                     "Poster or KDP book, preflighted"],
        "hardest-problem": ("Placing up to 3,000 numbers with no overlaps is NP-hard, solved "
                            "with a greedy seed plus 200,000 iterations of simulated annealing. "
                            "The sneakiest bug: every number sat exactly on its own dot for a "
                            "month while the metrics showed 99.47% placement and zero errors. "
                            "Only rendering the PDF and looking caught it, so that's now a rule."),
        "philosophy": ("Quality over volume. Research into KDP's rules moved the goal from mass "
                       "production to premium puzzles, and no human override can bypass the "
                       "validator: the only way past a failed check is fixing the puzzle."),
    },
    "ai_cartoon": {
        "usp": ("A one-person Hindi animation studio: one sentence in, a finished thriller "
                "short out, on rented GPUs and open models instead of paid per-clip video APIs, "
                "with characters that stay consistent across every shot."),
        "pipeline": ["Premise, one sentence", "Hindi script", "Story bible with locked character looks",
                     "Narration, duration measured from audio", "Shot list of IDs, not prose",
                     "Prompt compiler, no LLM", "Frames with Qwen-Image",
                     "Motion director and Wan2.2 video on parallel GPUs",
                     "AI judge with retries", "ffmpeg assembles the final video"],
        "hardest-problem": ("Keeping a character's look identical across separately generated "
                            "shots. The shot planner outputs only IDs, never appearance text, "
                            "and a deterministic compiler pastes in each character's locked "
                            "description, so a look can't drift. One character stays "
                            "recognisable across 12 separately generated frames."),
        "philosophy": ("No framework without a reason. Plain Python instead of LangChain or "
                       "CrewAI, because nothing needed model-decided branching. Python, not the "
                       "LLM, enforces budgets and timing, and every expensive step is cached, "
                       "so nothing is generated or paid for twice."),
    },
    "ai_lawyer": {
        "usp": ("Planned as a flight simulator for a traffic-police stop: rehearse against an "
                "AI officer, magistrate and witness before it happens for real. Built so far is "
                "the legal engine underneath: verbatim law, search in English and Hinglish, and "
                "a citation checker with no LLM. It never gives legal advice."),
        "pipeline": ["Official Motor Vehicles Act PDF, checksum-verified",
                     "Text extraction, watermarks and footnotes filtered",
                     "Structural chunker: 1,107 verbatim units",
                     "Hybrid search: embeddings plus BM25", "Citation checker, no LLM"],
        "planned": ["Three AI calls per turn: gatekeeper, stage, bench", "Chat interface"],
        "hardest-problem": ("Search in two languages. Keyword search missed about twice as many "
                            "Hinglish questions as English ones, mostly vocabulary gaps like "
                            "\"helmet\" versus the Act's \"protective headgear\". Combining "
                            "embedding search with keyword search lifted recall@10 from 0.805 "
                            "to 0.900."),
        "philosophy": ("Foundation before flash, and never advice. The legal engine was built "
                       "before any AI character, so characters never sit on ungrounded law. An "
                       "earlier \"advice\" feature was cut, because a disclaimer doesn't "
                       "survive a feature that actually gives advice."),
    },
}


def context(variant: str) -> dict:
    keys = list(VARIANTS)
    i = keys.index(variant)
    name, template = VARIANTS[variant]
    return {"person": PERSON, "skills": SKILLS, "exp": EXPERIENCE, "edu": EDUCATION,
            "certs": CERTS, "projects": PROJECTS, "flags": FLAGS, "why": WHY_HIRE, "nav": NAV,
            "command_names": COMMAND_NAMES, "variant": variant, "variant_name": name,
            "template": template, "skin": variant,
            "prev": keys[i - 1], "next": keys[(i + 1) % len(keys)]}
