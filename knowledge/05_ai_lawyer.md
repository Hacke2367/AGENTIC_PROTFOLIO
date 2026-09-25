# AI Lawyer: Legal Flight Simulator

## Pitch

AI Lawyer: Legal Flight Simulator is an educational practice simulator where ordinary people and
law students rehearse a stressful real-life legal moment — being stopped by traffic police on an
Indian highway — against AI characters such as the officer, a magistrate, and a witness. It works
like a flight simulator for legal situations: users learn how the law and procedure actually work
before facing it for real. It is strictly educational, and it is not legal advice.

## Problem

- Most people in India don't know their rights or the procedure when police stop them: document
  checks, fines, drunk-driving tests, what an officer may or may not demand. Reading law doesn't
  help under pressure.
- The guiding idea: like pilots training in simulators, a citizen or law student can "crash test"
  reactions before facing real police or courts — selling confidence under pressure, not
  legal-education content.
- India replaced its old criminal codes (IPC, CrPC, Evidence Act) with new ones (BNS, BNSS, BSA)
  in July 2024, making a tool for the changed section numbers timely.
- Built for citizens and law students. Users can type English or Hinglish; statute text is always
  shown in its original English.
- Possible later audiences (not committed): law-college training, plus more scenarios.

## What it does

**Planned experience (not usable yet):**
- Case prep: an AI character asks questions and builds a "Case File" of facts, vehicle,
  documents, and witnesses.
- The encounter: a WhatsApp-style chat where an AI officer checks documents, raises allegations
  (e.g. overspeeding, no pollution certificate), and applies pressure; the user responds.
- An optional, short magistrate/courtroom stage, and a "Meta-Pause" where the user can ask a
  mentor character legal questions without breaking the story.
- A clickable law engine: any cited section opens the verbatim legal text, never a paraphrase.
- Scoring and debrief: a Judge character scores the user, penalizes things like citing fake law,
  and shows "Legal Context cards" behind each cited section.
- Fixed-button controls (Get Help / You Reply / I Have a Doubt); free typing is limited to the
  doubt box as anti-abuse.

**What exists today:** none of the above is usable yet. What is built is the legal-data engine
underneath it — see "How it works."

## How it works

**Built today:**
- Official-source ingestion with checksum: the Motor Vehicles Act, 1988 is downloaded over HTTPS
  from India's official government law portal and verified against a pinned checksum before use.
  If the source is ever silently replaced, the pipeline refuses to rebuild until reviewed.
- PDF text extraction that filters out the watermark, footnotes, and page numbers without ever
  editing the underlying legal text.
- A structural chunker, driven by the Act's own table of contents, producing 1,107 verbatim units
  (sections, sub-sections, provisos, explanations, state amendments), each an exact
  character-offset slice, never paraphrased.
- Hybrid retrieval: multilingual dense embedding search combined with BM25 keyword search, using
  exact (not approximate) vector search for reproducibility.
- A 100-question bilingual evaluation set (50 English, 50 Hinglish), written before the chunker
  existed so chunking choices couldn't bias the evaluation.
- An LLM-free citation checker: a deterministic parser (no LLM, no network call) recognizing
  English and Hinglish citation forms and classifying each as verified, unverified, or
  not-in-the-Act.

**Planned (not built yet):**
- Session-state storage (mode, case file, turn count, strikes, score) in a database.
- A three-call AI pipeline per turn: a fast "Gatekeeper" call that routes, rewrites risky
  first-person text into third person, and raises flags; a "Stage" call that plays the
  in-character reply from the Case File; and a "Bench" call that judges, scores, and builds the
  Legal Context cards from verbatim text only.
- A filter blocking obvious prompt-injection text before any AI call runs, and a chat frontend.

## Stack

- Python 3.12, FastAPI, Pydantic, pdfplumber for PDF extraction.
- Qdrant for vector search, with local, quantized multilingual embedding models plus BM25 keyword
  search.
- PostgreSQL (planned, for session state), Docker Compose for local infrastructure.
- GitHub Actions for CI, pytest, ruff, and strict mypy type-checking.
- Planned AI layer: Groq (Llama-3 family) for the fast routing call, Anthropic Claude for the
  role-play and judging calls; exact model versions not finalized. Planned frontend: Streamlit.

## Key decisions

- Scope cut to one feature and one scenario, rejecting an earlier two-feature design (a tutor plus
  a multi-scenario, eight-agent simulator) — a feasibility review judged the original plan too
  large for a solo build, so V1 keeps only the highway-checkpoint simulator.
- At most three AI calls per user turn, rejecting a chain of roughly five sequential calls — that
  many would mean 10-20 second turns, too slow for chat, so eight character personas are packed
  into three calls instead.
- All "advice" output removed, rejecting an earlier "Actionable Advice" block — a disclaimer
  doesn't survive a feature that actually gives advice, so the product gives procedural
  information and legal context only.
- The legal data foundation was built before any AI character code, rejecting a quick thin demo
  first — weak retrieval would surface late, with characters built on ungrounded law.
- Three citation states instead of a binary found/fake, rejecting a rule that penalizes any
  citation not found in the corpus — users legitimately cite other laws or old pre-2024 numbers.
  Citations are verified, unverified (no penalty), or not-in-the-Act (the only penalizable state),
  with a target of zero real citations ever wrongly marked fake.
- Structural, verbatim chunking instead of fixed-size chunks — some sections run past 11,000
  characters and naive splitting breaks nested lists, so each unit is an exact slice of the law.
- Compact, local embedding models instead of a hosted embedding API — avoids new external cost and
  fits a small, memory-limited laptop, with some quality loss versus full precision left
  unmeasured.

## Engineering highlights

- Getting verbatim law out of a government PDF: extraction filters the watermark, footnotes, and
  page numbers without ever editing the legal text; anything the PDF draws as an image (like a
  formula) is flagged rather than silently fixed.
- Parsing Indian statute structure: handles provisos and explanations that interrupt clause
  lists, nested numbering that isn't a sub-section, headings that don't match the table of
  contents, and state amendments embedded in central sections. The build stops on anything it
  can't confidently place.
- Golden tests with independent review: 19 hard sections were checked against the rendered PDF by
  two independent reviewers; the second caught a real bug where a proviso was "swallowing" a
  clause list, since fixed.
- Bilingual retrieval: keyword-only search missed roughly twice as many Hinglish questions as
  English ones, mostly vocabulary gaps (e.g. "helmet" vs. the Act's "protective headgear"), which
  combining embedding search with keyword search mostly closes.
- A citation parser built to resist false accusations: linear-time, never crashes, never logs
  input text, handles English and Hinglish forms and ranges, and tells apart similarly named
  laws. Its rule: doubt always favors the user, never "fake."
- Built to run on a small laptop without a GPU, through a disciplined process with a spec per
  step and a running decision log.

## Safety & guardrails

- Educational only, not legal advice: explains how statutes and procedures work in the abstract;
  never tells a specific user what they personally should do.
- No legal document drafting: never generates ready-to-use documents like FIRs or petitions —
  only explains how they work.
- Law always shown verbatim: statute text is the exact retrieved text, never a paraphrase;
  provisional mapping data is never shown as statute text.
- Citation verification: cited sections are checked against the actual law before a character can
  accuse a user of citing fake law, favoring the user when in doubt.
- Sensitive input handling: raw user input is kept out of logs and test data; all test questions
  are synthetic.
- Planned (not built yet): a red-line test suite for advice-like language and document requests; a
  prompt-injection filter; schema-validated character outputs with a safe fallback; and dropping
  extra legal issues from memory if a user raises several at once.
- This agent describes the project; it does not give legal advice.

## Numbers

- Source Act: the Motor Vehicles Act, 1988 — 4,328,659 bytes, 176 extracted pages.
- Table of contents: 257 sections (7 omitted).
- 1,107 verbatim units: 250 sections, 649 sub-sections, 170 provisos, 32 explanations, 6 state
  amendments.
- 19 golden sections independently reviewed; 10 sections spot-checked word for word.
- Evaluation set: 100 questions (50 English, 50 Hinglish; 88 checkpoint, 12 magistrate stage),
  108 labels across 48 sections.
- Retrieval (recall@10 / MRR@10): keyword baseline 0.805 (English 0.870, Hinglish 0.740) / 0.649;
  dense-only 0.795 (0.860, 0.730) / 0.611; keyword over structural units 0.880 (0.950, 0.810) /
  0.647; hybrid dense+keyword 0.900 (0.950, 0.850), recall@5 0.85, / 0.731; larger-model hybrid
  prototype 0.925 (0.970, 0.880), recall@5 0.895, / 0.794.
- Citation checker: 0 of 4,943 real citations wrongly marked fake; 81 of 81 fake test citations
  caught.
- Provisional legal-code mapping table: 41 rows (24 IPC, 17 CrPC); independent review agreed with
  40 of 41 rows, refined 1.
- Tests: 1,082 offline tests plus 13 network tests passing; roughly 4,000 lines of application
  Python merged.

## Status

WORK IN PROGRESS. Of 20 planned steps, 4 are merged and 2 more are built and awaiting review. The
legal-data foundation is nearly complete: the Act is downloaded, verified, chunked, searchable in
English and Hinglish, and checked for citation accuracy. The AI characters, game engine, session
database, and chat interface are designed in detail but not built yet. The vector index step is
next, followed by the session database, scenario logic, the three-call AI pipeline, guardrail
testing, and the chat interface.

## Limitations

- No playable product yet: no AI model is integrated, and there is no user interface, game logic,
  or session database.
- Only one law is covered so far — the Motor Vehicles Act, 1988; citations to other laws come
  back "unverified" rather than confirmed.
- The best retrieval number reported above is from a prototype run, not yet reproduced in the
  committed benchmark, and remaining misses are mostly Hinglish.
- Compact, quantized embedding models may cost some retrieval quality versus full-precision
  models, and that cost is unmeasured so far.
- The provisional legal-code mapping table was written from model knowledge and reviewed by a
  second independent AI agent, but not yet checked against official government tables.
- Legal quality review so far is by AI review agents plus deterministic checks, not a named human
  legal reviewer.
- The citation checker verifies that a provision exists, not what the user claims it says, and
  doesn't guess which Act a bare number belongs to — loosely written real citations can come back
  "unverified" rather than "verified."
- A block of the Act's PDF pages had no extractable text layer, though all 257 official sections
  were still successfully processed.

## Code & demos

Code is available on request — contact Abhishek. There is no UI or demo yet; what's available to
show are evaluation numbers — retrieval quality results and citation-checker accuracy — rather
than a running product.

## Recruiter Q&A

**Q1. What is this project, in simple terms?**
A "Legal Flight Simulator": a text-based role-play where you practice a traffic-police stop on an
Indian highway against AI characters (officer, magistrate, witness), so you learn your rights and
the procedure before facing it for real. Educational only, not legal advice.

**Q2. Is it finished? Can I try it?**
Not yet — it's actively in progress. The legal-data foundation is built and tested: the Act is
downloaded, verified, split into 1,107 exact pieces, and searchable in English and Hinglish, with
a citation checker. The AI characters, game logic, and chat interface are designed but not built.
4 of 20 steps are merged, 2 more are in review; the vector index step is next.

**Q3. Why build the data pipeline before the "fun" AI part?**
Abhishek's own feasibility review found that the retrieval layer decides whether everything above
it works, and that the evaluation set should exist before any agent code — a quick demo first was
rejected because weak retrieval would surface late, with characters built on shaky legal
grounding.

**Q4. How do you stop the AI from giving legal advice?**
It's a firm rule: the system explains what the law says and how procedures work, never what a
specific user personally should do, and never drafts legal documents. Statute text is always
verbatim. An earlier "advice" output block was removed, since a disclaimer doesn't survive a
feature that gives advice. A dedicated zero-advice-language test suite is planned.

**Q5. How does it catch fake-law citations without punishing honest users?**
A deterministic, LLM-free checker classifies each citation as verified (found, with exact text),
unverified (can't be confirmed either way — e.g. another Act or an old pre-2024 number — no
penalty), or not-in-the-Act (the only penalizable state). Measured on 4,943 real citations: zero
wrongly flagged fake, and all 81 fake test citations caught.

**Q6. What makes the retrieval good, especially for Hinglish?**
Users write "helmet" or "phone"; the Act says "protective headgear" and "handheld communications
devices," so keyword search struggles (0.740 recall@10 on Hinglish alone). Combining multilingual
embedding search with keyword search lifts recall@10 to 0.900 overall (0.850 Hinglish) in
committed results, and to 0.925 in a not-yet-reproduced prototype.

**Q7. What's the tech stack?**
Python 3.12, FastAPI, Pydantic, pdfplumber, Qdrant with local quantized multilingual embeddings
plus keyword search, PostgreSQL (planned), Docker Compose, GitHub Actions, pytest, ruff, strict
mypy. Planned AI layer: Groq for routing, Anthropic Claude for role-play and judging. Planned
frontend: Streamlit.

**Q8. Why at most three AI calls per turn?**
Latency and cost. A five-call chain would mean 10-20 second turns — too slow for chat. Eight
character roles are kept as prompt personas but packed into three calls: route and flag,
in-character reply, and judge/score/build law cards.

**Q9. What was the hardest problem?**
Balancing legal correctness with user trust: Indian statutes have provisos, nested numbering, and
mismatched headings that had to be parsed correctly, and "not found" doesn't mean "fake," since
the Act itself cites an older section and users legitimately use pre-2024 numbers. Both were
solved with explicit rules and measurement. A small, GPU-less laptop also shaped the
embedding-model choice.

**Q10. How is user privacy handled?**
Because users might type self-incriminating things, raw input is treated as sensitive: logs
record only route, status, and duration, never request text, headers, IPs, or exception details.
Search and the citation checker never log or echo input, and all development test data is
synthetic.

**Q11. How was it built — did an AI write the code?**
Yes, and Abhishek is upfront about it: he designed the systems, made the decisions, and directed
AI coding agents (Claude Code / Codex) that wrote most of the code; he reviewed and tested it.
The process is rigorous — a spec and plan per step, a decision log, independent AI reviewers, and
over a thousand automated tests. Abhishek alone approves merges.
