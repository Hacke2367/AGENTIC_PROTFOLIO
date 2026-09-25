"""Shared offline test scaffolding: a fake OpenAI client, a TestClient, and chat helpers.

Test modules import the helpers with `from conftest import ...`.
"""
import re
from pathlib import Path
from types import SimpleNamespace

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


def say(client, token, message, ip="10.0.0.1", **fields):
    return client.post("/chat", data={"message": message, "state": token, **fields},
                       headers={"x-forwarded-for": ip})


def token_of(resp):
    return TOKEN_RE.search(resp.text).group(1)
