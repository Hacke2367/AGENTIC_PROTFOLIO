"""Offline acceptance tests for the chat agent (spec 01). No network: OpenAI is faked."""
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import httpx2
import openai
import pytest
from fastapi.testclient import TestClient

from app import agent, limits, main

ROOT = Path(__file__).resolve().parent.parent
SENTINEL = "sk-test-SENTINEL"
TOKEN_RE = re.compile(r'id="chat-state" name="state" value="([^"]+)"')


class FakeResponses:
    def __init__(self):
        self.calls, self.exc, self.text = [], None, "Fake answer."

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.exc:
            raise self.exc
        usage = SimpleNamespace(input_tokens=1000, output_tokens=100,
                                input_tokens_details=SimpleNamespace(cached_tokens=0))
        return SimpleNamespace(output_text=self.text, usage=usage)


@pytest.fixture
def fake(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", SENTINEL)
    monkeypatch.setenv("STATE_SECRET", "test-secret")
    monkeypatch.delenv("KV_REST_API_URL", raising=False)
    monkeypatch.delenv("KV_REST_API_TOKEN", raising=False)
    limits.reset_memory()
    responses = FakeResponses()
    monkeypatch.setattr(agent, "get_client", lambda: SimpleNamespace(responses=responses))
    return responses


@pytest.fixture
def client(fake):
    return TestClient(main.app)


def open_token(client, slug):
    resp = client.get(f"/chat/open?project={slug}")
    assert resp.status_code == 200
    return TOKEN_RE.search(resp.text).group(1)


def say(client, token, message, ip="10.0.0.1"):
    return client.post("/chat", data={"message": message, "state": token},
                       headers={"x-forwarded-for": ip})


def token_of(resp):
    return TOKEN_RE.search(resp.text).group(1)


# --- AC1 --------------------------------------------------------------------------------

def test_greeting_names_project_and_sets_state(client):
    resp = client.get("/chat/open?project=dmc")
    assert resp.status_code == 200
    assert "Project DMC" in resp.text
    assert main.load_state(token_of(resp)).active == "dmc"


# --- AC3 / AC4 / AC5: routing -------------------------------------------------------------

def test_switch_notice_then_stays_on_new_project(client, fake):
    resp = say(client, open_token(client, "autoshorts"), "tell me about the lawyer project")
    assert "Switching to AI Lawyer: Legal Flight Simulator" in resp.text
    token = token_of(resp)
    assert main.load_state(token).active == "ai_lawyer"

    resp = say(client, token, "how does it work?")
    assert "Switching to" not in resp.text
    instructions = fake.calls[-1]["instructions"]
    assert "=== PROJECT KNOWLEDGE: AI Lawyer: Legal Flight Simulator ===" in instructions
    assert "\n# AutoShorts" not in instructions


def test_same_project_named_gives_no_switch_notice(client):
    resp = say(client, open_token(client, "dmc"), "how was DMC tested?")
    assert resp.status_code == 200
    assert "Switching to" not in resp.text


def test_vague_reference_asks_which_without_calling_openai(client, fake):
    resp = say(client, open_token(client, "dot_to_image"), "tell me about the video one")
    for name in ("AutoShorts", "Project DMC", "AI Cartoon"):
        assert name in resp.text
    assert main.load_state(token_of(resp)).active == "dot_to_image"
    assert fake.calls == []


def test_router_rules():
    assert agent.route("what about project 3?", "dmc").target == "dot_to_image"
    assert agent.route("how are the videos rendered?", "autoshorts").action == "stay"
    r = agent.route("compare DMC with the cartoon one", "dmc")
    assert (r.action, r.others) == ("stay", ("ai_cartoon",))
    r = agent.route("tell me about the cartoon and the lawyer projects", "dmc")
    assert (r.action, r.target, r.others) == ("switch", "ai_cartoon", ("ai_lawyer",))


# --- input and state guards ----------------------------------------------------------------

def test_empty_long_and_tampered_messages_never_call_openai(client, fake):
    token = open_token(client, "autoshorts")
    assert say(client, token, "   ").status_code == 204
    assert "shorten" in say(client, token, "x" * 501).text
    assert "expired" in say(client, token[:-1] + "0", "hello").text
    assert fake.calls == []


# --- AC13: the key never leaks ------------------------------------------------------------

def test_no_key_leak(client):
    token = open_token(client, "autoshorts")
    bodies = [client.get("/").text, client.get("/chat/open?project=autoshorts").text,
              say(client, token, "what does it do?").text]
    assert all(SENTINEL not in b for b in bodies)
    tracked = subprocess.run(["git", "grep", "-nE", "sk-[A-Za-z0-9_-]{20,}"],
                             cwd=ROOT, capture_output=True, text=True)
    assert tracked.stdout == ""


# --- AC14 / AC15: caps ------------------------------------------------------------------

def test_visitor_cap_blocks_21st_message(client, fake):
    token = open_token(client, "autoshorts")
    for _ in range(20):
        assert "chat limit" not in say(client, token, "what does it do?").text
    assert "chat limit" in say(client, token, "what does it do?").text
    assert len(fake.calls) == 20


def test_daily_cap_blocks_all_chats(client, fake):
    day = f"spend:{datetime.now(timezone.utc):%Y-%m-%d}"
    limits._memory[day] = (1_000_000, 0.0)
    resp = say(client, open_token(client, "dmc"), "what does it do?")
    assert "resting" in resp.text
    assert fake.calls == []


def test_store_failure_fails_closed(client, fake, monkeypatch):
    def broken(*_):
        raise limits.LimitStoreError("down")
    monkeypatch.setattr(limits, "_kv", broken)
    assert "resting" in say(client, open_token(client, "dmc"), "hi").text
    assert fake.calls == []


# --- AC16: OpenAI failure --------------------------------------------------------------

def test_openai_failure_shows_error_and_keeps_state(client, fake):
    token = open_token(client, "autoshorts")
    fake.exc = openai.APIConnectionError(request=httpx2.Request("POST", "https://api.openai.com"))
    resp = say(client, token, "what does it do?")
    assert "answer right now" in resp.text
    assert token_of(resp) == token
    fake.exc = None
    assert "Fake answer." in say(client, token, "what does it do?").text


# --- AC17: no custom JavaScript ---------------------------------------------------------

def test_no_custom_js(client):
    token = open_token(client, "autoshorts")
    sources = [p.read_text(encoding="utf-8") for p in (ROOT / "app" / "templates").glob("*.html")]
    rendered = [client.get("/").text, client.get("/chat/open?project=dmc").text,
                say(client, token, "hi").text]
    everything = "\n".join(sources + rendered)
    assert client.get("/").text.count("<script") == 1
    assert "cdn.jsdelivr.net/npm/htmx.org" in client.get("/").text
    assert sum(s.count("<script") for s in sources) == 1
    assert "hx-on" not in everything
    assert not re.search(r"\son[a-z]+\s*=", everything)
    assert not re.search(r'hx-trigger="[^"]*\[', everything)


# --- knowledge hygiene (plan §9) --------------------------------------------------------

FORBIDDEN = [r"\b401\b", r"leak", r"open question", r"credit", r"C:\\", r"sandeep",
             r"demo_output_result"]


def test_knowledge_files_exist_and_are_clean():
    for p in agent.PROJECTS:
        assert (ROOT / "knowledge" / p.knowledge_file).exists(), p.knowledge_file
    for path in (ROOT / "knowledge").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        for pat in FORBIDDEN:
            assert not re.search(pat, text, re.I), f"{path.name}: {pat}"
        emails = set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text)) - {main.CONTACT_EMAIL}
        assert not emails, f"{path.name}: {emails}"
        assert len(text.split()) <= 3000, f"{path.name} is too long"
