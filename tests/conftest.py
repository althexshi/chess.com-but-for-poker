import json
import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import poker_coach.api.database as db_module
from poker_coach.api.database import init_db, get_connection


SAMPLE_SCENARIO = {
    "board": "Ah Kd 7c",
    "hole_cards": "QsJs",
    "position": "BTN",
    "pot_size": 12.0,
    "stack_size": 100.0,
    "opponent_action": "One player raised",
    "gto_strategy": {"raise": 15.0, "call": 55.0, "fold": 30.0},
}


@pytest.fixture()
def test_db(tmp_path):
    test_db_path = tmp_path / "test.db"
    with patch.object(db_module, "DB_PATH", test_db_path):
        init_db()
        yield test_db_path


@pytest.fixture()
def seeded_db(test_db):
    conn = sqlite3.connect(str(test_db))
    conn.execute(
        """INSERT INTO scenarios
           (board, hole_cards, position, pot_size, stack_size, opponent_action, gto_strategy)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            SAMPLE_SCENARIO["board"],
            SAMPLE_SCENARIO["hole_cards"],
            SAMPLE_SCENARIO["position"],
            SAMPLE_SCENARIO["pot_size"],
            SAMPLE_SCENARIO["stack_size"],
            SAMPLE_SCENARIO["opponent_action"],
            json.dumps(SAMPLE_SCENARIO["gto_strategy"]),
        ),
    )
    conn.commit()
    conn.close()
    return test_db


@pytest.fixture()
def client(seeded_db):
    with patch.object(db_module, "DB_PATH", seeded_db):
        with patch(
            "poker_coach.api.main.get_coaching",
            return_value={
                "verdict": "good",
                "concept": "range advantage",
                "summary": "Your call aligns with the solver.",
                "advice": "Keep making this play in similar spots.",
            },
        ):
            from poker_coach.api.main import app
            with TestClient(app) as tc:
                yield tc


@pytest.fixture()
def empty_client(test_db):
    with patch.object(db_module, "DB_PATH", test_db):
        with patch(
            "poker_coach.api.main.get_coaching",
            return_value={
                "verdict": "good",
                "concept": "general strategy",
                "summary": "Solid play.",
                "advice": "Keep it up.",
            },
        ):
            from poker_coach.api.main import app
            with TestClient(app) as tc:
                yield tc
