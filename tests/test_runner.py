from dou_dizhu_simulator.experiments.runner import MonteCarloSimulator, SimResults
from dou_dizhu_simulator.agents.random_policy import RandomPolicy
from dou_dizhu_simulator.agents.heuristic_policy import HeuristicPolicy
import random


def _random_factory(rng):
    return RandomPolicy(rng)


def _heuristic_factory(_rng):
    return HeuristicPolicy()


def test_sim_results_count_correct():
    sim = MonteCarloSimulator(_random_factory)
    results = sim.run(n_games=100, seed=0)
    assert results.n_games == 100
    assert sum(results.wins) == 100


def test_sim_win_rates_sum_to_1():
    sim = MonteCarloSimulator(_random_factory)
    results = sim.run(n_games=200, seed=1)
    assert abs(sum(results.win_rates) - 1.0) < 1e-9


def test_sim_reproducible():
    sim = MonteCarloSimulator(_random_factory)
    r1 = sim.run(n_games=500, seed=42)
    r2 = sim.run(n_games=500, seed=42)
    assert r1.wins == r2.wins


def test_sim_heuristic_terminates():
    sim = MonteCarloSimulator(_heuristic_factory)
    results = sim.run(n_games=100, seed=0)
    assert sum(results.wins) == 100


def test_sim_tracks_turns():
    sim = MonteCarloSimulator(_random_factory)
    results = sim.run(n_games=100, seed=0)
    assert results.total_turns > 0
    assert results.avg_turns > 0


def test_game_passes_opponent_hand_sizes():
    from dou_dizhu_simulator.agents.base import PlayerPolicy
    from dou_dizhu_simulator.engine.game import GameRound

    sizes_received = []

    class RecordingPolicy(PlayerPolicy):
        def __init__(self, inner):
            self._inner = inner
        def choose_move(self, hand, legal_moves, last_combo, opponent_hand_sizes=None,
                        ace_revealed=False, last_player_idx=None):
            sizes_received.append(opponent_hand_sizes)
            return self._inner.choose_move(hand, legal_moves, last_combo)

    rng = random.Random(42)
    inner = [RandomPolicy(random.Random(rng.random())) for _ in range(3)]
    recording = [RecordingPolicy(p) for p in inner]
    GameRound(random.Random(42)).play(recording)

    assert sizes_received[0] is not None
    assert len(sizes_received[0]) == 2       # exactly two opponents
    assert sum(sizes_received[0]) == 36      # 18 + 18 at game start
