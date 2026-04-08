"""Tests for RL Tournament — multi-agent policy evaluation."""


from strategify.rl.tournament import (
    DovePolicy,
    HawkPolicy,
    RandomPolicy,
    run_tournament,
)


class TestPolicies:
    def test_random_policy(self):
        policy = RandomPolicy()
        obs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        action = policy(obs)
        assert action in [0, 1]

    def test_hawk_policy(self):
        policy = HawkPolicy()
        obs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        action = policy(obs)
        assert action == 1

    def test_dove_policy(self):
        policy = DovePolicy()
        obs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        action = policy(obs)
        assert action == 0


class TestTournament:
    def test_run_tournament_single_episode(self):
        run_tournament(n_episodes=1)

    def test_run_tournament_multiple_episodes(self):
        run_tournament(n_episodes=3)

    def test_tournament_env_initialized(self):
        from strategify.rl.tournament import env

        assert env is not None

    def test_tournament_archetypes_defined(self):
        from strategify.rl.tournament import (
            archetypes,
        )

        assert len(archetypes) == 4
