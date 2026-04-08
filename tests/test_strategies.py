import axelrod as axl

from strategify.reasoning.strategies import (
    DEESCALATE,
    ESCALATE,
    DiplomacyStrategy,
    OpponentProxy,
)


class TestOpponentProxy:
    def test_initial_state(self):
        proxy = OpponentProxy()
        assert proxy.cooperations == 0
        assert proxy.defections == 0
        assert list(proxy.history) == []

    def test_update_records_opponent_action(self):
        proxy = OpponentProxy()
        proxy.update(DEESCALATE, ESCALATE)
        assert proxy.defections == 1
        assert list(proxy.history) == [axl.Action.D]

    def test_update_records_multiple(self):
        proxy = OpponentProxy()
        proxy.update(DEESCALATE, ESCALATE)
        proxy.update(ESCALATE, DEESCALATE)
        assert proxy.cooperations == 1
        assert proxy.defections == 1


class TestDiplomacyStrategy:
    def test_available_personalities(self):
        personalities = DiplomacyStrategy.available_personalities()
        assert "Aggressor" in personalities
        assert "Pacifist" in personalities
        assert "Tit-for-Tat" in personalities
        assert "Neutral" in personalities
        assert "Grudger" in personalities

    def test_aggressor_always_escalates(self):
        s = DiplomacyStrategy("Aggressor")
        for _ in range(5):
            action = s.decide(ESCALATE)
            assert action == ESCALATE

    def test_pacifist_always_deescalates(self):
        s = DiplomacyStrategy("Pacifist")
        for _ in range(5):
            action = s.decide(ESCALATE)
            assert action == DEESCALATE

    def test_tit_for_tat_mirrors_opponent(self):
        s = DiplomacyStrategy("Tit-for-Tat")
        # First move is always deescalate (no history)
        assert s.decide() == DEESCALATE
        # After opponent escalates, mirrors escalation
        assert s.decide(ESCALATE) == ESCALATE
        # After opponent deescalates, mirrors deescalation
        assert s.decide(DEESCALATE) == DEESCALATE

    def test_tit_for_tat_alternating(self):
        s = DiplomacyStrategy("Tit-for-Tat")
        # Turn 0: no prior opponent action
        assert s.decide() == DEESCALATE
        # Turns 1-4: mirror the opponent's responses
        # Turn 1: opponent responded to our C with E → mirror E
        assert s.decide(ESCALATE) == ESCALATE
        # Turn 2: opponent responded to our E with d → mirror d
        assert s.decide(DEESCALATE) == DEESCALATE
        # Turn 3: opponent responded to our d with E → mirror E
        assert s.decide(ESCALATE) == ESCALATE
        # Turn 4: opponent responded to our E with d → mirror d
        assert s.decide(DEESCALATE) == DEESCALATE

    def test_grudger_triggers_on_defection(self):
        """Grudger cooperates until opponent defects, then always defects."""
        s = DiplomacyStrategy("Grudger")
        # First move: cooperate
        assert s.decide() == DEESCALATE
        # Opponent defects — grudger triggers and always defects
        assert s.decide(ESCALATE) == ESCALATE
        # Even after opponent cooperates, grudger stays triggered
        assert s.decide(DEESCALATE) == ESCALATE
        assert s.decide(DEESCALATE) == ESCALATE

    def test_reset_clears_state(self):
        s = DiplomacyStrategy("Tit-for-Tat")
        s.decide()  # C
        s.decide(ESCALATE)  # D (mirrored)
        s.reset()
        # After reset, behaves as fresh
        assert s.decide() == DEESCALATE

    def test_returns_valid_actions(self):
        for personality in DiplomacyStrategy.available_personalities():
            s = DiplomacyStrategy(personality)
            for _ in range(10):
                action = s.decide(ESCALATE)
                assert action in (ESCALATE, DEESCALATE)

    def test_default_personality_is_neutral(self):
        s = DiplomacyStrategy()
        assert s.personality == "Neutral"

    def test_unknown_personality_falls_back(self):
        s = DiplomacyStrategy("NonexistentPersonality")
        # Should fall back to GoByMajority without crashing
        action = s.decide(ESCALATE)
        assert action in (ESCALATE, DEESCALATE)
