import json
from datetime import date

import pytest

from nafas import qa, synthetic
from nafas.engine import fill_gaps
from nafas.llm import LLMError, LLMProvider, get_provider
from nafas.llm.gemini import GeminiProvider
from nafas.loop import run
from nafas.server import create_app


class Canned(LLMProvider):
    name, model = "canned", "test"

    def __init__(self, text=None, error=None):
        self.text, self.error, self.calls = text, error, []

    def generate(self, system, user, max_tokens=2000):
        self.calls.append((system, user))
        if self.error:
            raise LLMError(self.error)
        return self.text


@pytest.fixture(scope="module")
def r():
    p = synthetic.persona_layla()
    return run(p["profile"], fill_gaps(p["nights"]), p["checkins"], as_of=date(2026, 8, 11))


def test_emergency_and_clinical_questions_never_reach_the_model(r):
    for q, route in [("I have chest pain", "emergency"), ("Should I raise my pressure?", "care_team"),
                     ("هل أزيد الضغط؟", "care_team"), ("Can I take melatonin?", "care_team")]:
        llm = Canned("anything")
        out = qa.ask(r, q, llm, "en")
        assert out["route"] == route and out["source"] == "fixed" and not llm.calls


def test_grounded_answer_is_shown_and_gets_the_fact_pack(r):
    llm = Canned(f"You've banked {r.momentum['banked_nights']} good nights.")
    out = qa.ask(r, "How am I doing?", llm, "en")
    assert out["source"] == "llm:canned" and out["checks"] == "passed"
    system, user = llm.calls[0]
    facts = json.loads(user.split("FACTS:\n", 1)[1].split("\n\nQUESTION:", 1)[0])
    assert facts["progress"]["banked_nights"] == r.momentum["banked_nights"]
    assert len(facts["last_14_nights"]) == 14 and "pressure_95_cmh2o" in facts["last_14_nights"][-1]
    assert "Never suggest a pressure value" in system


@pytest.mark.parametrize("answer,reason", [
    ("Your adherence is 87.3%.", "ungrounded_numbers"),
    ("Increase your pressure tonight.", "pressure_advice"),
    ("You have central sleep apnoea.", "diagnosis"),
])
def test_unsafe_or_invented_answers_are_replaced(r, answer, reason):
    out = qa.ask(r, "How am I doing?", Canned(answer), "en")
    assert out["source"] == "template" and reason in out["fallback_reason"]
    assert str(r.momentum["banked_nights"]) in out["answer"]


def test_model_failure_and_ai_off_fall_back(r):
    assert qa.ask(r, "How am I doing?", Canned(error="timeout"), "en")["source"] == "template"
    r.profile.use_llm = False
    try:
        llm = Canned("x")
        assert qa.ask(r, "كيف حالي؟", llm, "en")["answer"].startswith("إليك") and not llm.calls
    finally:
        r.profile.use_llm = True


def test_rounding_is_not_treated_as_invention():
    facts = json.dumps({"avg": 7.56, "adh": 96.7})
    assert qa.ungrounded_numbers("About 7.6 h, roughly 8 h, 97% of nights.", facts, "") == []
    assert qa.ungrounded_numbers("About 6.2 h.", facts, "") == ["6.2"]


def test_gemini_provider_config_and_request_shape(monkeypatch):
    for k in ("NAFAS_GEMINI_VERTEX_PROJECT", "NAFAS_GEMINI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NAFAS_LLM", "gemini")
    assert get_provider().name == "offline"                       # not configured → template, says why

    monkeypatch.setenv("NAFAS_GEMINI_API_KEY", "test-key")
    g = GeminiProvider()
    assert g.available() and g.route == "ai-studio"
    seen = {}

    class Resp:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"candidates": [{"finishReason": "STOP",
                                               "content": {"parts": [{"text": "thinking", "thought": True},
                                                                     {"text": "Hello."}]}}]}).encode()

    def fake_urlopen(req, timeout=0):
        seen["url"], seen["headers"], seen["body"] = req.full_url, dict(req.header_items()), json.loads(req.data)
        return Resp()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    assert g.generate("sys", "hi") == "Hello."                    # thought parts are dropped
    assert "generativelanguage.googleapis.com" in seen["url"] and seen["body"]["systemInstruction"]
    assert seen["body"]["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "LOW"


def test_gemini_safety_block_becomes_llm_error(monkeypatch):
    monkeypatch.setenv("NAFAS_GEMINI_API_KEY", "k")
    monkeypatch.delenv("NAFAS_GEMINI_VERTEX_PROJECT", raising=False)

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"candidates": [{"finishReason": "SAFETY"}]}).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=0: Resp())
    with pytest.raises(LLMError):
        GeminiProvider().generate("s", "u")


def test_ask_endpoint(monkeypatch):
    monkeypatch.setenv("NAFAS_LLM", "offline")
    c = create_app().test_client()
    out = c.post("/api/ask", json={"persona": "omar", "question": "كيف كان أسبوعي؟"}).get_json()
    assert out["route"] == "answer" and out["source"] == "template" and out["lang"] == "ar"
    out = c.post("/api/ask", json={"persona": "ravi", "question": "Should I stop CPAP?"}).get_json()
    assert out["route"] == "care_team"


def test_reply_follows_the_language_of_the_question(r):
    assert qa.ask(r, "عندي ألم في الصدر", Canned("x"), "en")["lang"] == "ar"
    assert qa.ask(r, "Should I raise my pressure?", Canned("x"), "ar")["answer"].startswith("That's a decision")
