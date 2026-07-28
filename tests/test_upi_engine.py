import json
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from poker_coach.upi_engine import PioEngine, PioEngineError

MOCK_STRATEGY_OUTPUT = (
    "OOP\n"
    "AhAs:0.000:0.500:0.500\n"
    "AhKs:0.000:0.300:0.700\n"
    "Ah2d:1.000:0.000:0.000\n"
    "END\n"
)

MOCK_LOAD_RESPONSE = "tree loaded\nEND\n"


def _make_mock_proc(stdout_text: str):
    proc = MagicMock()
    proc.stdin = MagicMock()
    proc.stdout = StringIO(stdout_text)
    proc.stderr = MagicMock()
    proc.wait = MagicMock()
    proc.terminate = MagicMock()
    return proc


class TestPioEngineLifecycle:
    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_start_creates_process(self, mock_popen):
        mock_popen.return_value = _make_mock_proc("")
        engine = PioEngine("mock_solver")
        engine.start()
        mock_popen.assert_called_once_with(
            ["mock_solver"],
            stdin=-1,
            stdout=-1,
            stderr=-1,
            text=True,
        )

    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_start_twice_raises(self, mock_popen):
        mock_popen.return_value = _make_mock_proc("")
        engine = PioEngine()
        engine.start()
        with pytest.raises(PioEngineError, match="already running"):
            engine.start()

    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_stop_terminates(self, mock_popen):
        proc = _make_mock_proc("END\n")
        mock_popen.return_value = proc
        engine = PioEngine()
        engine.start()
        engine.stop()
        proc.terminate.assert_called_once()
        proc.wait.assert_called_once()

    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_context_manager(self, mock_popen):
        proc = _make_mock_proc("END\n")
        mock_popen.return_value = proc
        with PioEngine() as engine:
            assert engine._proc is not None
        proc.terminate.assert_called_once()

    def test_send_without_start_raises(self):
        engine = PioEngine()
        with pytest.raises(PioEngineError, match="not running"):
            engine.load_tree("test.cfr")


class TestPioEngineCommands:
    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_load_tree(self, mock_popen):
        proc = _make_mock_proc(MOCK_LOAD_RESPONSE)
        mock_popen.return_value = proc
        engine = PioEngine()
        engine.start()
        result = engine.load_tree("/path/to/tree.cfr")
        assert result == "tree loaded"
        proc.stdin.write.assert_called_with("load_tree /path/to/tree.cfr\n")

    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_show_strategy(self, mock_popen):
        proc = _make_mock_proc(MOCK_STRATEGY_OUTPUT)
        mock_popen.return_value = proc
        engine = PioEngine()
        engine.start()
        result = engine.show_strategy("r:0:c")
        assert "AhAs" in result
        assert "END" not in result

    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_extract_strategy(self, mock_popen):
        proc = _make_mock_proc(MOCK_STRATEGY_OUTPUT)
        mock_popen.return_value = proc
        engine = PioEngine()
        engine.start()
        parsed = engine.extract_strategy(
            "r:0:c", actions=["fold", "call", "raise"]
        )
        assert parsed.position == "OOP"
        assert len(parsed.combos) == 3
        assert parsed.combos["AhAs"] == {"fold": 0.0, "call": 0.5, "raise": 0.5}


class TestExtractAndSave:
    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_saves_json_file(self, mock_popen, tmp_path):
        proc = _make_mock_proc(MOCK_STRATEGY_OUTPUT)
        mock_popen.return_value = proc
        engine = PioEngine()
        engine.start()

        out_file = tmp_path / "strategies" / "node1.json"
        parsed = engine.extract_and_save(
            "r:0:c", out_file, actions=["fold", "call", "raise"]
        )

        assert out_file.exists()
        data = json.loads(out_file.read_text())
        assert data["position"] == "OOP"
        assert data["actions"] == ["fold", "call", "raise"]
        assert len(data["combos"]) == 3

    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_creates_parent_dirs(self, mock_popen, tmp_path):
        proc = _make_mock_proc(MOCK_STRATEGY_OUTPUT)
        mock_popen.return_value = proc
        engine = PioEngine()
        engine.start()

        out_file = tmp_path / "a" / "b" / "c" / "out.json"
        engine.extract_and_save(
            "r:0:c", out_file, actions=["fold", "call", "raise"]
        )
        assert out_file.exists()


class TestEndToEndMockPipeline:
    @patch("poker_coach.upi_engine.subprocess.Popen")
    def test_load_then_extract(self, mock_popen, tmp_path):
        load_output = "tree loaded successfully\nEND\n"
        strategy_output = (
            "IP\n"
            "AhAs:0.100:0.900\n"
            "KhKs:0.400:0.600\n"
            "END\n"
        )
        combined = load_output + strategy_output
        proc = _make_mock_proc(combined)
        mock_popen.return_value = proc

        engine = PioEngine()
        engine.start()

        load_resp = engine.load_tree("/data/solve.cfr")
        assert "loaded" in load_resp

        parsed = engine.extract_strategy("r:0", actions=["check", "bet"])
        assert parsed.position == "IP"
        assert len(parsed.combos) == 2
        assert parsed.combos["KhKs"]["bet"] == pytest.approx(0.6)

        out_file = tmp_path / "result.json"
        out_file.write_text(parsed.to_json())
        data = json.loads(out_file.read_text())
        assert data["combos"]["AhAs"] == [0.1, 0.9]
