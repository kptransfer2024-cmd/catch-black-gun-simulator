# Model 2: Combo-Aware Heuristic Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `ComboAwarePolicy` as Model 2 — a deterministic policy that protects valuable hand structures (straights ≥5, consecutive pairs, triple cores, high standalone pairs) by preferring full combos when leading and passing rather than breaking protected cards when following.

**Architecture:** A new `combo_policy.py` contains `_get_protected_cards()` (identifies cards that belong to worth-keeping structures), `_lead_sort_key()` (category priority: straight/consec-pairs longest-first > triple+pair > triple+single > triple > pair > single), and `ComboAwarePolicy` (same `PlayerPolicy` interface). Wired into `main.py` as Model 2 and into `debug_game.py` via `--combo` flag.

**Tech Stack:** Python 3.10+, pytest, existing `dou_dizhu_simulator` package.

---

## Design Reference

### Protected Structures
A card is **protected** if removing it destroys any of:
- A triple core (3+ cards of the same rank)
- A straight of length ≥ 5
- A consecutive pair run of length ≥ 3 pairs
- A high standalone pair (rank ≥ K=13) when the current trick is a weak pair (rank ≤ 7)

### Leading Freely (hand > 5 cards)
Priority order for `min(candidates, key=_lead_sort_key)`:

| Category | Types | Sort within category |
|----------|-------|----------------------|
| 0 | STRAIGHT, CONSECUTIVE_PAIRS | longest first (`-len`), then lowest rank |
| 1 | TRIPLE_PAIR | lowest triple rank |
| 2 | TRIPLE_SINGLE | lowest triple rank |
| 3 | TRIPLE | lowest rank |
| 4 | PAIR | lowest rank |
| — | SINGLE (fallback) | isolated (unprotected) first, then lowest rank |
| — | BOMB/JOKER_BOMB | never led voluntarily |

### Following a Trick (hand > 5 cards)
1. Collect non-bomb legal responses.
2. If none → PASS (preserve bombs).
3. Among non-bomb responses, filter out those that use any protected card → `unprotected`.
4. If `unprotected` is non-empty → play `min(unprotected, key=(rank_value, len))`.
5. If ALL non-bomb responses touch a protected card → PASS.

### Endgame (hand ≤ 5 cards)
Same as Model 1: `max(legal_moves, key=lambda c: len(c.cards))`.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `dou_dizhu_simulator/agents/combo_policy.py` | **Create** | `_get_protected_cards`, `_lead_sort_key`, `ComboAwarePolicy` |
| `tests/test_combo_policy.py` | **Create** | Unit tests for all policy behaviors |
| `dou_dizhu_simulator/main.py` | **Modify** | Add Model 2 run |
| `debug_game.py` | **Modify** | Add `--combo` flag |

---

## Task 1: `_get_protected_cards` helper

**Files:**
- Create: `dou_dizhu_simulator/agents/combo_policy.py`
- Create: `tests/test_combo_policy.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_combo_policy.py`:

```python
import pytest
from dou_dizhu_simulator.agents.combo_policy import _get_protected_cards
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import Combination, CombType


def card(rank_val: int, suit: str) -> Card:
    return Card(Rank(rank_val), suit)


# ── triple / bomb ──────────────────────────────────────────────────────────

def test_triple_core_protected():
    hand = [card(7,'H'), card(7,'S'), card(7,'C'), card(12,'D')]
    p = _get_protected_cards(hand)
    assert card(7,'H') in p
    assert card(7,'S') in p
    assert card(7,'C') in p
    assert card(12,'D') not in p


def test_bomb_all_four_protected():
    hand = [card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D'), card(3,'H')]
    p = _get_protected_cards(hand)
    assert all(card(9, s) in p for s in ('H','S','C','D'))
    assert card(3,'H') not in p


# ── straight ───────────────────────────────────────────────────────────────

def test_straight_exactly_5_protected():
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S')]
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


def test_straight_4_not_protected():
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    p = _get_protected_cards(hand)
    assert len(p) == 0


def test_straight_7_protected():
    hand = [card(r,'H') for r in range(3, 10)]  # 3–9
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


def test_two_separate_straights_both_protected():
    # [3-7] and [9-K]: gap at 8
    hand = [card(r,'H') for r in [3,4,5,6,7,9,10,11,12,13]]
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


# ── consecutive pairs ─────────────────────────────────────────────────────

def test_consec_pairs_3_protected():
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D')]
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


def test_consec_pairs_2_not_protected():
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'), card(9,'H')]
    p = _get_protected_cards(hand)
    assert len(p) == 0


def test_consec_pairs_standalone_pair_not_protected():
    # [33, 44, 55] run + standalone [KK]; KK should not be protected
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D'), card(13,'H'), card(13,'S')]
    p = _get_protected_cards(hand)
    assert card(3,'H') in p
    assert card(13,'H') not in p
    assert card(13,'S') not in p


# ── high standalone pair soft-protection ──────────────────────────────────

def test_high_pair_protected_against_weak_trick():
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]  # KK + 3
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    p = _get_protected_cards(hand, last)
    assert card(13,'H') in p
    assert card(13,'S') in p
    assert card(3,'D') not in p


def test_high_pair_not_protected_against_strong_trick():
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]  # KK + 3
    last = Combination(CombType.PAIR, (card(8,'H'), card(8,'S')), 8)
    p = _get_protected_cards(hand, last)
    assert len(p) == 0


def test_ace_pair_protected_against_weak_trick():
    hand = [card(14,'H'), card(14,'S')]  # AA
    last = Combination(CombType.PAIR, (card(7,'H'), card(7,'S')), 7)
    p = _get_protected_cards(hand, last)
    assert card(14,'H') in p
    assert card(14,'S') in p


def test_two_protected_against_weak_trick():
    hand = [card(15,'H'), card(15,'S')]  # 22
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    p = _get_protected_cards(hand, last)
    assert card(15,'H') in p
    assert card(15,'S') in p


def test_high_pair_protection_only_for_pair_trick():
    # Soft protection only triggers when following a PAIR trick
    hand = [card(13,'H'), card(13,'S')]
    last = Combination(CombType.SINGLE, (card(5,'H'),), 5)
    p = _get_protected_cards(hand, last)
    assert len(p) == 0  # SINGLE trick, no soft protection
```

- [ ] **Step 2: Run to confirm failure**

```
pytest tests/test_combo_policy.py -v
```
Expected: `ImportError: cannot import name '_get_protected_cards'`

- [ ] **Step 3: Implement `_get_protected_cards` in `combo_policy.py`**

Create `dou_dizhu_simulator/agents/combo_policy.py`:

```python
from collections import defaultdict
from typing import List, Optional, Set
from .base import PlayerPolicy
from ..game.card import Card, Rank
from ..game.combination import Combination, CombType

_BOMB_TYPES = (CombType.BOMB, CombType.JOKER_BOMB)
_HIGH_PAIR_RANK = 13   # K=13, A=14, 2=15 all get soft protection
_WEAK_TRICK_RANK = 7   # opponent pair rank ≤ 7 triggers soft protection

_LEAD_CATEGORY = {
    CombType.STRAIGHT: 0,
    CombType.CONSECUTIVE_PAIRS: 0,
    CombType.TRIPLE_PAIR: 1,
    CombType.TRIPLE_SINGLE: 2,
    CombType.TRIPLE: 3,
    CombType.PAIR: 4,
}


def _get_protected_cards(
    hand: List[Card], last_combo: Optional[Combination] = None
) -> Set[Card]:
    protected: Set[Card] = set()
    groups: dict = defaultdict(list)
    for card in hand:
        groups[card.rank].append(card)

    # Protect triple cores and bombs (3+ of same rank)
    for rank, cards in groups.items():
        if len(cards) >= 3:
            protected.update(cards)

    # Protect straights of length >= 5
    straight_eligible = sorted(r for r in groups if Rank.THREE <= r <= Rank.ACE)
    for i in range(len(straight_eligible)):
        run_len = 1
        for j in range(i + 1, len(straight_eligible)):
            if int(straight_eligible[j]) == int(straight_eligible[j - 1]) + 1:
                run_len += 1
            else:
                break
        if run_len >= 5:
            for k in range(i, i + run_len):
                protected.add(groups[straight_eligible[k]][0])

    # Protect consecutive pair runs of length >= 3 pairs
    pair_eligible = sorted(
        r for r in groups
        if len(groups[r]) >= 2 and Rank.THREE <= r <= Rank.ACE
    )
    for i in range(len(pair_eligible)):
        run_len = 1
        for j in range(i + 1, len(pair_eligible)):
            if int(pair_eligible[j]) == int(pair_eligible[j - 1]) + 1:
                run_len += 1
            else:
                break
        if run_len >= 3:
            for k in range(i, i + run_len):
                protected.update(groups[pair_eligible[k]][:2])

    # Soft-protect high standalone pairs (rank >= K) when following a weak pair trick
    if (
        last_combo is not None
        and last_combo.type == CombType.PAIR
        and last_combo.rank_value <= _WEAK_TRICK_RANK
    ):
        for rank, cards in groups.items():
            if len(cards) == 2 and int(rank) >= _HIGH_PAIR_RANK:
                protected.update(cards)

    return protected
```

- [ ] **Step 4: Run to confirm all tests pass**

```
pytest tests/test_combo_policy.py -v
```
Expected: 14 tests PASS

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/agents/combo_policy.py tests/test_combo_policy.py
git commit -m "feat: add _get_protected_cards helper for combo-aware policy"
```

---

## Task 2: Full `ComboAwarePolicy` class

**Files:**
- Modify: `dou_dizhu_simulator/agents/combo_policy.py`
- Modify: `tests/test_combo_policy.py`

- [ ] **Step 1: Write failing tests for lead, follow, and endgame**

Append to `tests/test_combo_policy.py`:

```python
from dou_dizhu_simulator.agents.combo_policy import ComboAwarePolicy
from dou_dizhu_simulator.game.rules import get_legal_moves


def policy() -> ComboAwarePolicy:
    return ComboAwarePolicy()


# ── LEADING FREELY ────────────────────────────────────────────────────────

def test_lead_straight_preferred_over_pair():
    # straight [34567] + standalone pair [99] + filler → must lead straight
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S'),
            card(9,'H'), card(9,'S'), card(13,'D'), card(14,'C')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT


def test_lead_longest_straight_first():
    # 7-card run [3-9] + extra cards → should play the 7-card straight
    hand = [card(r,'H') for r in range(3, 10)] + [card(14,'S'), card(14,'H')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT
    assert len(move.cards) == 7


def test_lead_lower_rank_straight_first_same_length():
    # Two 5-card straights [3-7] and [9-K] with a gap at 8
    hand = ([card(r,'H') for r in [3,4,5,6,7]] +
            [card(r,'S') for r in [9,10,11,12,13]] +
            [card(14,'C')])
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT
    assert move.rank_value == 7   # top card of [3-7] = 7


def test_lead_triple_pair_over_triple_single():
    # Hand has triple 5s, pair 9s, plus other singles → triple+pair beats triple+single
    hand = [card(5,'H'), card(5,'S'), card(5,'C'),
            card(9,'H'), card(9,'S'),
            card(3,'D'), card(4,'D'), card(7,'D'), card(8,'D'), card(13,'D')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.TRIPLE_PAIR


def test_lead_triple_single_over_plain_triple():
    # Hand has triple 5s and singles but no pair → triple+single preferred over plain triple
    hand = [card(5,'H'), card(5,'S'), card(5,'C'),
            card(3,'D'), card(4,'D'), card(7,'D'), card(8,'D'),
            card(11,'S'), card(13,'H')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.TRIPLE_SINGLE


def test_lead_pair_over_single():
    # No straights/triples; hand has pair [33] + isolated singles → play lowest pair
    hand = [card(3,'H'), card(3,'S'),
            card(7,'C'), card(9,'D'), card(12,'H'), card(14,'S'), card(14,'C'), card(15,'D')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.PAIR
    assert move.rank_value == 3


def test_lead_consecutive_pairs_over_standalone_pair():
    # Consec pairs [33,44,55] + standalone [KK] → lead consec pairs (cat 0 beats cat 4)
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D'), card(13,'H'), card(13,'S'), card(9,'C')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.CONSECUTIVE_PAIRS


def test_lead_isolated_single_before_protected_single():
    # Hand has pair [99] (protected) and isolated [Q] — no multi-card combos available
    # Actually pair [99] IS a multi-card combo and would be played by category priority.
    # To test isolated single preference we need a hand with only singles of different types.
    # Use hand where pair exists but also straight exists to consume them, OR use endgame off path.
    # Simpler: test with hand > 5 where no multi-card combo exists (all different ranks, no pairs).
    # [3,5,7,9,J,K] — all isolated singles, no pairs, no straights.
    hand = [card(3,'H'), card(5,'S'), card(7,'C'), card(9,'D'), card(11,'H'), card(13,'S')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.SINGLE
    assert move.rank_value == 3   # lowest isolated single


# ── FOLLOWING A TRICK ─────────────────────────────────────────────────────

def test_follow_plays_isolated_single_not_straight_card():
    # Hand [3,4,5,6,7,A]; opponent played SINGLE[6H]
    # 7 is in protected straight [34567]; A is isolated → play A
    last = Combination(CombType.SINGLE, (card(6,'H'),), 6)
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S'), card(14,'C')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is not None
    assert move.cards[0] == card(14,'C')


def test_follow_pass_to_protect_straight():
    # Hand [3,4,5,6,7]; opponent played SINGLE[6H]
    # Only 7 can beat it, but 7 is in protected straight → PASS
    last = Combination(CombType.SINGLE, (card(6,'H'),), 6)
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


def test_follow_pass_high_pair_vs_weak_pair():
    # Hand [KH, KS, 3D]; opponent played PAIR[55] (rank 5 ≤ 7)
    # KK is soft-protected → PASS
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


def test_follow_play_high_pair_vs_strong_trick():
    # Hand [KH, KS, 3D]; opponent played PAIR[88] (rank 8 > 7)
    # KK is NOT soft-protected → play it
    last = Combination(CombType.PAIR, (card(8,'H'), card(8,'S')), 8)
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is not None
    assert move.type == CombType.PAIR
    assert move.rank_value == 13


def test_follow_prefers_standalone_pair_over_consec_pair_run():
    # Hand: consec pairs [33,44,55] (all protected) + standalone [KK]
    # Opponent played PAIR[88] (rank 8 > 7, so soft-protection inactive)
    # Consec pair run: 33 (3<8 ✗), 44 (4<8 ✗), 55 (5<8 ✗) — none can beat PAIR[88]
    # KK (rank 13 > 8 ✓), standalone → unprotected → plays KK
    last = Combination(CombType.PAIR, (card(8,'H'), card(8,'S')), 8)
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D'), card(13,'H'), card(13,'S'), card(9,'C')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is not None
    assert move.type == CombType.PAIR
    assert move.rank_value == 13


def test_follow_pass_when_all_pairs_in_consec_run():
    # All beatable pairs are inside consecutive pair run → PASS
    # Hand: consec pairs [77,88,99]; opponent played PAIR[66]
    # 77, 88, 99 all beat it but all are in the consec run → protected → PASS
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


def test_follow_pass_preserves_bombs():
    # Following a BOMB with only JOKER_BOMB available
    # Joker bomb cards are protected (triple-ish — two jokers always go together)
    # Actually jokers don't form a triple, but if we have nothing else → non_bombs is empty → PASS
    from dou_dizhu_simulator.game.card import Card, Rank
    sj = Card(Rank.SMALL_JOKER, 'J')
    bj = Card(Rank.BIG_JOKER, 'J')
    last = Combination(CombType.BOMB, (card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D')), 9)
    hand = [sj, bj, card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    legal = get_legal_moves(hand, last)
    # Only joker bomb can beat a bomb; non_bombs is empty → PASS
    move = policy().choose_move(hand, legal, last)
    assert move is None


# ── ENDGAME ───────────────────────────────────────────────────────────────

def test_endgame_maximises_card_count():
    # Hand <= 5; should play move with most cards regardless of protection
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'), card(5,'H')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    # Consecutive pairs [33,44] is 4 cards; or consec pairs [33,44,55]... wait 5 is only 1 card
    # Pairs available: [33] (2 cards), [44] (2 cards). No 3-pair consecutive run (only 2 consecutive pairs).
    # But we also have combos: pair[33]=2, pair[44]=2, single[5]=1
    # No consecutive pairs (only 2 ranks with pairs, need 3). No triples.
    # Max card move = pair (2 cards); first pair found = pair[33]
    assert len(move.cards) >= 2


def test_endgame_plays_combo_over_single():
    # Hand with 3 cards [3,3,K]; endgame should play pair[33] not single[3]
    hand = [card(3,'H'), card(3,'S'), card(13,'D')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.PAIR
    assert len(move.cards) == 2
```

- [ ] **Step 2: Run to confirm tests fail**

```
pytest tests/test_combo_policy.py -v -k "test_lead or test_follow or test_endgame"
```
Expected: `AttributeError: module has no attribute 'ComboAwarePolicy'`

- [ ] **Step 3: Add `_lead_sort_key` and `ComboAwarePolicy` to `combo_policy.py`**

Append to the existing `combo_policy.py` (after `_get_protected_cards`):

```python
def _lead_sort_key(combo: Combination):
    cat = _LEAD_CATEGORY.get(combo.type, 4)
    if cat == 0:
        return (0, -len(combo.cards), combo.rank_value)
    return (cat, combo.rank_value)


class ComboAwarePolicy(PlayerPolicy):
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
    ) -> Optional[Combination]:
        if not legal_moves:
            return None
        if len(hand) <= 5:
            return max(legal_moves, key=lambda c: len(c.cards))
        if last_combo is None:
            return self._lead(hand, legal_moves)
        return self._follow(hand, legal_moves, last_combo)

    def _lead(self, hand: List[Card], legal_moves: List[Combination]) -> Combination:
        candidates = [
            m for m in legal_moves
            if m.type not in _BOMB_TYPES and m.type in _LEAD_CATEGORY
        ]
        if candidates:
            return min(candidates, key=_lead_sort_key)

        # Fall back to singles: isolated (unprotected) first, then lowest rank
        protected = _get_protected_cards(hand)
        isolated = [
            m for m in legal_moves
            if m.type == CombType.SINGLE and m.cards[0] not in protected
        ]
        pool = isolated if isolated else [m for m in legal_moves if m.type == CombType.SINGLE]
        if pool:
            return min(pool, key=lambda c: c.rank_value)

        # Last resort: minimum non-bomb move (shouldn't normally reach here)
        non_bombs = [m for m in legal_moves if m.type not in _BOMB_TYPES]
        return min(non_bombs or legal_moves, key=lambda c: (c.rank_value, len(c.cards)))

    def _follow(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Combination,
    ) -> Optional[Combination]:
        non_bombs = [m for m in legal_moves if m.type not in _BOMB_TYPES]
        if not non_bombs:
            return None  # save bombs

        protected = _get_protected_cards(hand, last_combo)
        unprotected = [
            m for m in non_bombs
            if not any(card in protected for card in m.cards)
        ]
        if unprotected:
            return min(unprotected, key=lambda c: (c.rank_value, len(c.cards)))

        return None  # all responses would break protected structures
```

- [ ] **Step 4: Run all tests**

```
pytest tests/test_combo_policy.py -v
```
Expected: all tests PASS

- [ ] **Step 5: Run full test suite to check for regressions**

```
pytest -v
```
Expected: all existing tests still PASS

- [ ] **Step 6: Commit**

```
git add dou_dizhu_simulator/agents/combo_policy.py tests/test_combo_policy.py
git commit -m "feat: add ComboAwarePolicy — protects straights/pairs/triples when playing"
```

---

## Task 3: Wire Model 2 into main.py and debug_game.py

**Files:**
- Modify: `dou_dizhu_simulator/main.py`
- Modify: `debug_game.py`

- [ ] **Step 1: Update `main.py`**

Replace the full file:

```python
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
```

- [ ] **Step 2: Smoke-test main.py with 100 games**

```
python3 -m dou_dizhu_simulator.main --games 100
```
Expected: all three models run, print win rates, no errors.

- [ ] **Step 3: Update `debug_game.py`**

Locate the import block at the top (lines 17–21) and the `make_policies` function (lines 23–26). Make the following changes:

Add import after the existing heuristic import:
```python
from dou_dizhu_simulator.agents.combo_policy import ComboAwarePolicy
```

Replace `make_policies`:
```python
def make_policies(policy_type: str, rng: random.Random):
    if policy_type == "heuristic":
        return [HeuristicPolicy() for _ in range(3)]
    if policy_type == "combo":
        return [ComboAwarePolicy() for _ in range(3)]
    return [RandomPolicy(random.Random(rng.random())) for _ in range(3)]
```

In `mini_sim`, replace the factory block:
```python
    if policy_type == "heuristic":
        factory = lambda _rng: HeuristicPolicy()
    elif policy_type == "combo":
        factory = lambda _rng: ComboAwarePolicy()
    else:
        factory = lambda rng: RandomPolicy(rng)
```

In `main()`, replace the policy_type assignment:
```python
    if args.combo:
        policy_type = "combo"
    elif args.heuristic:
        policy_type = "heuristic"
    else:
        policy_type = "random"
```

Add the `--combo` argument to the argparse block (after `--heuristic`):
```python
    parser.add_argument("--combo", action="store_true",
                        help="Use combo-aware policy instead of heuristic")
```

In the QUICK COMPARISON block at the bottom, add combo to the loop:
```python
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
```

- [ ] **Step 4: Test debug_game.py with combo policy**

```
python3 debug_game.py --combo --games 2 --random-seed
```
Expected: two traced games using ComboAwarePolicy — should see pairs and straights played as full combos, significantly fewer 50+ turn single-card grind games compared to `--heuristic`.

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/main.py debug_game.py
git commit -m "feat: wire ComboAwarePolicy as Model 2 in main and debug_game"
```
