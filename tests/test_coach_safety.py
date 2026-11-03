from conftest import make_nights
from nafas import coach, loop
from nafas.llm import LLMError, LLMProvider, OfflineProvider, get_provider
from nafas.safety import check_output, crisis_check


class FakeLLM(LLMProvider):
    name, model = "fake", "fake-1"

    def __init__(self, text=None, error=None):
        self.text, self.error, self.calls = text, error, []

    def generate(self, system, user, max_tokens=2000):
        self.calls.append((system, user))
        if self.error:
            raise LLMError(self.error)
        return self.text


def _result(profile, **kw):
    nights = make_nights([420] * 15 + [0, 0])
    return loop.run(profile, nights, **kw)


def test_safety_rules_catch_the_things_we_never_say():
    assert "pressure_change" in check_output("Try to increase your pressure a little tonight.")
    assert "pressure_change" in check_output("Set it to 12 cmH2O.")
    assert "diagnosis" in check_output("You have central sleep apnoea.")
    assert "medication" in check_output("Melatonin might help.")
    assert "blame" in check_output("You failed again last night.")
    assert "stop_therapy" in check_output("Maybe stop using CPAP for a week.")
    assert check_output("You've banked 40 good nights. Tonight, wear it for an hour.") == []


def test_crisis_notes_get_an_emergency_message():
    assert "998" in crisis_check("woke up with chest pain")
    assert crisis_check("لا أستطيع التنفس", "ar").startswith("ما كتبته")
    assert crisis_check("mask was itchy") is None


def test_coach_uses_llm_text_when_it_passes_checks(profile):
    llm = FakeLLM("Hi Test. You've banked 15 good nights. Tonight, just one hour counts.")
    out = coach.compose(_result(profile), llm)
    assert out["source"] == "llm:fake" and out["text"].startswith("Hi Test")
    system, brief = llm.calls[0]
    assert "Never mention pressure" in system and '"banked_good_nights": 15' in brief


def test_coach_falls_back_when_llm_breaks_a_rule(profile):
    out = coach.compose(_result(profile), FakeLLM("You failed. Increase the pressure."))
    assert out["source"] == "template" and "safety checks" in out["fallback_reason"]
    assert check_output(out["text"]) == []


def test_coach_falls_back_when_llm_is_down_or_off(profile):
    assert coach.compose(_result(profile), FakeLLM(error="timeout"))["source"] == "template"
    assert coach.compose(_result(profile), OfflineProvider())["source"] == "template"
    profile.use_llm = False
    llm = FakeLLM("anything")
    assert coach.compose(_result(profile), llm)["source"] == "template" and not llm.calls


def test_arabic_template(profile):
    profile.language = "ar"
    out = coach.compose(_result(profile), OfflineProvider())
    assert out["text"].startswith("مرحباً") and out["lang"] == "ar"


def test_provider_selection_falls_back_to_offline(monkeypatch):
    monkeypatch.setenv("NAFAS_LLM", "azure")
    for k in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_DEPLOYMENT"):
        monkeypatch.delenv(k, raising=False)
    p = get_provider()
    assert p.name == "offline" and "azure" in p.describe()["note"]
    monkeypatch.setenv("NAFAS_LLM", "offline")
    assert get_provider().name == "offline"
