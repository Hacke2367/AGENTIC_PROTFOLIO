"""Offline acceptance tests for the front page (spec 02, plan 02 §10). No network: OpenAI is faked."""
import json
import re

import pytest
from markupsafe import escape

from app import agent, content, limits, main
from conftest import ROOT, open_token, say, token_of

STYLES = (ROOT / "app" / "static" / "styles.css").read_text(encoding="utf-8")
RESUME = ROOT / "app" / "static" / "resume.pdf"
KNOWLEDGE = {p.slug: (ROOT / "knowledge" / p.knowledge_file).read_text(encoding="utf-8")
             for p in agent.PROJECTS}

# Plan §8 fact table: (text on the card, evidence verbatim in that project's knowledge file).
FACTS = {
    "autoshorts": [("$0.036", "30 AI calls, ~$0.036 total"), ("7", "7 production templates"),
                   ("0.00 s", "(0.00s delta)"), ("up to 6 s", "0.76–6.08s")],
    "dmc": [("r = 0.97", "r = 0.97"), ("846", "846 scripts checked against 9 viewer guarantees"),
            ("82%", "230 (82%) passed"), ("80 glowing dots", "simulates 80 glowing dots")],
    "dot_to_image": [("2,763", "2,763 dots on one A2 poster"), ("$5.38", "~$5.38"), ("~573", "573"),
                     ("1,180", "1,180 test functions"), ("1,000 to 3,000", "1,000 to 3,000"),
                     ("30 automated checks", "30 validation checks")],
    "ai_cartoon": [("₹30–50", "₹30–50 per video"), ("₹1,500+", "₹1,500+ via paid APIs"),
                   ("1.74", "1.74 GPU-hours"), ("12-shot", "12 shots, all AI motion"),
                   ("463", "463 tests passing")],
    "ai_lawyer": [("0.90", "hybrid dense+keyword 0.900"), ("0.805", "keyword baseline 0.805"),
                  ("81 / 81", "81 of 81 fake test citations"), ("1,107", "1,107 verbatim units"),
                  ("4 of 20", "4 are merged")],
}
FLAG_EVIDENCE = [("autoshorts", "~$0.036"), ("dmc", "r = 0.97"), ("dot_to_image", "1,180 test functions"),
                 ("ai_lawyer", "1,082 offline tests")]


def esc(text):
    return str(escape(text))


def answer_texts(slug, cmd):
    answer = content.COMMANDS[slug][cmd]
    return answer.built if isinstance(answer, content.Pipeline) else (answer,)


def rl_keys():
    return [k for k in limits._memory if k.startswith("rl:")]


# --- content integrity ----------------------------------------------------------------------

def test_content_covers_every_project():
    slugs = set(agent.BY_SLUG)
    assert set(content.CARDS) == slugs and set(content.COMMANDS) == slugs
    for slug in slugs:
        assert len(content.CARDS[slug].stats) == 3
        assert set(content.COMMANDS[slug]) == set(content.COMMAND_NAMES)


# --- AC1 / AC2: page structure and hero ------------------------------------------------------

def test_page_sections_in_order(client):
    body = client.get("/").text
    marks = ['id="projects"', 'id="why-hire-me"', 'id="about"', 'id="contact"', 'id="feedback"',
             'class="foot"']
    positions = [body.index(m) for m in marks]
    assert positions == sorted(positions)
    assert body.index('class="bar"') < body.index('class="hero"') < positions[0]
    for label, href in content.NAV:
        assert f'href="{href}"' in body and f">{label}</a>" in body
    assert 'href="/static/resume.pdf" class="primary" download' in body
    assert RESUME.exists()


def test_hero_flags_and_ctas(client):
    body = client.get("/").text
    assert body.count('<details class="flag" name="flags">') == len(content.FLAGS) == 6
    for flag, proof in content.FLAGS:
        assert f"<summary>{esc(flag)}</summary><p>{esc(proof)}</p>" in body
    assert "See the projects" in body and "Download resume (PDF)" in body
    for slug, evidence in FLAG_EVIDENCE:
        assert evidence in KNOWLEDGE[slug]


# --- AC3: project rows and facts ---------------------------------------------------------------

def test_project_rows(client):
    body = client.get("/").text
    rows = re.findall(r'<article class="project" data-p="([a-z_]+)">(.*?)</article>', body, re.S)
    assert [slug for slug, _ in rows] == [p.slug for p in agent.PROJECTS]
    for slug, row in rows:
        assert row.count("<dt>") == 3
        assert "Talk to this project" in row
        assert row.count(f"/chat/open?project={slug}&amp;cmd=") == 4
        assert esc(content.CARDS[slug].pitch) in row


def test_card_facts_match_knowledge():
    for slug, facts in FACTS.items():
        card = content.CARDS[slug]
        blob = " | ".join([card.pitch, card.status, *(f"{v} {label}" for v, label in card.stats)])
        for value, evidence in facts:
            assert value in blob, (slug, value)
            assert evidence in KNOWLEDGE[slug], (slug, evidence)
        # Every stat value on the card is in the fact table: no untraced numbers.
        assert {v for v, _ in card.stats} <= {v for v, _ in facts}, slug


# --- AC4 / AC8 / AC9: agent map ---------------------------------------------------------------

def test_talk_opens_active_project(client):
    resp = client.get("/chat/open?project=dmc")
    assert 'id="chat-title" data-active="dmc"' in resp.text
    assert "data-initial" not in resp.text
    assert '<input type="checkbox" id="sheet" hidden checked hx-swap-oob="true">' in resp.text
    body = client.get("/").text
    assert 'id="chat-title" data-active="autoshorts" data-initial' in body
    assert 'id="sheet" hidden checked' not in body


def test_switch_moves_map(client):
    resp = say(client, open_token(client, "autoshorts"), "tell me about the lawyer project")
    assert '<h3 id="chat-title" data-active="ai_lawyer" hx-swap-oob="true">' in resp.text


def test_map_rules_for_every_project(client):
    body = client.get("/").text
    for p in agent.PROJECTS:
        s = p.slug
        assert f'.console:has(#chat-title[data-active="{s}"]) .node[data-p="{s}"] .dot' in body
        assert f'#chat-title[data-active="{s}"]:not([data-initial])' in body
        assert f'.page:has(.project[data-p="{s}"]:hover) .edge[data-p="{s}"]' in body
        assert f'class="node" data-p="{s}"' in body and f'class="edge" data-p="{s}"' in body


# --- AC5 / AC6 / AC7: slash commands -----------------------------------------------------------

@pytest.mark.parametrize("cmd", content.COMMAND_NAMES)
@pytest.mark.parametrize("slug", [p.slug for p in agent.PROJECTS])
def test_row_commands_answer_statically(client, fake, slug, cmd):
    resp = client.get(f"/chat/open?project={slug}&cmd={cmd}")
    assert resp.status_code == 200
    assert f'<div class="msg user cmd">/{cmd}</div>' in resp.text
    for text in answer_texts(slug, cmd):
        assert esc(text) in resp.text
    assert fake.calls == [] and rl_keys() == []
    assert main.load_state(token_of(resp)).history[0]["content"] == f"/{cmd}"


def test_typed_commands(client, fake):
    token = open_token(client, "dmc")
    for typed, cmd in [("/usp", "usp"), ("  /USP ", "usp"), ("/pipeline", "pipeline"),
                       ("/hardest-problem", "hardest-problem"), ("/philosophy", "philosophy")]:
        resp = say(client, token, typed)
        assert esc(answer_texts("dmc", cmd)[0]) in resp.text
        token = token_of(resp)
    for typed in ("/help", "/nope"):
        resp = say(client, token, typed)
        assert esc(content.HELP) in resp.text
        token = token_of(resp)
    assert fake.calls == [] and rl_keys() == []
    history = main.load_state(token).history
    assert len(history) == agent.MAX_HISTORY and history[-1]["content"] == content.HELP
    # A console button leaves a half-typed question alone; a typed command resets the input.
    assert 'id="chat-input"' not in say(client, token, "/usp", via="button").text
    assert 'id="chat-input"' in say(client, token, "/usp").text


def test_commands_work_when_the_chat_is_capped(client, fake, monkeypatch):
    monkeypatch.setenv("DAILY_BUDGET_USD", "0")
    token = open_token(client, "ai_cartoon")
    assert "resting" in say(client, token, "what does it do?").text
    assert esc(answer_texts("ai_cartoon", "usp")[0]) in say(client, token, "/usp").text
    assert fake.calls == []


def test_pipeline_flow_marks_planned_steps(client):
    lawyer = content.COMMANDS["ai_lawyer"]["pipeline"]
    resp = client.get("/chat/open?project=ai_lawyer&cmd=pipeline")
    flow = re.search(r'<ol class="flow">(.*?)</ol>', resp.text).group(1)
    assert flow.count("<li") == len(lawyer.built) + len(lawyer.planned) == 7
    assert flow.count('<li class="planned">') == len(lawyer.planned) == 2
    assert "Dashed steps are planned, not built yet." in resp.text
    resp = client.get("/chat/open?project=autoshorts&cmd=pipeline")
    assert 'class="planned"' not in resp.text and "Dashed steps" not in resp.text


# --- AC10: motion -------------------------------------------------------------------------------

def test_motion_is_one_load_moment_and_respects_reduced_motion():
    css = re.sub(r"/\*.*?\*/", "", STYLES, flags=re.S)
    assert set(re.findall(r"@keyframes\s+([\w-]+)", css)) == {"draw", "fade", "ping"}
    before, reduced = css.split("@media (prefers-reduced-motion: reduce)")
    assert before.count("animation:") == 2  # .edge draws, .node fades in; the ping is per-switch
    for rule in (".edge { animation: none", ".node { animation: none",
                 ".node .dot { animation: none !important"):
        assert rule in reduced
    assert "@media (prefers-reduced-motion: no-preference) { html { scroll-behavior: smooth; } }" in css


# --- AC12: feedback ---------------------------------------------------------------------------

def post_feedback(client, ip="10.0.0.9", **fields):
    data = {"message": "Loved the agent console.", "name": "", "company": "", "website": "", **fields}
    return client.post("/feedback", data=data, headers={"x-forwarded-for": ip})


def stored():
    return limits._memory.get("feedback", (None, 0.0))[0] or []


def test_feedback_saved_privately(client, fake):
    resp = post_feedback(client, name="Priya", company="Acme")
    assert "reached Abhishek" in resp.text and "hx-retarget" not in resp.headers
    [record] = [json.loads(r) for r in stored()]
    assert (record["message"], record["name"], record["company"]) == ("Loved the agent console.", "Priya", "Acme")
    assert set(record) == {"at", "name", "company", "message"}  # no IP, no visitor hash
    assert fake.calls == []


def test_feedback_invalid_input_keeps_the_form(client):
    for fields, text in [({"message": "  "}, "write a message"), ({"message": "x" * 501}, "under 500"),
                         ({"name": "n" * 81}, "under 80")]:
        resp = post_feedback(client, **fields)
        assert text in resp.text
        assert (resp.headers["hx-retarget"], resp.headers["hx-reswap"]) == ("#fb-status", "innerHTML")
    assert stored() == []


def test_feedback_honeypot_stores_nothing(client):
    assert "reached Abhishek" in post_feedback(client, website="http://spam.example").text
    assert stored() == []


def test_feedback_daily_limit_per_visitor(client):
    for _ in range(3):
        assert "reached Abhishek" in post_feedback(client).text
    assert "already sent" in post_feedback(client).text
    assert len(stored()) == 3
    assert "reached Abhishek" in post_feedback(client, ip="10.0.0.10").text


def test_feedback_store_failure_keeps_the_form(client, monkeypatch):
    def broken(*_):
        raise limits.LimitStoreError("down")
    monkeypatch.setattr(limits, "_kv", broken)
    resp = post_feedback(client)
    assert content.EMAIL in resp.text and resp.headers["hx-retarget"] == "#fb-status"


# --- AC13 / AC14 / AC15 / AC16 / perf ----------------------------------------------------------

def test_contact_privacy_and_resume_size(client):
    body = client.get("/").text
    assert content.EMAIL in body
    sources = [p.read_text(encoding="utf-8") for p in (ROOT / "app" / "templates").glob("*.html")]
    for text in [body, *sources, (ROOT / "app" / "content.py").read_text(encoding="utf-8")]:
        assert "9930692220" not in text and "+91" not in text
    assert RESUME.stat().st_size <= 1_048_576


def test_no_custom_js_in_front_page_fragments(client):
    token = open_token(client, "dmc")
    rendered = [client.get("/chat/open?project=ai_lawyer&cmd=pipeline").text,
                say(client, token, "/usp", via="button").text,
                client.post("/feedback", data={"message": "hi"}).text]
    for text in rendered:
        assert "<script" not in text and "hx-on" not in text
        assert not re.search(r"\son[a-z]+\s*=", text)
    templates = "\n".join(p.read_text(encoding="utf-8") for p in (ROOT / "app" / "templates").glob("*.html"))
    assert "js:" not in templates


def _luminance(hex_color):
    def channel(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(int(hex_color[i:i + 2], 16) / 255) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_contrast_meets_wcag_aa():
    root = STYLES.split(":root {", 1)[1].split("}", 1)[0]
    tokens = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})", root))
    pairs = [("ink", "bg"), ("ink", "surface"), ("ink", "reply-bg"), ("ink", "user-bg"),
             ("muted", "bg"), ("muted", "surface"), ("muted", "reply-bg"),
             ("faint", "bg"), ("faint", "surface"), ("faint", "reply-bg"),
             ("good", "bg"), ("good", "surface"), ("wip", "bg"), ("wip", "surface"),
             ("accent-ink", "surface"), ("accent-ink", "reply-bg")]
    for fg, bg in pairs:
        assert _contrast(tokens[fg], tokens[bg]) >= 4.5, (fg, bg)
    assert _contrast("#FFFFFF", tokens["accent"]) >= 4.5
    assert _contrast("#FFFFFF", tokens["ink"]) >= 4.5


def test_prototype_gone(client):
    assert not (ROOT / "app" / "prototype_front_page.py").exists()
    assert not (ROOT / "app" / "templates" / "prototype_front_page").exists()
    assert client.get("/prototype/cmd?project=dmc").status_code == 404
    assert "proto-switcher" not in client.get("/?variant=d").text


def test_page_weight(client):
    assert len(client.get("/").content) + len(STYLES.encode()) < 100_000
