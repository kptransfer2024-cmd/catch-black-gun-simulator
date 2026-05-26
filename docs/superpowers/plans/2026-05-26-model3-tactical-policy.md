# Model 3: Tactical Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `TacticalPolicy` as Model 3 — a policy that extends Model 2 with two improvements: smarter kicker selection (prefer isolated cards as kickers in triple+kicker combos) and danger mode (when any opponent has ≤ 3 cards, override protection logic and shed cards as fast as possible, including using bombs).

**Architecture:** Extend `choose_move` in the base interface to optionally receive opponent hand sizes. Wire the game engine to compute and pass them. Create `TacticalPolicy` in a new `tactical_policy.py` that subclasses `ComboAwarePolicy` and adds: (1) `_lead` override with a smarter sort key that avoids protected kickers, and (2) a `choose_move` override that triggers danger mode when an opponent is close to winning.

**Tech Stack:** Python 3.10+, pytest, existing `dou_dizhu_simulator` package.

---

## Background for implementers

This project simulates a 3-player card game (Dou Dizhu variant). The code lives in `dou_dizhu_simulator/`. There are three existing policies in `agents/`: `RandomPolicy`, `HeuristicPolicy`, `ComboAwarePolicy`. The game engine in `engine/game.py` calls `policy.choose_move(hand, legal_moves, last_combo)` on each turn.

Model 2 (`ComboAwarePolicy`) plays full combos when leading and passes rather than breaking protected hand structures when following. Model 3 adds two behaviours on top:

1. **Smart kicker selection** — when leading with a triple+kicker combo, prefer kickers that are isolated (not part of any protected structure). Currently Model 2 picks the first available kicker by rank, which may waste a card needed for a protected straight.

2. **Danger mode** — when any opponent has ≤ 3 cards remaining, ignore all protection logic and play the move that sheds the maximum number of cards from your hand. This prevents the policy from stubbornly protecting structures while an opponent is about to win.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `dou_dizhu_simulator/agents/base.py` | **Modify** | Add `opponent_hand_sizes` optional param to `choose_move` |
| `dou_dizhu_simulator/engine/game.py` | **Modify** | Compute and pass opponent hand sizes to each policy |
| `dou_dizhu_simulator/agents/random_policy.py` | **Modify** | Accept (and ignore) new param |
| `dou_dizhu_simulator/agents/heuristic_policy.py` | **Modify** | Accept (and ignore) new param |
| `dou_dizhu_simulator/agents/combo_policy.py` | **Modify** | Accept (and ignore) new param |
| `dou_dizhu_simulator/agents/tactical_policy.py` | **Create** | `TacticalPolicy` class + helpers |
| `tests/test_runner.py` | **Modify** | Add test that game passes opponent sizes |
| `tests/test_tactical_policy.py` | **Create** | Unit + integration tests for Model 3 |
| `dou_dizhu_simulator/main.py` | **Modify** | Add Model 3 run |
| `debug_game.py` | **Modify** | Add `--tactical` flag |

---

## Task 1: Extend `choose_move` interface to pass opponent hand sizes

**Files:**
- Modify: `dou_dizhu_simulator/agents/base.py`
- Modify: `dou_dizhu_simulator/engine/game.py:47`
- Modify: `dou_dizhu_simulator/agents/random_policy.py`
- Modify: `dou_dizhu_simulator/agents/heuristic_policy.py`
- Modify: `dou_dizhu_simulator/agents/combo_policy.py`
- Modify: `tests/test_runner.py`

- [ ] **Step 1: Write a failing test**

Append to `tests/test_runner.py`:

```python
def test_game_passes_opponent_hand_sizes():
    from dou_dizhu_simulator.agents.base import PlayerPolicy
    from dou_dizhu_simulator.engine.game import GameRound

    sizes_received = []

    class RecordingPolicy(PlayerPolicy):
        def __init__(self, inner):
            self._inner = inner
        def choose_move(self, hand, legal_moves, last_combo, opponent_hand_sizes=None):
            sizes_received.append(opponent_hand_sizes)
            return self._inner.choose_move(hand, legal_moves, last_combo)

    rng = random.Random(42)
    inner = [RandomPolicy(random.Random(rng.random())) for _ in range(3)]
    recording = [RecordingPolicy(p) for p in inner]
    GameRound(random.Random(42)).play(recording)

    assert sizes_received[0] is not None
    assert len(sizes_received[0]) == 2       # exactly two opponents
    assert sum(sizes_received[0]) == 36      # 18 + 18 at game start
```

- [ ] **Step 2: Run to confirm it fails**

```
python3 -m pytest tests/test_runner.py::test_game_passes_opponent_hand_sizes -v
```
Expected: FAIL — `sizes_received[0]` is `None` because game.py doesn't pass it yet.

- [ ] **Step 3: Update `base.py`**

Replace the full file:

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from ..game.card import Card
from ..game.combination import Combination


class PlayerPolicy(ABC):
    @abstractmethod
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
        opponent_hand_sizes: Optional[List[int]] = None,
    ) -> Optional[Combination]:
        """Return a Combination to play, or None to pass."""
```

- [ ] **Step 4: Update `game.py` line 47**

Replace:
```python
            move = policies[current].choose_move(hand, legal, last_combo)
```
With:
```python
            opp_sizes = [len(hands[(current + 1) % 3]), len(hands[(current + 2) % 3])]
            move = policies[current].choose_move(hand, legal, last_combo, opp_sizes)
```

- [ ] **Step 5: Update `random_policy.py`**

Replace the `choose_move` signature (add the new param, ignore it):

```python
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
        opponent_hand_sizes: Optional[List[int]] = None,
    ) -> Optional[Combination]:
        if not legal_moves:
            return None
        return self._rng.choice(legal_moves)
```

- [ ] **Step 6: Update `heuristic_policy.py`**

Replace the `choose_move` signature:

```python
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
        opponent_hand_sizes: Optional[List[int]] = None,
    ) -> Optional[Combination]:
        if not legal_moves:
            return None

        # Endgame: play the combo that uses the most cards to finish fastest
        if len(hand) <= 5:
            return max(legal_moves, key=lambda c: len(c.cards))

        # Otherwise: play lowest-rank non-bomb (preserve bombs); break ties by fewest cards
        non_bombs = [c for c in legal_moves if c.type not in _BOMB_TYPES]
        candidates = non_bombs if non_bombs else legal_moves
        return min(candidates, key=lambda c: (c.rank_value, len(c.cards)))
```

- [ ] **Step 7: Update `combo_policy.py`**

In `ComboAwarePolicy.choose_move`, replace the signature line only (keep body unchanged):

```python
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
        opponent_hand_sizes: Optional[List[int]] = None,
    ) -> Optional[Combination]:
```

- [ ] **Step 8: Run the new test**

```
python3 -m pytest tests/test_runner.py::test_game_passes_opponent_hand_sizes -v
```
Expected: PASS.

- [ ] **Step 9: Run the full test suite to confirm no regressions**

```
python3 -m pytest -v
```
Expected: all 85 tests PASS (84 existing + 1 new).

- [ ] **Step 10: Commit**

```
git add dou_dizhu_simulator/agents/base.py dou_dizhu_simulator/engine/game.py dou_dizhu_simulator/agents/random_policy.py dou_dizhu_simulator/agents/heuristic_policy.py dou_dizhu_simulator/agents/combo_policy.py tests/test_runner.py
git commit -m "feat: extend choose_move interface to receive opponent hand sizes"
```

---

## Task 2: Create `TacticalPolicy` with smart kicker selection

**Context:** `ComboAwarePolicy._lead` picks the best combo to lead with. For TRIPLE_SINGLE and TRIPLE_PAIR, multiple combos with the same triple exist — differing only in which card is the kicker. Model 2 picks them with identical sort keys, effectively taking the first in list order. Model 3 adds a tiebreaker: prefer kickers that are NOT in any protected structure (not part of a straight ≥5, consec-pair run ≥3, or triple core). The helpers `_kicker_cards` (extracts the non-triple cards from a TRIPLE_SINGLE/PAIR combo) and `_smart_lead_key` (adds the kicker-protection tiebreaker) implement this.

**Files:**
- Create: `dou_dizhu_simulator/agents/tactical_policy.py`
- Create: `tests/test_tactical_policy.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_tactical_policy.py`:

```python
import pytest
from dou_dizhu_simulator.agents.tactical_policy import TacticalPolicy, _kicker_cards, _smart_lead_key
from dou_dizhu_simulator.agents.combo_policy import _get_protected_cards
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import Combination, CombType
from dou_dizhu_simulator.game.rules import get_legal_moves


def card(rank_val: int, suit: str) -> Card:
    return Card(Rank(rank_val), suit)


# ── _kicker_cards ─────────────────────────────────────────────────────────────

def test_kicker_cards_triple_single():
    triple = (card(5,'H'), card(5,'S'), card(5,'C'))
    combo = Combination(CombType.TRIPLE_SINGLE, triple + (card(13,'D'),), 5)
    assert _kicker_cards(combo) == [card(13,'D')]


def test_kicker_cards_triple_pair():
    triple = (card(5,'H'), card(5,'S'), card(5,'C'))
    combo = Combination(CombType.TRIPLE_PAIR, triple + (card(13,'D'), card(13,'H')), 5)
    kickers = _kicker_cards(combo)
    assert len(kickers) == 2
    assert all(int(c.rank) == 13 for c in kickers)


# ── _smart_lead_key ───────────────────────────────────────────────────────────

def test_smart_lead_key_unprotected_kicker_sorts_first():
    triple = (card(9,'H'), card(9,'S'), card(9,'C'))
    protected = {card(7,'H')}
    combo_protected = Combination(CombType.TRIPLE_SINGLE, triple + (card(7,'H'),), 9)
    combo_unprotected = Combination(CombType.TRIPLE_SINGLE, triple + (card(14,'C'),), 9)
    assert _smart_lead_key(combo_unprotected, protected) < _smart_lead_key(combo_protected, protected)


def test_smart_lead_key_straight_still_beats_triple():
    # Straight (cat 0) must always sort before TRIPLE_SINGLE (cat 2)
    protected = set()
    straight = Combination(CombType.STRAIGHT,
        (card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H')), 7)
    triple_single = Combination(CombType.TRIPLE_SINGLE,
        (card(9,'H'), card(9,'S'), card(9,'C'), card(14,'C')), 9)
    assert _smart_lead_key(straight, protected) < _smart_lead_key(triple_single, protected)


def test_smart_lead_key_non_kicker_combo_unchanged():
    # PAIR uses (cat, rank_value, 0, 0) — same ordering as before
    protected = set()
    pair_low = Combination(CombType.PAIR, (card(3,'H'), card(3,'S')), 3)
    pair_high = Combination(CombType.PAIR, (card(9,'H'), card(9,'S')), 9)
    assert _smart_lead_key(pair_low, protected) < _smart_lead_key(pair_high, protected)


# ── TacticalPolicy._lead integration ─────────────────────────────────────────

def test_lead_picks_unprotected_kicker_over_protected():
    # Hand: triple 9s + straight [3-7] (protects 3,4,5,6,7) + isolated A
    # Manually pass only TRIPLE_SINGLE combos to _lead (no straight in legal pool)
    # to isolate the kicker-selection logic.
    hand = [card(9,'H'), card(9,'S'), card(9,'C'),
            card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'),
            card(14,'C')]
    # _get_protected_cards(hand) → {3H,4S,5C,6D,7H} (straight) + {9H,9S,9C} (triple)
    triple = (card(9,'H'), card(9,'S'), card(9,'C'))
    combo_protected_kicker = Combination(CombType.TRIPLE_SINGLE, triple + (card(7,'H'),), 9)
    combo_unprotected_kicker = Combination(CombType.TRIPLE_SINGLE, triple + (card(14,'C'),), 9)

    policy = TacticalPolicy()
    move = policy._lead(hand, [combo_protected_kicker, combo_unprotected_kicker])
    assert move == combo_unprotected_kicker


def test_lead_normal_behavior_inherited():
    # Without any special scenario, TacticalPolicy leads with straight (cat 0 priority)
    hand = ([card(r,'H') for r in [3,4,5,6,7]] +
            [card(9,'H'), card(9,'S'), card(14,'C'), card(3,'S')])
    legal = get_legal_moves(hand, None)
    move = TacticalPolicy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT
```

- [ ] **Step 2: Run to confirm failure**

```
python3 -m pytest tests/test_tactical_policy.py -v
```
Expected: `ImportError: cannot import name 'TacticalPolicy'`

- [ ] **Step 3: Create `tactical_policy.py`**

Create `dou_dizhu_simulator/agents/tactical_policy.py`:

```python
from typing import List, Optional, Set
from .combo_policy import (
    ComboAwarePolicy,
    _BOMB_TYPES,
    _LEAD_CATEGORY,
    _get_protected_cards,
    _maximal_sequences,
)
from ..game.card import Card
from ..game.combination import Combination, CombType

_DANGER_THRESHOLD = 3


def _kicker_cards(combo: Combination) -> List[Card]:
    return [c for c in combo.cards if int(c.rank) != combo.rank_value]


def _smart_lead_key(combo: Combination, protected: Set[Card]) -> tuple:
    cat = _LEAD_CATEGORY.get(combo.type, 4)
    if cat == 0:
        return (0, combo.rank_value, -len(combo.cards), 0)
    if combo.type in (CombType.TRIPLE_SINGLE, CombType.TRIPLE_PAIR):
        kicker_protected = int(any(c in protected for c in _kicker_cards(combo)))
        return (cat, combo.rank_value, kicker_protected, 0)
    return (cat, combo.rank_value, 0, 0)


class TacticalPolicy(ComboAwarePolicy):
    def _lead(self, hand: List[Card], legal_moves: List[Combination]) -> Combination:
        other_candidates = [
            m for m in legal_moves
            if m.type not in _BOMB_TYPES
            and m.type in _LEAD_CATEGORY
            and m.type not in (CombType.STRAIGHT, CombType.CONSECUTIVE_PAIRS)
        ]
        maximal_straights = _maximal_sequences(legal_moves, hand, CombType.STRAIGHT)
        maximal_consec = _maximal_sequences(legal_moves, hand, CombType.CONSECUTIVE_PAIRS)
        candidates = maximal_straights + maximal_consec + other_candidates
        if candidates:
            protected = _get_protected_cards(hand)
            return min(candidates, key=lambda c: _smart_lead_key(c, protected))

        protected = _get_protected_cards(hand)
        isolated = [
            m for m in legal_moves
            if m.type == CombType.SINGLE and m.cards[0] not in protected
        ]
        pool = isolated if isolated else [m for m in legal_moves if m.type == CombType.SINGLE]
        if pool:
            return min(pool, key=lambda c: c.rank_value)
        non_bombs = [m for m in legal_moves if m.type not in _BOMB_TYPES]
        return min(non_bombs or legal_moves, key=lambda c: (c.rank_value, len(c.cards)))
```

- [ ] **Step 4: Run tests**

```
python3 -m pytest tests/test_tactical_policy.py -v
```
Expected: all 7 tests PASS.

- [ ] **Step 5: Run full suite**

```
python3 -m pytest -v
```
Expected: all 92 tests PASS.

- [ ] **Step 6: Commit**

```
git add dou_dizhu_simulator/agents/tactical_policy.py tests/test_tactical_policy.py
git commit -m "feat: add TacticalPolicy with smart kicker selection"
```

---

## Task 3: Add danger mode to `TacticalPolicy`

**Context:** When any opponent has ≤ 3 cards, the current player should stop protecting structures and shed cards as fast as possible. This is implemented by overriding `choose_move`: if `min(opponent_hand_sizes) <= _DANGER_THRESHOLD`, bypass all protection/follow logic and return `max(legal_moves, key=len)` — the legal move that discards the most cards. This also enables bombs in danger mode (since `legal_moves` includes them and `max(key=len)` might pick a bomb if it's the largest legal play).

**Files:**
- Modify: `dou_dizhu_simulator/agents/tactical_policy.py`
- Modify: `tests/test_tactical_policy.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_tactical_policy.py`:

```python
# ── Danger mode ───────────────────────────────────────────────────────────────

def test_danger_mode_overrides_protection_when_following():
    # Consec pairs [77,88,99] are all protected; following PAIR[6H,6S]
    # Without danger mode → PASS (all beatable pairs are protected)
    # With danger mode (opponent has 2 cards) → plays a pair
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)

    move_safe = TacticalPolicy().choose_move(hand, legal, last, [15, 15])
    assert move_safe is None  # no danger: protect consec-pair run

    move_danger = TacticalPolicy().choose_move(hand, legal, last, [2, 15])
    assert move_danger is not None
    assert move_danger.type == CombType.PAIR


def test_danger_mode_uses_bomb_when_following():
    # Only a JOKER_BOMB can beat opponent's BOMB; normally policy saves bombs
    # In danger mode: plays the joker bomb (2 cards, the only legal move)
    from dou_dizhu_simulator.game.card import Card, Rank
    sj = Card(Rank.SMALL_JOKER, 'J')
    bj = Card(Rank.BIG_JOKER, 'J')
    last = Combination(CombType.BOMB,
        (card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D')), 9)
    hand = [sj, bj, card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    legal = get_legal_moves(hand, last)

    assert TacticalPolicy().choose_move(hand, legal, last, [15, 15]) is None   # saves bomb
    move = TacticalPolicy().choose_move(hand, legal, last, [2, 15])
    assert move is not None
    assert move.type == CombType.JOKER_BOMB


def test_danger_mode_leads_with_bomb():
    # Free lead; hand has a bomb + isolated singles; normally never leads with bomb
    # In danger mode: max(key=len) picks the 4-card bomb over 1-card singles
    hand = [card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D'),
            card(3,'H'), card(5,'C'), card(7,'D')]
    legal = get_legal_moves(hand, None)

    move_safe = TacticalPolicy().choose_move(hand, legal, None, [15, 15])
    assert move_safe.type != CombType.BOMB  # normal: never leads with bomb

    move_danger = TacticalPolicy().choose_move(hand, legal, None, [3, 15])
    assert move_danger.type == CombType.BOMB


def test_danger_mode_inactive_without_sizes():
    # When opponent_hand_sizes is None (not provided), no danger mode
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)
    assert TacticalPolicy().choose_move(hand, legal, last) is None  # behaves like ComboAwarePolicy


def test_danger_threshold_is_exclusive():
    # Opponent with exactly 4 cards does NOT trigger danger mode
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)
    assert TacticalPolicy().choose_move(hand, legal, last, [4, 15]) is None  # 4 > threshold
    assert TacticalPolicy().choose_move(hand, legal, last, [3, 15]) is not None  # 3 == threshold
```

- [ ] **Step 2: Run to confirm failure**

```
python3 -m pytest tests/test_tactical_policy.py -k "danger" -v
```
Expected: all 5 danger tests FAIL — `TacticalPolicy` has no `choose_move` override yet so it behaves exactly like `ComboAwarePolicy` (no danger mode).

- [ ] **Step 3: Add `choose_move` override to `TacticalPolicy`**

In `dou_dizhu_simulator/agents/tactical_policy.py`, add the `choose_move` method to the `TacticalPolicy` class (insert before `_lead`):

```python
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
        opponent_hand_sizes: Optional[List[int]] = None,
    ) -> Optional[Combination]:
        if not legal_moves:
            return None
        in_danger = (
            opponent_hand_sizes is not None
            and min(opponent_hand_sizes) <= _DANGER_THRESHOLD
        )
        if in_danger or len(hand) <= 5:
            return max(legal_moves, key=lambda c: len(c.cards))
        if last_combo is None:
            return self._lead(hand, legal_moves)
        return self._follow(hand, legal_moves, last_combo)
```

The full `tactical_policy.py` after this addition:

```python
from typing import List, Optional, Set
from .combo_policy import (
    ComboAwarePolicy,
    _BOMB_TYPES,
    _LEAD_CATEGORY,
    _get_protected_cards,
    _maximal_sequences,
)
from ..game.card import Card
from ..game.combination import Combination, CombType

_DANGER_THRESHOLD = 3


def _kicker_cards(combo: Combination) -> List[Card]:
    return [c for c in combo.cards if int(c.rank) != combo.rank_value]


def _smart_lead_key(combo: Combination, protected: Set[Card]) -> tuple:
    cat = _LEAD_CATEGORY.get(combo.type, 4)
    if cat == 0:
        return (0, combo.rank_value, -len(combo.cards), 0)
    if combo.type in (CombType.TRIPLE_SINGLE, CombType.TRIPLE_PAIR):
        kicker_protected = int(any(c in protected for c in _kicker_cards(combo)))
        return (cat, combo.rank_value, kicker_protected, 0)
    return (cat, combo.rank_value, 0, 0)


class TacticalPolicy(ComboAwarePolicy):
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
        opponent_hand_sizes: Optional[List[int]] = None,
    ) -> Optional[Combination]:
        if not legal_moves:
            return None
        in_danger = (
            opponent_hand_sizes is not None
            and min(opponent_hand_sizes) <= _DANGER_THRESHOLD
        )
        if in_danger or len(hand) <= 5:
            return max(legal_moves, key=lambda c: len(c.cards))
        if last_combo is None:
            return self._lead(hand, legal_moves)
        return self._follow(hand, legal_moves, last_combo)

    def _lead(self, hand: List[Card], legal_moves: List[Combination]) -> Combination:
        other_candidates = [
            m for m in legal_moves
            if m.type not in _BOMB_TYPES
            and m.type in _LEAD_CATEGORY
            and m.type not in (CombType.STRAIGHT, CombType.CONSECUTIVE_PAIRS)
        ]
        maximal_straights = _maximal_sequences(legal_moves, hand, CombType.STRAIGHT)
        maximal_consec = _maximal_sequences(legal_moves, hand, CombType.CONSECUTIVE_PAIRS)
        candidates = maximal_straights + maximal_consec + other_candidates
        if candidates:
            protected = _get_protected_cards(hand)
            return min(candidates, key=lambda c: _smart_lead_key(c, protected))

        protected = _get_protected_cards(hand)
        isolated = [
            m for m in legal_moves
            if m.type == CombType.SINGLE and m.cards[0] not in protected
        ]
        pool = isolated if isolated else [m for m in legal_moves if m.type == CombType.SINGLE]
        if pool:
            return min(pool, key=lambda c: c.rank_value)
        non_bombs = [m for m in legal_moves if m.type not in _BOMB_TYPES]
        return min(non_bombs or legal_moves, key=lambda c: (c.rank_value, len(c.cards)))
```

- [ ] **Step 4: Run all tests**

```
python3 -m pytest tests/test_tactical_policy.py -v
```
Expected: all 12 tests PASS.

- [ ] **Step 5: Run full suite**

```
python3 -m pytest -v
```
Expected: all 97 tests PASS.

- [ ] **Step 6: Commit**

```
git add dou_dizhu_simulator/agents/tactical_policy.py tests/test_tactical_policy.py
git commit -m "feat: add danger mode to TacticalPolicy — override protection when opponent is close to winning"
```

---

## Task 4: Wire Model 3 into `main.py` and `debug_game.py`

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
from .agents.tactical_policy import TacticalPolicy
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


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test main.py with 100 games**

```
python3 -m dou_dizhu_simulator.main --games 100
```
Expected: all four models run, print win rates, no errors.

- [ ] **Step 3: Update `debug_game.py`**

Add import after the existing combo import:
```python
from dou_dizhu_simulator.agents.tactical_policy import TacticalPolicy
```

Replace `make_policies`:
```python
def make_policies(policy_type: str, rng: random.Random):
    if policy_type == "heuristic":
        return [HeuristicPolicy() for _ in range(3)]
    if policy_type == "combo":
        return [ComboAwarePolicy() for _ in range(3)]
    if policy_type == "tactical":
        return [TacticalPolicy() for _ in range(3)]
    return [RandomPolicy(random.Random(rng.random())) for _ in range(3)]
```

In `mini_sim`, replace the factory block:
```python
    if policy_type == "heuristic":
        factory = lambda _rng: HeuristicPolicy()
    elif policy_type == "combo":
        factory = lambda _rng: ComboAwarePolicy()
    elif policy_type == "tactical":
        factory = lambda _rng: TacticalPolicy()
    else:
        factory = lambda rng: RandomPolicy(rng)
```

In `main()`, replace the policy_type assignment:
```python
    if args.tactical:
        policy_type = "tactical"
    elif args.combo:
        policy_type = "combo"
    elif args.heuristic:
        policy_type = "heuristic"
    else:
        policy_type = "random"
```

Add the `--tactical` argument (after `--combo`):
```python
    parser.add_argument("--tactical", action="store_true",
                        help="Use tactical policy (Model 3)")
```

Replace the QUICK COMPARISON loop:
```python
        for ptype in ("random", "heuristic", "combo", "tactical"):
            if ptype == "heuristic":
                factory = lambda _r: HeuristicPolicy()
            elif ptype == "combo":
                factory = lambda _r: ComboAwarePolicy()
            elif ptype == "tactical":
                factory = lambda _r: TacticalPolicy()
            else:
                factory = lambda r: RandomPolicy(r)
            results = MonteCarloSimulator(factory).run(args.mini, seed=seed)
            bg = results.wins[0]
            print(f"  {ptype:>10}: black gun {bg}/{args.mini}  ({results.win_rates[0]:.3f})")
```

- [ ] **Step 4: Test debug_game.py with tactical policy**

```
python3 debug_game.py --tactical --games 2 --seed 42
```
Expected: two traced games using TacticalPolicy — games should end faster than `--combo` when an opponent gets low on cards, with fewer passes in the late game.

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/main.py debug_game.py
git commit -m "feat: wire TacticalPolicy as Model 3 in main and debug_game"
```
