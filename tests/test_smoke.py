import importlib
import sys


def load_app():
    sys.path.insert(0, ".")
    module = importlib.import_module("jarvis")
    return module


def test_hud_serves_command_center():
    module = load_app()
    client = module.app.test_client()
    response = client.get("/", base_url="http://127.0.0.1:8765")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "VENOM // COMMAND CENTER" in body
    assert "__TOKEN__" not in body


def test_status_endpoint_returns_expected_shape():
    module = load_app()
    client = module.app.test_client()
    response = client.get(
        "/api/status",
        base_url="http://127.0.0.1:8765",
        headers={"X-Venom-Token": module.TOKEN},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "stats" in data
    assert "ai_providers" in data
    assert "phone_alerts" in data


def test_empty_command_is_safe():
    module = load_app()
    client = module.app.test_client()
    response = client.post(
        "/api/command",
        base_url="http://127.0.0.1:8765",
        headers={"X-Venom-Token": module.TOKEN},
        json={"text": ""},
    )
    assert response.status_code == 200
    assert response.get_json()["replies"] == []



def test_reply_capture_does_not_share_global_buffer():
    module = load_app()
    captured = module._capture_replies(lambda: module._speak("isolated reply"))
    assert captured == [{"say": "isolated reply", "show": "isolated reply"}]


def test_status_tolerates_corrupt_local_records(monkeypatch):
    module = load_app()
    original_load_json = module.V.load_json

    def fake_load_json(path, default):
        if path == module.V.CLIENT_FILE:
            return [{"payments": [None, {}], "price": "not-a-number", "paid": None}]
        if str(path).endswith("leads.json"):
            return [None, "bad-record"]
        if str(path).endswith("queue.json"):
            return [None]
        if str(path).endswith("briefs.json"):
            return [None]
        return original_load_json(path, default)

    monkeypatch.setattr(module.V, "load_json", fake_load_json)
    monkeypatch.setattr(module.V, "load_meetings", lambda: [{"when": "broken"}, None])
    client = module.app.test_client()
    response = client.get(
        "/api/status",
        base_url="http://127.0.0.1:8765",
        headers={"X-Venom-Token": module.TOKEN},
    )
    assert response.status_code == 200
    assert response.get_json()["meeting"] == ""



def test_api_wizard_accepts_numbered_backup_key():
    import api_setup

    assert api_setup.has_provider_key({"GEMINI_API_KEY_2": "example-key"})
    assert not api_setup.has_provider_key({"GEMINI_API_KEY_2": ""})



def test_provider_key_cooldown_is_independent(monkeypatch):
    import venom

    monkeypatch.setattr(venom, "PROVIDERS", [("gemini", "key-a"), ("gemini", "key-b")])
    monkeypatch.setattr(venom, "_PROVIDER_COOLDOWN", {})
    monkeypatch.setattr(venom, "_PROVIDER_HEALTH", {})
    venom._cooldown("gemini", RuntimeError("HTTP 429"), "key-a")

    assert venom._provider_key_id("gemini", "key-a") in venom._PROVIDER_COOLDOWN
    assert venom._provider_key_id("gemini", "key-b") not in venom._PROVIDER_COOLDOWN
    assert venom.provider_status()[0]["status"] == "degraded"



def test_openai_provider_route_uses_configured_adapter(monkeypatch, tmp_path):
    import venom

    monkeypatch.setattr(venom, "PROVIDERS", [("openai", "test-key")])
    monkeypatch.setattr(venom, "_PROVIDER_COOLDOWN", {})
    monkeypatch.setattr(venom, "_PROVIDER_HEALTH", {})
    monkeypatch.setattr(venom, "history", [])
    monkeypatch.setattr(venom, "HISTORY_FILE", tmp_path / "history.json")
    monkeypatch.setattr(venom, "call_openai", lambda key, system, contents: "OpenAI route OK")

    assert venom.ask("hello", keep=True) == "OpenAI route OK"
    assert venom._PROVIDER_HEALTH["openai"] == "online"
    assert venom.HISTORY_FILE.exists()
