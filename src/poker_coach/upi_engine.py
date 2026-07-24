from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

from poker_coach.upi_parser import ParsedStrategy, parse_strategy

logger = logging.getLogger(__name__)

END_MARKER = "END"


class PioEngineError(RuntimeError):
    pass


class PioEngine:
    def __init__(self, executable: str = "PioSOLVER2-pro"):
        self._executable = executable
        self._proc: subprocess.Popen | None = None

    def start(self) -> None:
        if self._proc is not None:
            raise PioEngineError("Engine already running")
        self._proc = subprocess.Popen(
            [self._executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    def stop(self) -> None:
        if self._proc is None:
            return
        try:
            self._send("exit")
        except PioEngineError:
            pass
        self._proc.terminate()
        self._proc.wait(timeout=5)
        self._proc = None

    def _send(self, command: str) -> str:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise PioEngineError("Engine not running")

        self._proc.stdin.write(command + "\n")
        self._proc.stdin.flush()

        lines: list[str] = []
        for line in self._proc.stdout:
            stripped = line.rstrip("\n")
            if stripped == END_MARKER:
                break
            lines.append(stripped)

        return "\n".join(lines)

    def load_tree(self, cfr_path: str) -> str:
        return self._send(f"load_tree {cfr_path}")

    def show_strategy(self, node: str) -> str:
        return self._send(f"show_strategy {node}")

    def extract_strategy(
        self, node: str, actions: list[str] | None = None
    ) -> ParsedStrategy:
        raw = self.show_strategy(node)
        return parse_strategy(raw, actions=actions)

    def extract_and_save(
        self,
        node: str,
        output_path: Path,
        actions: list[str] | None = None,
    ) -> ParsedStrategy:
        parsed = self.extract_strategy(node, actions=actions)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(parsed.to_json())
        logger.info("Saved strategy to %s (%d bytes)", output_path, parsed.size_bytes())
        return parsed

    def __enter__(self) -> PioEngine:
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()
