# Project Context: Agent Portfolio

## Problem
A recruiter skims a static resume in seconds and cannot ask follow-up questions about the
projects on it. The owner builds AI and agent systems, and a PDF cannot prove that. The owner
needs the resume online, plus a way for a recruiter to question any project in depth whenever
they want to.

## Objective
A first version, live on a public URL today (2026-09-25), within 6 hours:
- A single-page portfolio in a light theme, with one smooth load animation and a subtle
  AI/creative feel.
- The full resume on the front page: philosophy/about, skills, 5 projects, and contact.
- Each project is shown well enough to impress on its own, and each one has a
  "talk to this project" chat agent that holds that project's A-to-Z context.
- The agent answers only about the active project. If the user asks about a different project,
  the agent says so openly ("switching to Project X") and from then on talks only about that
  project.

## Who it's for
Recruiters, both non-technical HR and technical hiring managers. The agent gives a
plain-language answer first and goes into technical depth (architecture, tradeoffs) when asked.
The owner targets three roles: AI/ML engineer, GenAI/agent engineer, and full-stack + AI.

## Scope
**In scope:**
- Resume sections: philosophy/about, skills, projects, contact.
- 5 projects: MANIM code video template, Project DMC, DOT_TO_IMAGE, AI Cartoon 0 Cost,
  AI LLM Lawyer (in progress).
- A per-project chat agent that switches context between projects visibly.
- A layout that works on mobile.

**Out of scope:**
- The previous Streamlit portfolio (`C:\Protfolio`): ignored completely, both UI and content.
- Blog, CMS/admin panel, login/accounts, chat history persistence, voice, analytics.
- The agent as a general-purpose chatbot. It talks about the owner's projects only.

## Constraints
- Time: must be live within 6 hours of the kickoff on 2026-09-25.
- Money: free or near-free hosting. LLM cost stays low, and because the page is public, usage
  must be capped.
- LLM provider: OpenAI (owner decision, 2026-09-25).
- Content sources: the resume is in `docs/resume.md`, and project knowledge is in
  `docs/projects/`.
- Machine: a small Windows machine where heavy local runs can run out of memory.

## What already exists that's close
- `C:\Protfolio`: an old Streamlit portfolio. The owner decided to ignore it entirely.
- Project knowledge is being compiled from the 5 project repos into `docs/projects/0N_*.md`.
  That knowledge is the agent's A-to-Z context.

## Success signal
- The site is live on a public URL today.
- For each project, a recruiter can ask 5 test questions and get accurate answers grounded in
  that project's knowledge, with zero invented facts.
- Asking about another project triggers a visible switch, and later answers stay on the new
  project.

## Red lines
- The agent never invents facts. If something is not in the project knowledge, it says so and
  points to the contact section.
- API keys and secrets are never exposed, neither in the page source nor in answers.
- The agent never makes commitments on the owner's behalf: salary, availability, notice
  period, or offers.
- The AI LLM Lawyer agent never gives legal advice. It only describes the project.
- A public chat must not be able to run up an unbounded LLM bill.
- The agent cannot be steered (for example by prompt injection) into topics outside the
  projects.
