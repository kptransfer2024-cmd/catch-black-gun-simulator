import random
from dataclasses import dataclass
from typing import Callable, List
from ..engine.game import GameRound
from ..agents.base import PlayerPolicy


@dataclass
class SimResults:
    n_games: int
    wins: List[int]       # wins[i] = win count for player i
    total_turns: int

    @property
    def win_rates(self) -> List[float]:
        return [w / self.n_games for w in self.wins]

    @property
    def avg_turns(self) -> float:
        return self.total_turns / self.n_games


PolicyFactory = Callable[[random.Random], PlayerPolicy]


class MonteCarloSimulator:
    def __init__(self, policy_factory: PolicyFactory) -> None:
        self._factory = policy_factory

    def run(self, n_games: int, seed: int) -> SimResults:
        rng = random.Random(seed)
        wins = [0, 0, 0]
        total_turns = 0

        for _ in range(n_games):
            game_rng = random.Random(rng.random())
            policies = [self._factory(random.Random(rng.random())) for _ in range(3)]
            winner, turns = GameRound(game_rng).play(policies)
            wins[winner] += 1
            total_turns += turns

        return SimResults(n_games=n_games, wins=wins, total_turns=total_turns)
