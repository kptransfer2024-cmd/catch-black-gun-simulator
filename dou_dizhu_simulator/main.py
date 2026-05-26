import argparse
import random
from .agents.random_policy import RandomPolicy
from .agents.heuristic_policy import HeuristicPolicy
from .agents.combo_policy import ComboAwarePolicy
from .agents.tactical_policy import TacticalPolicy
from .agents.coalition_policy import CoalitionPolicy
from .agents.coalition_refined_policy import CoalitionRefinedPolicy
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


def _tactical_factory(_rng: random.Random) -> TacticalPolicy:
    return TacticalPolicy()


def _coalition_factories():
    return [
        lambda _rng: TacticalPolicy(),
        lambda _rng: CoalitionPolicy(1),
        lambda _rng: CoalitionPolicy(2),
    ]


def _coalition_refined_factories():
    return [
        lambda _rng: TacticalPolicy(),
        lambda _rng: CoalitionRefinedPolicy(1),
        lambda _rng: CoalitionRefinedPolicy(2),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--games", type=int, default=N_GAMES)
    parser.add_argument("--random-seed", action="store_true",
                        help="Use a random seed instead of the fixed default")
    args = parser.parse_args()

    if args.random_seed:
        import random as _random
        args.seed = _random.randint(0, 999_999)

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

    print("Running Model 3: Tactical Policy...")
    tactical_results = MonteCarloSimulator(_tactical_factory).run(
        args.games, seed=args.seed, verbose=True
    )
    run_analysis(tactical_results, "Model 3: Tactical Policy")

    print("Running Model 4: Coalition Policy...")
    coalition_results = MonteCarloSimulator(_coalition_factories()).run(
        args.games, seed=args.seed, verbose=True
    )
    run_analysis(coalition_results, "Model 4: Coalition Policy")

    print("Running Model 5: Coalition Refined Policy...")
    coalition_refined_results = MonteCarloSimulator(_coalition_refined_factories()).run(
        args.games, seed=args.seed, verbose=True
    )
    run_analysis(coalition_refined_results, "Model 5: Coalition Refined Policy")


if __name__ == "__main__":
    main()
