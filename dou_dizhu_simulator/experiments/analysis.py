from typing import Tuple
from math import sqrt
from scipy.stats import binomtest
from .runner import SimResults


def wilson_ci(wins: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """95% Wilson score confidence interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def run_analysis(results: SimResults, label: str, null_p: float = 1 / 3) -> None:
    n = results.n_games
    bg_wins = results.wins[0]
    bg_rate = results.win_rates[0]
    lo, hi = wilson_ci(bg_wins, n)
    btest = binomtest(bg_wins, n, null_p, alternative='two-sided')
    p_value = btest.pvalue
    sig = "SIGNIFICANT" if p_value < 0.05 else "not significant"

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Games played:        {n:,}")
    print(f"  Black gun wins:      {bg_wins:,}  ({bg_rate:.4f})")
    print(f"  95% CI:              [{lo:.4f}, {hi:.4f}]")
    print(f"  Null (p=1/3):        {null_p:.4f}")
    print(f"  Binomial p-value:    {p_value:.6f}  ({sig})")
    print(f"  Avg turns/game:      {results.avg_turns:.1f}")
    print()
    for i, (w, r) in enumerate(zip(results.wins, results.win_rates)):
        label_str = "black gun" if i == 0 else f"player {i}"
        print(f"  Player {i} ({label_str}): {w:,} wins  ({r:.4f})")
    print()
