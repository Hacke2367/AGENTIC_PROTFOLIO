"""FastAPI app: the front page, opening a project chat, one chat turn per POST, and private
feedback (HTMX, no custom JS)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import agent, content, feedback, limits
from app.agent import BY_SLUG, MAX_HISTORY, MAX_TURN_CHARS, PROJECTS, ChatState

load_dotenv()
log = logging.getLogger("portfolio")

BASE = Path(__file__).resolve().parent
CONTACT_EMAIL = content.EMAIL
MAX_MESSAGE_CHARS = 500
CSP = "script-src 'self' https://cdn.jsdelivr.net"


def _state_secret() -> bytes:
    secret = os.getenv("STATE_SECRET")
    if secret:
        return secret.encode()
    if os.getenv("VERCEL"):
        raise RuntimeError("STATE_SECRET must be set in production")
    log.warning("STATE_SECRET not set; using an insecure dev default")
    return b"dev-only-insecure-state-secret"


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


@app.middleware("http")
async def csp_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = CSP
    return response


# --- signed conversation state (plan D3) ------------------------------------------------

def sign_state(state: ChatState) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"a": state.active, "h": state.history}, separators=(",", ":")).encode()
    ).decode()
    sig = hmac.new(_state_secret(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def load_state(token: str) -> ChatState | None:
    payload, _, sig = token.rpartition(".")
    expected = hmac.new(_state_secret(), payload.encode(), hashlib.sha256).hexdigest()
    if not payload or not hmac.compare_digest(sig, expected):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload))
    except ValueError:
        return None
    history = data.get("h")
    if data.get("a") not in BY_SLUG or not isinstance(history, list) or not all(
        isinstance(t, dict) and t.get("role") in ("user", "assistant")
        and isinstance(t.get("content"), str) for t in history
    ):
        return None
    return ChatState(data["a"], history)


# --- routes -----------------------------------------------------------------------------

def panel_context(slug: str, cmd: str = "", *, initial: bool = False,
                  open_sheet: bool = True) -> dict:
    """chat_panel.html context. A command opens the panel with its answer already in the
    history (plan 02 D3); open_sheet slides the mobile sheet up via an OOB checkbox (D8)."""
    history = []
    if cmd:
        history = [{"role": "user", "content": f"/{cmd}"},
                   {"role": "assistant", "content": content.command_text(slug, cmd)[:MAX_TURN_CHARS]}]
    return {
        "project": BY_SLUG[slug], "greeting": agent.greeting(slug),
        "state_token": sign_state(ChatState(slug, history)),
        "cmd": cmd, "cmd_label": f"/{cmd}", "answers": content.COMMANDS[slug],
        "help": content.HELP, "command_names": content.COMMAND_NAMES,
        "initial": initial, "open_sheet": open_sheet,
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    # The first console panel is rendered here, not fetched on load (plan 02 D7).
    return templates.TemplateResponse(request, "index.html", {
        "person": content.PERSON, "nav": content.NAV, "flags": content.FLAGS,
        "why": content.WHY_HIRE, "skills": content.SKILLS, "exp": content.EXPERIENCE,
        "edu": content.EDUCATION, "certs": content.CERTS, "projects": PROJECTS,
        "cards": content.CARDS, "email": CONTACT_EMAIL,
        **panel_context(PROJECTS[0].slug, initial=True, open_sheet=False),
    })


@app.get("/chat/open", response_class=HTMLResponse)
def open_chat(request: Request, project: str = "", cmd: str = ""):
    if project not in BY_SLUG:
        return HTMLResponse('<p class="msg notice">Unknown project.</p>', status_code=404)
    cmd = cmd if cmd in content.COMMAND_NAMES else ""
    return templates.TemplateResponse(request, "chat_panel.html", panel_context(project, cmd))


def _turn(request: Request, reply: str, kind: str, user_text: str = "",
          state_token: str = "", switched_to: str = "", switched_slug: str = ""):
    # Always 200: HTMX does not swap 4xx/5xx responses by default.
    return templates.TemplateResponse(request, "message.html", {
        "user_text": user_text, "reply": reply, "kind": kind, "state_token": state_token,
        "switched_to": switched_to, "switched_slug": switched_slug,
    })


def _command_turn(request: Request, st: ChatState, message: str, cmd: str, via: str):
    """A slash command: a static answer, no caps and no OpenAI call (plan 02 D2, D3)."""
    text = content.command_text(st.active, cmd)
    history = (st.history + [{"role": "user", "content": message[:MAX_TURN_CHARS]},
                             {"role": "assistant", "content": text[:MAX_TURN_CHARS]}])[-MAX_HISTORY:]
    return templates.TemplateResponse(request, "message.html", {
        "cmd": cmd, "cmd_label": message, "answers": content.COMMANDS[st.active],
        "help": content.HELP, "state_token": sign_state(ChatState(st.active, history)),
        "keep_input": via == "button",  # a console button leaves a half-typed question alone
    })


@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, message: str = Form(""), state: str = Form(""), via: str = Form("")):
    message = message.strip()
    if not message:
        return Response(status_code=204)
    if len(message) > MAX_MESSAGE_CHARS:
        return _turn(request, f"Please shorten your question to {MAX_MESSAGE_CHARS} characters.",
                     "notice", state_token=state)

    st = load_state(state)
    if st is None:
        return _turn(request, "This chat expired. Pick a project to start again.", "notice")

    cmd = content.parse_command(message)
    if cmd:
        return _command_turn(request, st, message, cmd, via)

    try:
        decision = limits.check(limits.visitor_id(request))
    except limits.LimitStoreError:
        log.exception("limit store failed; failing closed")
        decision = limits.LimitDecision(False, "daily")
    if not decision.allowed:
        text = ("You've hit the chat limit for now." if decision.reason == "visitor"
                else "The chat is resting for today.")
        return _turn(request, f"{text} You can reach Abhishek at {CONTACT_EMAIL}.", "notice",
                     user_text=message, state_token=state)

    try:
        reply = agent.answer(st, message)
    except agent.AgentUnavailable:
        log.exception("agent unavailable")
        return _turn(request, "I couldn't answer right now. Please try again.", "error",
                     user_text=message, state_token=state)

    if reply.cost_usd > 0:
        try:
            limits.record_spend(reply.cost_usd)
        except limits.LimitStoreError:
            log.exception("could not record spend")  # the answer is already paid for

    switched = reply.route.action == "switch"
    history = [] if switched else st.history
    history = (history + [{"role": "user", "content": message[:MAX_TURN_CHARS]},
                          {"role": "assistant", "content": reply.text[:MAX_TURN_CHARS]}])[-MAX_HISTORY:]
    new_state = ChatState(reply.route.target, history)
    return _turn(request, reply.text, "reply", user_text=message,
                 state_token=sign_state(new_state),
                 switched_to=BY_SLUG[reply.route.target].name if switched else "",
                 switched_slug=reply.route.target if switched else "")


# --- feedback (plan 02 D9, D10) -----------------------------------------------------------

def _feedback_reply(text: str, *, keep_form: bool = False) -> HTMLResponse:
    """Success replaces the form; errors go to #fb-status so the typed text survives."""
    headers = {"HX-Retarget": "#fb-status", "HX-Reswap": "innerHTML"} if keep_form else None
    return HTMLResponse(f'<p class="fb-done" role="status">{html.escape(text)}</p>', headers=headers)


@app.post("/feedback", response_class=HTMLResponse)
def feedback_submit(request: Request, message: str = Form(""), name: str = Form(""),
                    company: str = Form(""), website: str = Form("")):
    message, name, company = message.strip(), name.strip(), company.strip()
    thanks = "Thanks, your feedback reached Abhishek."
    if website.strip():  # hidden bot trap: look successful, store nothing
        log.info("feedback honeypot hit")
        return _feedback_reply(thanks)
    if not message:
        return _feedback_reply("Please write a message first.", keep_form=True)
    if len(message) > feedback.MAX_MESSAGE:
        return _feedback_reply("Please keep it under 500 characters.", keep_form=True)
    if len(name) > feedback.MAX_FIELD or len(company) > feedback.MAX_FIELD:
        return _feedback_reply("Please keep name and company under 80 characters.", keep_form=True)
    try:
        result = feedback.save(limits.visitor_id(request), message, name, company)
    except limits.LimitStoreError:
        log.exception("feedback store failed")
        return _feedback_reply("Couldn't save your feedback right now. "
                               f"You can email {CONTACT_EMAIL}.", keep_form=True)
    if result == "limited":
        return _feedback_reply("Thanks, you've already sent feedback today.")
    return _feedback_reply(thanks)
