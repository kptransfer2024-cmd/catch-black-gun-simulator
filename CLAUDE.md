# Catch-the-Black-Gun Card Game Simulator: Black Gun Win Rate Study

## Research Question & Goal

**Primary Question:** Does the "black gun" player (the one holding the Ace of Spades) win at the same rate as the other two players (i.e., 1/3 ≈ 33.3%), or is there a **statistically significant difference** in win probability when all players follow **identical rational strategies**?

**Setup:** All 54 cards are dealt equally — 18 cards each to three players. The player who receives the Ace of Spades is designated the "black gun" player. The Ace of Spades has no special gameplay power; it simply labels one player. The question is whether holding it coincidentally correlates with a different win rate.

**What We're Measuring:** Not hand strength numerically, but **actual win rates under realistic gameplay dynamics** where combinations, sequences, control, and flexibility matter.

**Why This Question Matters:** Whether the Ace of Spades creates a structural bias (through hand composition effects or purely by chance labeling) is non-obvious. Monte Carlo simulation under identical policies is the correct methodology to isolate any such effect.

---

## Experimental Design & Methodology

### Core Assumptions (Non-Negotiable)

1. **Three Identical Players**
   - All players use the **exact same decision-making policy**
   - No skill differences, psychology, or learning
   - Any win-rate difference comes purely from card distribution
   - This experimental design isolates the structural effect

2. **Deterministic & Reproducible**
   - Policies must be fully deterministic (given the same hand state, always output the same decision)
   - No randomness in decision-making (only in initial deck shuffle)
   - Same random seed → same game sequence
   - This ensures statistical validity

3. **Game Rules**
   - Standard Dou Dizhu / Catch-the-Black-Gun three-player variant
   - **Card distribution:** 54 cards dealt as 18+18+18; player who receives Ace of Spades is the "black gun"
   - **First player:** whoever holds the 3 of Hearts goes first (standard Dou Dizhu rule)
   - Valid combinations: single, pair, triple, triple+single, triple+pair, bomb (4-of-a-kind), straight (min 5 cards, no 2s/jokers), consecutive pairs (min 3 pairs, no 2s/jokers), joker bomb
   - Standard beat logic: joker bomb > bomb > non-bomb; same type + same length requires higher rank
   - Two consecutive passes reset the trick (last player to play leads freely)
   - Game ends when one player empties their hand

### Experimental Models

We will implement and compare **at least two models**:

#### Model 0: Random Policy Baseline
**Purpose:** Measure pure structural card-count advantage with zero strategy.

**Rules:**
- If you can legally play, randomly choose from all legal moves (uniform distribution)
- If no legal moves, pass
- No strategic reasoning whatsoever

**Metrics:**
- Win rate of black gun player (Player 0, Ace of Spades holder)
- Win rate of each non-black-gun player
- 95% confidence intervals
- Average turns per game
- Average remaining cards at game end

**Sample size:** 100,000+ games

#### Model 1: Deterministic Heuristic Policy (Preferred)
**Purpose:** Estimate advantage under reasonable rational play.

**Decision Logic (Priority Order):**
1. **Finishing moves first** — if hand ≤ 5 cards, prioritize combos that empty the hand quickly
2. **Smallest valid move** — play the lowest-rank legal combination (preserves flexibility)
3. **Pass if no legal moves**

**Why This Policy:**
- Deterministic and reproducible
- Simple enough to be clearly interpretable
- Captures reasonable strategic intuition (finish when ahead, preserve options)
- All three players use identical logic

**Metrics:** Same as Model 0

**Sample size:** 100,000+ games

### Statistical Rigor

1. **Sample Size:** 100,000+ games per experiment (sufficiently large for stable estimates)

2. **Confidence Intervals:** 95% Wilson score intervals for all win rates

3. **Hypothesis Test:** Null hypothesis = black gun player wins at 33.3% (no structural effect)
   - Binomial test for black gun player's wins
   - Report p-value and effect size

4. **Reproducibility:** 
   - Fixed random seed for all experiments
   - All results should be exactly reproducible

5. **Sensitivity Analysis:** (Optional but recommended)
   - Vary heuristic aggressiveness (bomb-play threshold)
   - Check if advantage is robust across strategic assumptions

---

## Why This Design is Credible

### What Simulation Captures That Math Cannot

- **Combinatorial dependencies:** One extra card enables longer straights, more consecutive pairs, more bombs—nonlinear effects
- **Sequencing dynamics:** The order in which cards appear matters; control over turns matters
- **Flexibility under constraints:** A hand with 18 flexible cards is not proportionally stronger than 17 rigid cards
- **Endgame efficiency:** Fewer dead cards when you need to close out a game

### What We're Explicitly NOT Doing (And Why)

❌ **No:** Comparing average card values numerically
- ❌ **Reason:** This ignores combinations, which are the game's actual mechanic

❌ **No:** Using RL agents that might develop asymmetric strategies
- ❌ **Reason:** We want to isolate structural advantage, not conflate it with emergent skill differences

❌ **No:** Claiming perfect rule reproduction
- ✅ **Why instead:** We prioritize credible logic over pixel-perfect rule implementation
- ✅ **What matters:** The simulator captures the combinatorial and sequential nature of the game

❌ **No:** Running only 10K games
- ❌ **Reason:** Insufficient sample for confidence; win rate estimates would be noisy

---

## Implementation Architecture

### Core Modules

**Card & Deck (`game/card.py`)**
- `Rank` IntEnum: 3–15 (Two), 16 (Small Joker), 17 (Big Joker)
- `Card` frozen dataclass: rank + suit
- `make_deck()`: returns 54-card list
- Constants: `ACE_OF_SPADES`, `THREE_OF_HEARTS`

**Combinations (`game/combination.py`)**
- `CombType` enum: SINGLE, PAIR, TRIPLE, TRIPLE_SINGLE, TRIPLE_PAIR, BOMB, STRAIGHT, CONSECUTIVE_PAIRS, JOKER_BOMB
- `Combination` frozen dataclass: type, cards (tuple), rank_value
- `get_all_combinations(hand_cards)`: enumerate all valid combos from a hand

**Legal Move Generation (`game/rules.py`)**
- `beats(combo, last_combo)`: beat comparison logic
- `get_legal_moves(hand_cards, last_combo)`: returns list of valid Combinations (empty = must pass)

**Player Policies (`agents/`)**
- `PlayerPolicy` (abstract): interface for decision-making
- `RandomPolicy`: random selection from legal moves
- `HeuristicPolicy`: deterministic heuristic (smallest move, then finishing logic)

**Game Execution (`engine/game.py`)**
- `GameRound`: manages one full game
  - Initializes 3 hands with specified distribution
  - Executes turn-by-turn gameplay
  - Detects winner (first to empty hand)
  - Tracks metrics (turns, remaining cards)

**Experiment Runner (`experiments/runner.py`)**
- `MonteCarloSimulator`: runs N games with given policies
- Collects aggregate statistics: win counts, win rates, remaining cards, turn counts

**Statistical Analysis (`experiments/analysis.py`)**
- Confidence interval calculation (Wilson score)
- Binomial significance tests
- Pretty-print results with CI, p-values, effect sizes

**Main Entry Point (`main.py`)**
- `run_baseline_experiment()` — Random policy, 100K games
- `run_heuristic_experiment()` — Heuristic policy, 100K games
- Summary comparison and reporting

### Design Principles

1. **Modularity:** Each component has one clear responsibility
   - Game state and move validation are separate from gameplay logic
   - Policies are pluggable; easy to add new ones
   - Experiments are independent; easy to run variants

2. **Testability:** 
   - Unit tests for card/hand mechanics, move validation, legal moves
   - Integration tests for full game execution
   - Reproducibility: same seed = same game sequence

3. **Clarity Over Cleverness:**
   - Explicit state transitions (turn by turn)
   - Deterministic policies (no hidden randomness)
   - Clear logging and metrics

---

## Success Criteria

A successful implementation will:

1. ✅ **Correctly implement game logic**
   - Legal moves are generated correctly
   - Beat logic is correct (bomb > non-bomb, etc.)
   - Game terminates when a player wins
   - All cards accounted for

2. ✅ **Support identical player policies**
   - RandomPolicy works (random from legal moves)
   - HeuristicPolicy works (deterministic, same for all players)
   - Policies are pluggable

3. ✅ **Run Monte Carlo simulations at scale**
   - 100K+ games in reasonable time (~seconds to ~minute)
   - Reproducible results with fixed seed
   - Accurate win-rate estimation (narrow CI)

4. ✅ **Report credible statistics**
   - Win rates for each player
   - 95% confidence intervals
   - Hypothesis test result (is 18-card advantage significant?)
   - Interpretable summary

5. ✅ **Be modular and extensible**
   - Easy to add new policies
   - Easy to run variants (different card distributions, sensitivity analysis)
   - Easy to refine heuristics without rewriting core engine

---

## Deliverables

### Minimum Viable Result

1. **Core simulator** that executes games with Random + Heuristic policies
2. **100K+ games** per experiment with fixed seed
3. **Summary statistics:** win rates, CI, sample size
4. **Clear conclusion:** "Black gun player has [X]% win rate (95% CI: [Y, Z]); p = W; this is [significant/not significant]"

### Ideal Result

1. All above, plus
2. **Sensitivity analysis:** aggressiveness parameter varied (0.3, 0.5, 0.7) to show robustness
3. **Gameplay visualization:** optional metrics (bomb frequency, average hand duration, etc.)
4. **Well-documented code:** clear comments on non-obvious logic only

---

## Important Notes for Claude Code

### Game Rules Scope
- You don't need to implement every local variant or house rule
- You **do** need to implement the core combinatorial logic correctly:
  - Singles, pairs, triples, triple+single, triple+pair, bombs, straights (min 5), consecutive pairs (min 3 pairs), joker bomb
  - Standard beat logic: joker bomb > bomb > same-type-same-length-higher-rank
  - First player = holder of 3 of Hearts
- If ambiguity arises, choose the most common Dou Dizhu rule and move on

### Libraries
- `scipy`, `numpy` are allowed and encouraged for statistical analysis and performance

### Policy Design
- **Policies must be deterministic.** Given the same hand state and game state, they must always return the same move.
- **Both policies must be identical across all three players.** The 18-card advantage is the only variable.
- The heuristic policy should be simple and interpretable. Avoid over-engineering.

### Statistical Rigor
- Use at least 100K games per experiment
- Always report 95% confidence intervals
- Use binomial tests for hypothesis testing
- Ensure reproducibility with fixed seeds

### Code Quality
- Prefer smaller, focused modules over monolithic files
- Write tests for game mechanics (move validation, legal moves, state transitions)
- No comments required except on non-obvious logic
- Frequent, small commits

---

## Reference: Expected Reasonable Results

These are hypothetical estimates for intuition only—not targets:

- **Random Policy:** Black gun player might win ~33% (no structural bias expected since all get 18 cards)
- **Heuristic Policy:** Black gun player might win ~33% similarly
- If win rate is significantly ≠ 33.3%, the Ace of Spades creates some structural bias
- Most likely result: no significant difference (null hypothesis holds)

These are just ballpark estimates. The actual simulation will tell us the truth.

---

## Questions This Experiment Will Answer

1. **Does the black gun player win at 1/3?** (p-value vs null hypothesis)
2. **If not, how large is the deviation?** (effect size)
3. **Is the result robust?** (does it hold across Random and Heuristic policies?)
4. **Conclusion:** "Holding the Ace of Spades [does / does not] create a statistically significant difference in win rate."

---

## Getting Started

1. Follow the implementation plan in `docs/superpowers/plans/[date]-dou-dizhu-simulator.md`
2. Start with Task 1 (Card/Hand/Deck representation)
3. Build toward Task 12 (integration test)
4. Run the main entry point: `python -m dou_dizhu_simulator.main`
5. Report results with confidence intervals and statistical significance

Good luck! This is a well-posed experimental question with clear methodology.
