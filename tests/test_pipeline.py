import json

from poker_coach.pipeline import convert_and_save, strategy_to_scenarios

STRATEGY_DATA = {
    "position": "OOP",
    "actions": ["fold", "call", "raise"],
    "combos": {
        "AhAs": [0.0, 0.5, 0.5],
        "AhKs": [0.0, 0.3, 0.7],
        "Ah2d": [1.0, 0.0, 0.0],
        "KhQs": [0.2, 0.4, 0.4],
    },
}


def _write_strategy(tmp_path, data=None):
    p = tmp_path / "strategy.json"
    p.write_text(json.dumps(data or STRATEGY_DATA))
    return p


class TestStrategyToScenarios:
    def test_auto_selects_mixed_hands(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ah Kd 7c", pot_size=12.0, stack_size=100.0,
        )
        hole_cards = [s["hole_cards"] for s in scenarios]
        assert "Ah 2d" not in hole_cards
        assert len(scenarios) >= 2

    def test_explicit_combos(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ts 9s 2h", pot_size=8.5, stack_size=95.0,
            combos=["AhAs", "Ah2d"],
        )
        assert len(scenarios) == 2
        cards = {s["hole_cards"] for s in scenarios}
        assert "Ah As" in cards
        assert "Ah 2d" in cards

    def test_gto_strategy_percentages(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ah Kd 7c", pot_size=12.0, stack_size=100.0,
            combos=["AhKs"],
        )
        gto = scenarios[0]["gto_strategy"]
        assert gto["call"] == 30.0
        assert gto["raise"] == 70.0
        assert "fold" not in gto

    def test_zero_freq_omitted(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ah Kd 7c", pot_size=12.0, stack_size=100.0,
            combos=["AhAs"],
        )
        assert "fold" not in scenarios[0]["gto_strategy"]

    def test_position_from_strategy(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ah Kd 7c", pot_size=12.0, stack_size=100.0,
            combos=["AhAs"],
        )
        assert scenarios[0]["position"] == "OOP"

    def test_max_scenarios_limit(self, tmp_path):
        data = {
            "position": "IP",
            "actions": ["check", "bet"],
            "combos": {f"Ah{r}s": [0.5, 0.5] for r in "KQJT9876543"},
        }
        path = _write_strategy(tmp_path, data)
        scenarios = strategy_to_scenarios(
            path, board="2c 3c 4c", pot_size=10.0, stack_size=100.0,
            max_scenarios=3,
        )
        assert len(scenarios) == 3

    def test_scenario_fields_complete(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ah Kd 7c", pot_size=12.0, stack_size=100.0,
            opponent_action="One player raised", combos=["AhAs"],
        )
        s = scenarios[0]
        assert s["board"] == "Ah Kd 7c"
        assert s["pot_size"] == 12.0
        assert s["stack_size"] == 100.0
        assert s["opponent_action"] == "One player raised"

    def test_missing_combo_ignored(self, tmp_path):
        path = _write_strategy(tmp_path)
        scenarios = strategy_to_scenarios(
            path, board="Ah Kd 7c", pot_size=12.0, stack_size=100.0,
            combos=["AhAs", "XxYy"],
        )
        assert len(scenarios) == 1


class TestConvertAndSave:
    def test_writes_json_file(self, tmp_path):
        strat_path = _write_strategy(tmp_path)
        out_path = tmp_path / "output" / "scenarios.json"
        count = convert_and_save(
            strat_path, out_path, board="Ah Kd 7c",
            pot_size=12.0, stack_size=100.0,
        )
        assert out_path.exists()
        data = json.loads(out_path.read_text())
        assert len(data) == count
        assert count > 0

    def test_output_compatible_with_ingest(self, tmp_path):
        strat_path = _write_strategy(tmp_path)
        out_path = tmp_path / "scenarios.json"
        convert_and_save(
            strat_path, out_path, board="Ah Kd 7c",
            pot_size=12.0, stack_size=100.0, combos=["AhAs"],
        )
        data = json.loads(out_path.read_text())
        required = {"board", "hole_cards", "position", "pot_size", "stack_size", "gto_strategy"}
        for scenario in data:
            assert required.issubset(scenario.keys())
