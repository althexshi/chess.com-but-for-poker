from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

VALID_RANKS = set("AKQJT98765432")
VALID_SUITS = set("hdcs")
_COMBO_RE = re.compile(r"^[AKQJT98765432][hdcs][AKQJT98765432][hdcs]$")
_FREQ_SUM_TOLERANCE = 0.005


class UPIParseError(ValueError):
    pass


@dataclass
class ParsedStrategy:
    position: str | None
    actions: list[str]
    combos: dict[str, dict[str, float]] = field(default_factory=dict)

    def to_json(self, compact: bool = True) -> str:
        out: dict[str, list[float]] = {}
        for combo, freqs in self.combos.items():
            values = [round(freqs.get(a, 0.0), 3) for a in self.actions]
            out[combo] = values
        sep = (",", ":") if compact else (", ", ": ")
        return json.dumps(
            {"position": self.position, "actions": self.actions, "combos": out},
            separators=sep,
        )

    def size_bytes(self) -> int:
        return len(self.to_json(compact=True).encode())


def _is_combo(token: str) -> bool:
    return bool(_COMBO_RE.match(token))


def _is_position_token(line: str) -> bool:
    return line.isalpha() and len(line) <= 10 and not _is_combo(line)


def parse_combo_line(line: str, actions: list[str]) -> tuple[str, dict[str, float]]:
    parts = line.split(":")
    if len(parts) < 2:
        raise ValueError(f"Not enough colon-separated fields: {line!r}")

    combo = parts[0].strip()
    if not _is_combo(combo):
        raise ValueError(f"Invalid combo token: {combo!r}")

    freq_strs = parts[1:]
    if len(freq_strs) != len(actions):
        raise ValueError(
            f"Expected {len(actions)} frequencies, got {len(freq_strs)}: {line!r}"
        )

    freqs: list[float] = []
    for s in freq_strs:
        try:
            freqs.append(float(s.strip()))
        except ValueError:
            raise ValueError(f"Non-numeric frequency {s!r} in: {line!r}")

    total = sum(freqs)
    if abs(total - 1.0) > _FREQ_SUM_TOLERANCE:
        raise ValueError(
            f"Frequencies sum to {total:.4f}, expected ~1.0: {line!r}"
        )

    return combo, dict(zip(actions, freqs))


def parse_strategy(
    raw_text: str, actions: list[str] | None = None
) -> ParsedStrategy:
    if not raw_text or not raw_text.strip():
        raise UPIParseError("Empty input")

    lines = [l.strip() for l in raw_text.splitlines() if l.strip()]

    position: str | None = None
    start = 0
    if lines and _is_position_token(lines[0]):
        position = lines[0]
        start = 1

    resolved_actions: list[str] | None = (
        [a.lower() for a in actions] if actions is not None else None
    )
    combos: dict[str, dict[str, float]] = {}

    for line in lines[start:]:
        parts = line.split(":")
        if len(parts) < 2:
            logger.warning("Skipping malformed line (no colon): %r", line)
            continue

        combo_token = parts[0].strip()
        if not _is_combo(combo_token):
            logger.warning("Skipping non-combo line: %r", line)
            continue

        num_freqs = len(parts) - 1

        if resolved_actions is None:
            resolved_actions = [f"action_{i}" for i in range(num_freqs)]
        elif len(resolved_actions) != num_freqs:
            raise UPIParseError(
                f"actions has {len(resolved_actions)} items but line has "
                f"{num_freqs} frequencies: {line!r}"
            )

        try:
            combo, freq_dict = parse_combo_line(line, resolved_actions)
            combos[combo] = freq_dict
        except ValueError as e:
            logger.warning("Skipping invalid line: %s", e)

    if not combos:
        raise UPIParseError("No valid combo lines found")

    result = ParsedStrategy(
        position=position,
        actions=resolved_actions,
        combos=combos,
    )

    sz = result.size_bytes()
    if sz > 50 * 1024:
        logger.warning("Serialized output is %d bytes (exceeds 50KB limit)", sz)

    return result
