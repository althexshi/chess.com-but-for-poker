from __future__ import annotations

import json
from pathlib import Path


def _is_mixed(freqs: list[float], threshold: float = 0.05) -> bool:
    nonzero = [f for f in freqs if f >= threshold]
    return len(nonzero) >= 2


def _combo_to_display(combo: str) -> str:
    return combo[:2] + " " + combo[2:]


def strategy_to_scenarios(
    strategy_path: Path,
    board: str,
    pot_size: float,
    stack_size: float,
    opponent_action: str = "",
    combos: list[str] | None = None,
    max_scenarios: int = 50,
) -> list[dict]:
    data = json.loads(strategy_path.read_text())
    actions: list[str] = data["actions"]
    position: str = data.get("position") or "BTN"
    all_combos: dict[str, list[float]] = data["combos"]

    if combos is not None:
        selected = {c: all_combos[c] for c in combos if c in all_combos}
    else:
        selected = {
            c: freqs for c, freqs in all_combos.items() if _is_mixed(freqs)
        }

    sorted_combos = sorted(
        selected.items(),
        key=lambda item: max(item[1]) - min(item[1]),
    )[:max_scenarios]

    scenarios = []
    for combo, freqs in sorted_combos:
        gto = {}
        for action, freq in zip(actions, freqs):
            pct = round(freq * 100, 1)
            if pct > 0:
                gto[action] = pct
        scenarios.append({
            "board": board,
            "hole_cards": _combo_to_display(combo),
            "position": position,
            "pot_size": pot_size,
            "stack_size": stack_size,
            "opponent_action": opponent_action,
            "gto_strategy": gto,
        })

    return scenarios


def convert_and_save(
    strategy_path: Path,
    output_path: Path,
    board: str,
    pot_size: float,
    stack_size: float,
    opponent_action: str = "",
    combos: list[str] | None = None,
    max_scenarios: int = 50,
) -> int:
    scenarios = strategy_to_scenarios(
        strategy_path, board, pot_size, stack_size,
        opponent_action, combos, max_scenarios,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(scenarios, indent=2))
    return len(scenarios)
