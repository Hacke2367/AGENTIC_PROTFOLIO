# Resume: Abhishek Maurya

Source: `C:\Users\abhishek maurya\OneDrive\Desktop\Documents\abhishek_resume_pdf.pdf`
(transcribed 2026-09-25). The GitHub and LinkedIn links in the PDF are hyperlinks whose URLs
were not extractable, so the owner needs to provide them.

**Contact:** abhishekmlen25@gmail.com · +91 9930692220 · GitHub (URL pending) · LinkedIn (URL pending)
· Mumbai, Andheri (E)

## Profile
Research-driven AI/ML Developer focused on architecting production-grade Generative AI pipelines
and robust microservices. A strong proponent of comprehensive system visualization and
theoretical planning before execution, which enables the autonomous delivery of end-to-end,
crash-resilient solutions. Driven by complex technical challenges, with a clear vision to build
scalable, high-impact core technologies.

## Education
B.Sc. in Information Technology, Tolani College of Commerce, Mumbai University (2022–2025).
CGPA 8.0/10. Relevant coursework: Linear Algebra, Statistics, Probability.

## Skills
- **Generative AI & LLMs:** LangChain, LangGraph, Hugging Face, Gemini, FAISS, Prompt
  Engineering, Fine-tuning (PEFT, QLoRA, Unsloth), RAG Pipelines
- **Machine Learning:** Scikit-learn, Regression, Classification, Clustering, Feature Engineering
- **Deep Learning:** TensorFlow, PyTorch, CNN, ANN
- **Backend & MLOps:** FastAPI, Flask, Docker, MLflow, DVC, CI/CD, REST APIs, Async Processing
- **Programming & Data:** Python, SQL, MongoDB, NumPy, Pandas, Matplotlib
- **Tools & Visualization:** Git, GitHub, Streamlit, Manim CE, Claude Code

## Work experience
**AI Intern, Nullclass (Remote)**, June 2025 – August 2025
- Designed and delivered 7 self-built, production-grade AI chatbot projects in 1 month of a
  3-month internship.
- Built systems using RAG pipelines, multilingual NLP, vector search, and LLM-based reasoning
  with Hugging Face and LangChain.
- Implemented a medical Q&A bot on the MedQuAD dataset, with translation support and
  chunk-based retrieval.
- Developed dynamic knowledge-base expansion through automated web scraping and vector DB
  updates.
- Extended capabilities with sentiment-aware responses and multimodal chat using Gemini
  (text + image input/output).
- Used FastAPI, FAISS, Deep Translator, and Google Gemini, with a focus on scalable, real-world
  deployments.

## Projects (as listed in the resume)
**1. AutoShorts: Automated AI Video Generation Pipeline.** Python, LangGraph, Gemini, Manim CE,
ElevenLabs. GitHub repo.
- A 4-phase asynchronous microservice pipeline that covers the whole video lifecycle: autonomous
  topic discovery, web scraping, script generation, and 3D rendering.
- An "Under-run Gate": Pydub in-memory silence trimming (dBFS thresholding) with millisecond
  timelines, for frame-perfect audio-visual sync.
- Atomic file operations (`os.replace`) and job-centric isolation, so the pipeline can resume
  from any point of failure.
- SHA-256 hash-based caching (idempotency) to eliminate redundant LLM calls, and
  `asyncio.Semaphore` to respect third-party API rate limits.

**2. Vehicle Insurance MLOps Pipeline.** Python, Scikit-learn, DVC, Git, MongoDB.
- An end-to-end MLOps pipeline for vehicle insurance claim prediction, built from modular
  scripts for reproducibility across environments.
- Git and DVC for dataset and model-artifact versioning.
- MongoDB for data handling, with data ingestion decoupled from model training.

## Certifications & internships
- Internship Certificate, Novadita Infotech (2025): 3 basic ML projects completed under
  mentorship.
- Internship Certificate, Nullclass: a 3-month AI internship building 7 GenAI projects with
  LLMs, LangChain, and FastAPI.
- Course Completion, Nullclass (2025): an AI/ML course covering LLMs, NLP, and RAG workflows.

## Notes for the portfolio
- The resume's AutoShorts stack says Gemini, but the repo now uses OpenAI `gpt-5.6-luna`, with
  Gemini as a fallback (see `projects/01_*.md`).
- Owner decision (2026-09-25): portfolio projects come only from `docs/projects/`, never from
  this resume's Projects section. Vehicle Insurance MLOps and the Nullclass chatbots are not
  featured as projects.
