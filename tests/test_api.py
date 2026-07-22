import json
import sqlite3

from tests.conftest import SAMPLE_SCENARIO


class TestNextScenario:
    def test_returns_scenario(self, client):
        resp = client.get("/api/scenarios/next")
        assert resp.status_code == 200
        data = resp.json()
        assert data["board"] == SAMPLE_SCENARIO["board"]
        assert data["hole_cards"] == SAMPLE_SCENARIO["hole_cards"]
        assert data["position"] == SAMPLE_SCENARIO["position"]
        assert data["pot_size"] == SAMPLE_SCENARIO["pot_size"]
        assert data["stack_size"] == SAMPLE_SCENARIO["stack_size"]
        assert data["opponent_action"] == SAMPLE_SCENARIO["opponent_action"]
        assert "gto_strategy" not in data

    def test_returns_404_when_empty(self, empty_client):
        resp = empty_client.get("/api/scenarios/next")
        assert resp.status_code == 404


class TestEvaluate:
    def test_returns_gto_comparison(self, client):
        scenario = client.get("/api/scenarios/next").json()
        resp = client.post("/api/evaluate", json={
            "scenario_id": scenario["id"],
            "username": "testplayer",
            "action": "call",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["comparison"]["user_action"] == "call"
        assert data["comparison"]["gto_strategy"] == SAMPLE_SCENARIO["gto_strategy"]
        assert data["comparison"]["match_pct"] == 55.0

    def test_returns_zero_for_unknown_action(self, client):
        scenario = client.get("/api/scenarios/next").json()
        resp = client.post("/api/evaluate", json={
            "scenario_id": scenario["id"],
            "username": "testplayer",
            "action": "all-in",
        })
        assert resp.status_code == 200
        assert resp.json()["comparison"]["match_pct"] == 0.0

    def test_returns_coaching_feedback(self, client):
        scenario = client.get("/api/scenarios/next").json()
        resp = client.post("/api/evaluate", json={
            "scenario_id": scenario["id"],
            "username": "testplayer",
            "action": "call",
        })
        coaching = resp.json()["coaching"]
        assert coaching["verdict"] in ("good", "okay", "mistake")
        assert coaching["concept"]
        assert coaching["summary"]
        assert coaching["advice"]

    def test_scenario_not_found(self, client):
        resp = client.post("/api/evaluate", json={
            "scenario_id": 9999,
            "username": "testplayer",
            "action": "fold",
        })
        assert resp.status_code == 404

    def test_auto_creates_user(self, client, seeded_db):
        scenario = client.get("/api/scenarios/next").json()
        client.post("/api/evaluate", json={
            "scenario_id": scenario["id"],
            "username": "newplayer",
            "action": "fold",
        })
        conn = sqlite3.connect(str(seeded_db))
        row = conn.execute(
            "SELECT username FROM users WHERE username = ?", ("newplayer",)
        ).fetchone()
        conn.close()
        assert row is not None


class TestTelemetry:
    def test_telemetry_logged_on_evaluate(self, client, seeded_db):
        scenario = client.get("/api/scenarios/next").json()
        client.post("/api/evaluate", json={
            "scenario_id": scenario["id"],
            "username": "telemetryuser",
            "action": "raise",
            "bet_size": 24.0,
            "prev_outcome": "win",
            "response_time_ms": 3200,
        })
        conn = sqlite3.connect(str(seeded_db))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row is not None
        assert row["action"] == "raise"
        assert row["bet_size"] == 24.0
        assert row["prev_outcome"] == "win"
        assert row["response_time_ms"] == 3200

    def test_telemetry_nullable_fields(self, client, seeded_db):
        scenario = client.get("/api/scenarios/next").json()
        client.post("/api/evaluate", json={
            "scenario_id": scenario["id"],
            "username": "minimaluser",
            "action": "check",
        })
        conn = sqlite3.connect(str(seeded_db))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        assert row["bet_size"] is None
        assert row["prev_outcome"] is None
        assert row["response_time_ms"] is None


class TestUsers:
    def test_create_user(self, client):
        resp = client.post("/api/users", json={"username": "alice"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "alice"
        assert isinstance(data["id"], int)

    def test_create_duplicate_returns_same_id(self, client):
        resp1 = client.post("/api/users", json={"username": "bob"})
        resp2 = client.post("/api/users", json={"username": "bob"})
        assert resp1.json()["id"] == resp2.json()["id"]
