import argparse
import random
from .agents.random_policy import RandomPolicy
from .agents.heuristic_policy import HeuristicPolicy
from .agents.combo_policy import ComboAwarePolicy
from .experiments.runner import MonteCarloSimulator
from .experiments.analysis import run_analysis

N_GAMES = 100_000
SEED = 2026


def _random_factory(rng: random.Random) -> RandomPolicy:
    return RandomPolicy(rng)


def _heuristic_factory(_rng: random.Random) -> HeuristicPolicy:
    return HeuristicPolicy()


def _combo_factory(_rng: random.Random) -> ComboAwarePolicy:
    return ComboAwarePolicy()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--games", type=int, default=N_GAMES)
    args = parser.parse_args()

    print("Catch-the-Black-Gun Monte Carlo Simulator")
    print(f"Running {args.games:,} games per experiment (seed={args.seed})\n")

    print("Running Model 0: Random Policy...")
    random_results = MonteCarloSimulator(_random_factory).run(
        args.games, seed=args.seed, verbose=True
    )
    run_analysis(random_results, "Model 0: Random Policy")

    print("Running Model 1: Heuristic Policy...")
    heuristic_results = MonteCarloSimulator(_heuristic_factory).run(
        args.games, seed=args.seed, verbose=True
    )
    run_analysis(heuristic_results, "Model 1: Heuristic Policy")

    print("Running Model 2: Combo-Aware Policy...")
    combo_results = MonteCarloSimulator(_combo_factory).run(
        args.games, seed=args.seed, verbose=True
    )
    run_analysis(combo_results, "Model 2: Combo-Aware Policy")


if __name__ == "__main__":
    main()
