"""
CLI to ingest GTO scenario data into the SQLite database.

Usage:
    python -m poker_coach.ingest scenarios.json
    python -m poker_coach.ingest scenario_dir/

Expected JSON format — a list of scenario objects:
[
    {
        "board": "Ah Kd 7c",
        "hole_cards": "QsJs",
        "position": "BTN",
        "pot_size": 12.0,
        "stack_size": 100.0,
        "opponent_action": "One player raised",
        "gto_strategy": {"raise": 55.0, "call": 30.0, "fold": 15.0}
    },
    ...
]

Also accepts a directory — all .json files in it will be ingested.
"""

import json
import sys
from pathlib import Path

from poker_coach.api.database import get_connection, init_db

REQUIRED_FIELDS = {"board", "hole_cards", "position", "pot_size", "stack_size", "gto_strategy"}


def load_scenarios(path: Path) -> list[dict]:
    if path.is_dir():
        scenarios = []
        for f in sorted(path.glob("*.json")):
            scenarios.extend(json.loads(f.read_text()))
        return scenarios
    return json.loads(path.read_text())


def ingest(scenarios: list[dict]) -> int:
    conn = get_connection()
    count = 0
    for s in scenarios:
        missing = REQUIRED_FIELDS - s.keys()
        if missing:
            print(f"Skipping scenario missing fields {missing}: {s.get('board', '?')}")
            continue
        conn.execute(
            """INSERT INTO scenarios
               (board, hole_cards, position, pot_size, stack_size, opponent_action, gto_strategy)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                s["board"],
                s["hole_cards"],
                s["position"],
                s["pot_size"],
                s["stack_size"],
                s.get("opponent_action", ""),
                json.dumps(s["gto_strategy"]),
            ),
        )
        count += 1
    conn.commit()
    conn.close()
    return count


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m poker_coach.ingest <path-to-json-or-directory>")
        sys.exit(1)

    init_db()
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Path not found: {path}")
        sys.exit(1)

    scenarios = load_scenarios(path)
    count = ingest(scenarios)
    print(f"Ingested {count} scenarios into database.")


if __name__ == "__main__":
    main()
