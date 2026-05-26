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
    def __init__(self, factory_or_factories) -> None:
        if callable(factory_or_factories):
            self._factories = [factory_or_factories] * 3
        else:
            self._factories = list(factory_or_factories)
            assert len(self._factories) == 3

    def run(self, n_games: int, seed: int, verbose: bool = False) -> SimResults:
        rng = random.Random(seed)
        wins = [0, 0, 0]
        total_turns = 0
        report_every = max(1, n_games // 10)

        for i in range(n_games):
            game_rng = random.Random(rng.random())
            policies = [self._factories[j](random.Random(rng.random())) for j in range(3)]
            winner, turns = GameRound(game_rng).play(policies)
            wins[winner] += 1
            total_turns += turns

            if verbose and (i + 1) % report_every == 0:
                done = i + 1
                bg_rate = wins[0] / done
                p1_rate = wins[1] / done
                p2_rate = wins[2] / done
                print(
                    f"  {done:>7,}/{n_games:,}  ({done/n_games*100:5.1f}%)  "
                    f"| black gun: {bg_rate:.3f}  P1: {p1_rate:.3f}  P2: {p2_rate:.3f}",
                    flush=True,
                )

        return SimResults(n_games=n_games, wins=wins, total_turns=total_turns)
