from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_and_phase_contract():
    health = client.get("/v1/health")
    assert health.status_code == 200
    assert health.json()["phase"] == 3
    status = client.get("/v1/status")
    assert status.status_code == 200
    body = status.json()
    assert body["agent_can_send"] is False
    assert body["agent_can_write_calendar"] is False


def test_kill_switch_and_audit_and_ingest():
    paused = client.post("/v1/settings/kill-switch", json={"writes_enabled": False})
    assert paused.status_code == 200
    assert paused.json()["writes_enabled"] is False

    seeded = client.post("/v1/dev/seed-tuesday")
    assert seeded.status_code == 200
    assert seeded.json()["seeded"] == 5

    inbox = client.get("/v1/inbox/messages")
    assert inbox.status_code == 200
    subjects = {item["subject"] for item in inbox.json()}
    assert "Re: Weekly recap — week of 10 Mar" in subjects
    recap = next(item for item in inbox.json() if "Facebook" in item["body_text"])
    thread = [item for item in inbox.json() if item["thread_id"] == recap["thread_id"]]
    assert thread

    blocked = client.post("/v1/drafts/anything/approve")
    assert blocked.status_code == 403

    audit = client.get("/v1/audit")
    actions = {row["action"] for row in audit.json()}
    assert "kill_switch_toggled" in actions
    assert "message_ingested" in actions
