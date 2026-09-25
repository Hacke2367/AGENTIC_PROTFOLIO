"""FastAPI app: the page, opening a project chat, and one chat turn per POST (HTMX, no custom JS)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import agent, limits
from app.agent import BY_SLUG, MAX_HISTORY, MAX_TURN_CHARS, PROJECTS, ChatState

load_dotenv()
log = logging.getLogger("portfolio")

BASE = Path(__file__).resolve().parent
CONTACT_EMAIL = "abhishekmlen25@gmail.com"
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

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"projects": PROJECTS})


@app.get("/chat/open", response_class=HTMLResponse)
def open_chat(request: Request, project: str = ""):
    if project not in BY_SLUG:
        return HTMLResponse('<p class="msg notice">Unknown project.</p>', status_code=404)
    return templates.TemplateResponse(request, "chat_panel.html", {
        "project": BY_SLUG[project],
        "greeting": agent.greeting(project),
        "state_token": sign_state(ChatState(project)),
    })


def _turn(request: Request, reply: str, kind: str, user_text: str = "",
          state_token: str = "", switched_to: str = ""):
    # Always 200: HTMX does not swap 4xx/5xx responses by default.
    return templates.TemplateResponse(request, "message.html", {
        "user_text": user_text, "reply": reply, "kind": kind,
        "state_token": state_token, "switched_to": switched_to,
    })


@app.post("/chat", response_class=HTMLResponse)
def chat(request: Request, message: str = Form(""), state: str = Form("")):
    message = message.strip()
    if not message:
        return Response(status_code=204)
    if len(message) > MAX_MESSAGE_CHARS:
        return _turn(request, f"Please shorten your question to {MAX_MESSAGE_CHARS} characters.",
                     "notice", state_token=state)

    st = load_state(state)
    if st is None:
        return _turn(request, "This chat expired. Pick a project to start again.", "notice")

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
                 switched_to=BY_SLUG[reply.route.target].name if switched else "")
