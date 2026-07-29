import json
import itertools

import pytest

from poker_coach.upi_parser import (
    ParsedStrategy,
    UPIParseError,
    parse_combo_line,
    parse_strategy,
)

BASIC_UPI_OUTPUT = """\
OOP
AhAs:0.000:0.500:0.500
AhKs:0.000:0.300:0.700
Ah2d:1.000:0.000:0.000
"""

NO_METADATA_OUTPUT = """\
AhAs:0.000:0.500:0.500
AhKs:0.000:0.300:0.700
"""

SINGLE_COMBO_OUTPUT = "AhAs:0.250:0.750\n"

MIXED_VALIDITY_OUTPUT = """\
OOP
AhAs:0.000:0.500:0.500
BADLINE
AhKs:0.000:0.300:0.700
:0.5:0.5
Ah2d:1.000:0.000:0.000
"""

ACTIONS_3 = ["fold", "call", "raise"]
ACTIONS_2 = ["check", "bet"]


class TestParseComboLine:
    def test_valid_three_actions(self):
        combo, freqs = parse_combo_line("AhKs:0.000:0.300:0.700", ACTIONS_3)
        assert combo == "AhKs"
        assert freqs == {"fold": 0.0, "call": 0.3, "raise": 0.7}

    def test_valid_two_actions(self):
        combo, freqs = parse_combo_line("Td9c:0.400:0.600", ACTIONS_2)
        assert combo == "Td9c"
        assert freqs == {"check": 0.4, "bet": 0.6}

    def test_valid_four_actions(self):
        actions = ["fold", "call", "raise_small", "raise_large"]
        combo, freqs = parse_combo_line("AhAs:0.100:0.200:0.300:0.400", actions)
        assert combo == "AhAs"
        assert freqs["fold"] == pytest.approx(0.1)
        assert freqs["raise_large"] == pytest.approx(0.4)

    def test_invalid_missing_combo(self):
        with pytest.raises(ValueError, match="Not enough"):
            parse_combo_line("nofreqs", ACTIONS_3)

    def test_invalid_non_numeric(self):
        with pytest.raises(ValueError, match="Non-numeric"):
            parse_combo_line("AhKs:abc:0.5:0.5", ACTIONS_3)

    def test_invalid_wrong_freq_count(self):
        with pytest.raises(ValueError, match="Expected 3"):
            parse_combo_line("AhKs:0.5:0.5", ACTIONS_3)

    def test_invalid_bad_combo_token(self):
        with pytest.raises(ValueError, match="Invalid combo"):
            parse_combo_line("XXXX:0.5:0.5", ACTIONS_2)

    def test_freq_sum_tolerance(self):
        combo, freqs = parse_combo_line("AhKs:0.333:0.333:0.333", ACTIONS_3)
        assert combo == "AhKs"
        assert sum(freqs.values()) == pytest.approx(0.999, abs=0.005)

    def test_freq_sum_out_of_tolerance(self):
        with pytest.raises(ValueError, match="sum to"):
            parse_combo_line("AhKs:0.5:0.5:0.5", ACTIONS_3)


class TestParseStrategy:
    def test_basic_with_metadata_and_actions(self):
        result = parse_strategy(BASIC_UPI_OUTPUT, actions=ACTIONS_3)
        assert result.position == "OOP"
        assert result.actions == ["fold", "call", "raise"]
        assert len(result.combos) == 3
        assert result.combos["AhAs"] == {"fold": 0.0, "call": 0.5, "raise": 0.5}

    def test_no_metadata(self):
        result = parse_strategy(NO_METADATA_OUTPUT, actions=ACTIONS_3)
        assert result.position is None
        assert len(result.combos) == 2

    def test_no_explicit_actions(self):
        result = parse_strategy(SINGLE_COMBO_OUTPUT)
        assert result.actions == ["action_0", "action_1"]
        assert result.combos["AhAs"]["action_0"] == 0.25

    def test_malformed_lines_skipped(self):
        result = parse_strategy(MIXED_VALIDITY_OUTPUT, actions=ACTIONS_3)
        assert result.position == "OOP"
        assert len(result.combos) == 3
        assert "AhAs" in result.combos
        assert "AhKs" in result.combos
        assert "Ah2d" in result.combos

    def test_empty_input_raises(self):
        with pytest.raises(UPIParseError, match="Empty input"):
            parse_strategy("")

    def test_whitespace_only_raises(self):
        with pytest.raises(UPIParseError, match="Empty input"):
            parse_strategy("   \n\n  ")

    def test_all_invalid_raises(self):
        with pytest.raises(UPIParseError, match="No valid combo"):
            parse_strategy("garbage\nnonsense\n123")

    def test_actions_lowercased(self):
        result = parse_strategy(SINGLE_COMBO_OUTPUT, actions=["CHECK", "BET"])
        assert result.actions == ["check", "bet"]

    def test_actions_count_mismatch_raises(self):
        with pytest.raises(UPIParseError, match="actions has"):
            parse_strategy(BASIC_UPI_OUTPUT, actions=ACTIONS_2)

    def test_ip_position(self):
        text = "IP\nAhAs:0.500:0.500\n"
        result = parse_strategy(text, actions=ACTIONS_2)
        assert result.position == "IP"


class TestSizeConstraint:
    def test_full_1326_combos_under_50kb(self):
        ranks = "AKQJT98765432"
        suits = "hdcs"
        cards = [r + s for r in ranks for s in suits]
        combos = []
        for i, (c1, c2) in enumerate(itertools.combinations(cards, 2)):
            combos.append(c1 + c2)

        assert len(combos) == 1326

        lines = []
        for combo in combos:
            lines.append(f"{combo}:0.200:0.500:0.300")
        raw = "\n".join(lines)

        result = parse_strategy(raw, actions=ACTIONS_3)
        assert len(result.combos) == 1326
        assert result.size_bytes() < 50 * 1024

    def test_sparse_combos_smaller(self):
        lines = []
        for _ in range(100):
            lines.append("AhAs:1.000:0.000:0.000")
        raw = "\n".join(lines)

        result = parse_strategy(raw, actions=ACTIONS_3)
        full_size = result.size_bytes()

        lines2 = []
        for _ in range(100):
            lines2.append("AhAs:0.333:0.334:0.333")
        raw2 = "\n".join(lines2)

        result2 = parse_strategy(raw2, actions=ACTIONS_3)
        dense_size = result2.size_bytes()

        assert full_size < dense_size


class TestSerialization:
    def test_compact_no_spaces(self):
        result = parse_strategy(BASIC_UPI_OUTPUT, actions=ACTIONS_3)
        j = result.to_json(compact=True)
        assert ": " not in j
        assert ", " not in j

    def test_roundtrip(self):
        result = parse_strategy(BASIC_UPI_OUTPUT, actions=ACTIONS_3)
        j = result.to_json()
        data = json.loads(j)
        assert data["position"] == "OOP"
        assert data["actions"] == ["fold", "call", "raise"]
        assert "AhKs" in data["combos"]
        assert data["combos"]["AhKs"] == [0.0, 0.3, 0.7]

    def test_array_format(self):
        result = parse_strategy("Ah2d:1.000:0.000:0.000\n", actions=ACTIONS_3)
        j = result.to_json()
        data = json.loads(j)
        assert data["combos"]["Ah2d"] == [1.0, 0.0, 0.0]
        assert isinstance(data["combos"]["Ah2d"], list)
