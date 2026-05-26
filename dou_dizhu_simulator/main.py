import random
from .agents.random_policy import RandomPolicy
from .agents.heuristic_policy import HeuristicPolicy
from .experiments.runner import MonteCarloSimulator
from .experiments.analysis import run_analysis

N_GAMES = 100_000
SEED = 2026


def _random_factory(rng: random.Random) -> RandomPolicy:
    return RandomPolicy(rng)


def _heuristic_factory(_rng: random.Random) -> HeuristicPolicy:
    return HeuristicPolicy()


def main() -> None:
    print("Catch-the-Black-Gun Monte Carlo Simulator")
    print(f"Running {N_GAMES:,} games per experiment (seed={SEED})\n")

    print("Running Model 0: Random Policy...")
    random_sim = MonteCarloSimulator(_random_factory)
    random_results = random_sim.run(N_GAMES, seed=SEED, verbose=True)
    run_analysis(random_results, "Model 0: Random Policy")

    print("Running Model 1: Heuristic Policy...")
    heuristic_sim = MonteCarloSimulator(_heuristic_factory)
    heuristic_results = heuristic_sim.run(N_GAMES, seed=SEED, verbose=True)
    run_analysis(heuristic_results, "Model 1: Heuristic Policy")


if __name__ == "__main__":
    main()
