"""
Debug script: inspect game traces and run mini-simulations.

Usage:
  python debug_game.py                   # trace 1 random game + 10-game mini-sim
  python debug_game.py --seed 7          # specific seed (reproducible)
  python debug_game.py --random-seed     # fresh seed every run (varied output)
  python debug_game.py --heuristic       # use heuristic policy instead
  python debug_game.py --games 3         # trace first N games
"""
import argparse
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dou_dizhu_simulator.engine.game import GameRound
from dou_dizhu_simulator.agents.random_policy import RandomPolicy
from dou_dizhu_simulator.agents.heuristic_policy import HeuristicPolicy
from dou_dizhu_simulator.agents.combo_policy import ComboAwarePolicy
from dou_dizhu_simulator.experiments.runner import MonteCarloSimulator
from dou_dizhu_simulator.experiments.analysis import run_analysis

def make_policies(policy_type: str, rng: random.Random):
    if policy_type == "heuristic":
        return [HeuristicPolicy() for _ in range(3)]
    if policy_type == "combo":
        return [ComboAwarePolicy() for _ in range(3)]
    return [RandomPolicy(random.Random(rng.random())) for _ in range(3)]


def trace_games(seed: int, n: int, policy_type: str) -> None:
    print(f"\n{'='*60}")
    print(f"  TRACED GAMES  (policy={policy_type}, seed={seed}, n={n})")
    print(f"{'='*60}")
    rng = random.Random(seed)
    for game_idx in range(n):
        print(f"\n--- Game {game_idx + 1} -------------------------------------------")
        game_rng = random.Random(rng.random())
        policies = make_policies(policy_type, random.Random(rng.random()))
        winner, turns = GameRound(game_rng).play(policies, trace=True)
        label = " (BLACK GUN)" if winner == 0 else ""
        print(f"--- Result: P{winner}{label} wins  |  {turns} turns")


def mini_sim(seed: int, n_games: int, policy_type: str) -> None:
    print(f"\n{'='*60}")
    print(f"  MINI SIMULATION  (policy={policy_type}, seed={seed}, n={n_games})")
    print(f"{'='*60}")

    if policy_type == "heuristic":
        factory = lambda _rng: HeuristicPolicy()
    elif policy_type == "combo":
        factory = lambda _rng: ComboAwarePolicy()
    else:
        factory = lambda rng: RandomPolicy(rng)

    sim = MonteCarloSimulator(factory)
    results = sim.run(n_games, seed=seed, verbose=False)

    for i, (w, r) in enumerate(zip(results.wins, results.win_rates)):
        label = " <- BLACK GUN" if i == 0 else ""
        print(f"  P{i}: {w:>3} wins  ({r:.3f}){label}")
    print(f"  Avg turns: {results.avg_turns:.1f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--random-seed", action="store_true",
                        help="Use a random seed instead of a fixed one")
    parser.add_argument("--heuristic", action="store_true")
    parser.add_argument("--combo", action="store_true",
                        help="Use combo-aware policy instead of heuristic")
    parser.add_argument("--games", type=int, default=1,
                        help="Number of games to trace (default: 1)")
    parser.add_argument("--mini", type=int, default=10,
                        help="Number of games for mini-sim (default: 10)")
    parser.add_argument("--no-trace", action="store_true",
                        help="Skip trace, only run mini-sim")
    args = parser.parse_args()

    if args.random_seed:
        seed = random.randint(0, 999_999)
    elif args.seed is not None:
        seed = args.seed
    else:
        seed = 42

    if args.combo:
        policy_type = "combo"
    elif args.heuristic:
        policy_type = "heuristic"
    else:
        policy_type = "random"

    if not args.no_trace:
        trace_games(seed, args.games, policy_type)

    mini_sim(seed, args.mini, policy_type)

    # Run both policies for a quick comparison
    if not args.no_trace:
        print(f"\n{'='*60}")
        print(f"  QUICK COMPARISON  ({args.mini} games each)")
        print(f"{'='*60}")
        for ptype in ("random", "heuristic", "combo"):
            if ptype == "heuristic":
                factory = lambda _r: HeuristicPolicy()
            elif ptype == "combo":
                factory = lambda _r: ComboAwarePolicy()
            else:
                factory = lambda r: RandomPolicy(r)
            results = MonteCarloSimulator(factory).run(args.mini, seed=seed)
            bg = results.wins[0]
            print(f"  {ptype:>10}: black gun {bg}/{args.mini}  ({results.win_rates[0]:.3f})")


if __name__ == "__main__":
    main()
