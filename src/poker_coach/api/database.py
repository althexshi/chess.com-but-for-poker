import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "poker_coach.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS scenarios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            board           TEXT NOT NULL,
            hole_cards      TEXT NOT NULL,
            position        TEXT NOT NULL,
            pot_size        REAL NOT NULL,
            stack_size      REAL NOT NULL,
            opponent_action TEXT NOT NULL DEFAULT '',
            gto_strategy    TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS telemetry (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL REFERENCES users(id),
            scenario_id     INTEGER NOT NULL REFERENCES scenarios(id),
            action          TEXT NOT NULL,
            bet_size        REAL,
            prev_outcome    TEXT,
            response_time_ms INTEGER,
            created_at      TEXT DEFAULT (datetime('now'))
        );
    """)

    # Seed sample scenarios if the database is empty
    scenario_count = conn.execute(
        "SELECT COUNT(*) AS count FROM scenarios"
    ).fetchone()["count"]

    if scenario_count == 0:
        sample_scenarios = [
            {
                "board": "Ah Kd 7c",
                "hole_cards": "Qs Qh",
                "position": "BTN",
                "pot_size": 10.0,
                "stack_size": 100.0,
                "opponent_action": "Opponent bets half pot",
                "gto_strategy": {
                    "fold": 0.15,
                    "call": 0.55,
                    "raise": 0.30
                },
            },
            {
                "board": "9s 8s 2d",
                "hole_cards": "As Ks",
                "position": "CO",
                "pot_size": 14.0,
                "stack_size": 95.0,
                "opponent_action": "Opponent checks",
                "gto_strategy": {
                    "fold": 0.05,
                    "call": 0.25,
                    "raise": 0.70
                },
            },
            {
                "board": "Jh 6c 3d",
                "hole_cards": "7h 7s",
                "position": "BB",
                "pot_size": 8.0,
                "stack_size": 80.0,
                "opponent_action": "Opponent raises preflop",
                "gto_strategy": {
                    "fold": 0.45,
                    "call": 0.45,
                    "raise": 0.10
                },
            },
            {
                "board": "Ts 9c 4h",
                "hole_cards": "Ad Qd",
                "position": "SB",
                "pot_size": 12.0,
                "stack_size": 90.0,
                "opponent_action": "Opponent calls",
                "gto_strategy": {
                    "fold": 0.20,
                    "call": 0.50,
                    "raise": 0.30
                },
            },
        ]

        for scenario in sample_scenarios:
            conn.execute(
                """
                INSERT INTO scenarios
                (board, hole_cards, position, pot_size, stack_size, opponent_action, gto_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scenario["board"],
                    scenario["hole_cards"],
                    scenario["position"],
                    scenario["pot_size"],
                    scenario["stack_size"],
                    scenario["opponent_action"],
                    json.dumps(scenario["gto_strategy"]),
                ),
            )

    conn.commit()
    conn.close()


def get_random_scenario(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute(
        "SELECT * FROM scenarios ORDER BY RANDOM() LIMIT 1"
    ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["gto_strategy"] = json.loads(result["gto_strategy"])
    return result


def get_scenario_by_id(conn: sqlite3.Connection, scenario_id: int) -> dict | None:
    row = conn.execute(
        "SELECT * FROM scenarios WHERE id = ?", (scenario_id,)
    ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["gto_strategy"] = json.loads(result["gto_strategy"])
    return result


def get_or_create_user(conn: sqlite3.Connection, username: str) -> int:
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()

    if row:
        return row["id"]

    cursor = conn.execute(
        "INSERT INTO users (username) VALUES (?)", (username,)
    )
    conn.commit()
    return cursor.lastrowid


def insert_telemetry(
    conn: sqlite3.Connection,
    user_id: int,
    scenario_id: int,
    action: str,
    bet_size: float | None,
    prev_outcome: str | None,
    response_time_ms: int | None,
) -> None:
    conn.execute(
        """
        INSERT INTO telemetry
        (user_id, scenario_id, action, bet_size, prev_outcome, response_time_ms)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            scenario_id,
            action,
            bet_size,
            prev_outcome,
            response_time_ms,
        ),
    )
    conn.commit()