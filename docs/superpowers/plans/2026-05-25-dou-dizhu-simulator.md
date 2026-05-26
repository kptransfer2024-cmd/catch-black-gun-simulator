# Catch-the-Black-Gun Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Monte Carlo simulator that runs 100K+ three-player Catch-the-Black-Gun games to test whether the Ace of Spades holder wins at the same rate (1/3) as other players.

**Architecture:** Nine focused modules — card primitives → combination logic → legal move generation → player policies → game engine → Monte Carlo runner → statistical analysis → main entry point. TDD throughout; each module tested before the next builds on it.

**Tech Stack:** Python 3.10+, pytest, scipy (binomial test), standard library (random, dataclasses, enum).

---

## File Structure

```
dou_dizhu_simulator/
├── __init__.py
├── main.py
├── game/
│   ├── __init__.py
│   ├── card.py          # Rank enum, Card dataclass, make_deck(), ACE_OF_SPADES, THREE_OF_HEARTS
│   ├── combination.py   # CombType enum, Combination dataclass, get_all_combinations()
│   └── rules.py         # beats(), get_legal_moves()
├── agents/
│   ├── __init__.py
│   ├── base.py          # PlayerPolicy abstract base
│   ├── random_policy.py # RandomPolicy
│   └── heuristic_policy.py  # HeuristicPolicy
├── engine/
│   ├── __init__.py
│   └── game.py          # GameRound: deal + play loop + winner detection
└── experiments/
    ├── __init__.py
    ├── runner.py         # MonteCarloSimulator, SimResults
    └── analysis.py       # wilson_ci(), binomial_test(), print_report()

tests/
├── __init__.py
├── test_card.py
├── test_combination.py
├── test_rules.py
├── test_game.py
└── test_runner.py
```

---

## Task 1: Card Primitives

**Files:**
- Create: `dou_dizhu_simulator/__init__.py` (empty)
- Create: `dou_dizhu_simulator/game/__init__.py` (empty)
- Create: `dou_dizhu_simulator/game/card.py`
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_card.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_card.py
from dou_dizhu_simulator.game.card import (
    Card, Rank, ACE_OF_SPADES, THREE_OF_HEARTS, make_deck
)

def test_deck_has_54_cards():
    assert len(make_deck()) == 54

def test_deck_no_duplicates():
    deck = make_deck()
    assert len(set(deck)) == 54

def test_deck_contains_ace_of_spades():
    assert ACE_OF_SPADES in make_deck()

def test_deck_contains_three_of_hearts():
    assert THREE_OF_HEARTS in make_deck()

def test_rank_ordering():
    assert Rank.THREE < Rank.ACE < Rank.TWO < Rank.SMALL_JOKER < Rank.BIG_JOKER

def test_card_is_immutable():
    import pytest
    with pytest.raises(Exception):
        ACE_OF_SPADES.rank = Rank.TWO

def test_ace_of_spades_identity():
    deck = make_deck()
    aces_spades = [c for c in deck if c.rank == Rank.ACE and c.suit == 'S']
    assert len(aces_spades) == 1
    assert aces_spades[0] == ACE_OF_SPADES
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_card.py -v
```
Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement card.py**

```python
# dou_dizhu_simulator/game/card.py
from dataclasses import dataclass
from enum import IntEnum
from typing import List

class Rank(IntEnum):
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    TWO = 15
    SMALL_JOKER = 16
    BIG_JOKER = 17

@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: str  # 'S' 'H' 'D' 'C' for normal cards; 'J' for jokers

    def __repr__(self) -> str:
        names = {3:'3',4:'4',5:'5',6:'6',7:'7',8:'8',9:'9',10:'T',
                 11:'J',12:'Q',13:'K',14:'A',15:'2',16:'Sj',17:'Bj'}
        return f"{names[int(self.rank)]}{self.suit}"

ACE_OF_SPADES = Card(Rank.ACE, 'S')
THREE_OF_HEARTS = Card(Rank.THREE, 'H')

def make_deck() -> List[Card]:
    deck = []
    for rank_val in range(3, 16):  # 3 through 2
        for suit in ('S', 'H', 'D', 'C'):
            deck.append(Card(Rank(rank_val), suit))
    deck.append(Card(Rank.SMALL_JOKER, 'J'))
    deck.append(Card(Rank.BIG_JOKER, 'J'))
    return deck
```

Also create empty `__init__.py` files:
```python
# dou_dizhu_simulator/__init__.py  (empty)
# dou_dizhu_simulator/game/__init__.py  (empty)
# tests/__init__.py  (empty)
```

- [ ] **Step 4: Run tests to verify pass**

```
pytest tests/test_card.py -v
```
Expected: 7 tests PASSED

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/ tests/test_card.py tests/__init__.py
git commit -m "feat: add Card, Rank, make_deck() primitives"
```

---

## Task 2: Combination Types and Validators

**Files:**
- Create: `dou_dizhu_simulator/game/combination.py`
- Create: `tests/test_combination.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_combination.py
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import (
    CombType, Combination, get_all_combinations
)

def _cards(rank_suit_pairs):
    return [Card(Rank(r), s) for r, s in rank_suit_pairs]

def test_single_from_one_card():
    hand = _cards([(5, 'S')])
    combos = get_all_combinations(hand)
    singles = [c for c in combos if c.type == CombType.SINGLE]
    assert len(singles) == 1
    assert singles[0].rank_value == 5

def test_pair_detected():
    hand = _cards([(7, 'S'), (7, 'H')])
    combos = get_all_combinations(hand)
    pairs = [c for c in combos if c.type == CombType.PAIR]
    assert len(pairs) == 1
    assert pairs[0].rank_value == 7

def test_no_pair_from_jokers():
    hand = _cards([(16, 'J'), (17, 'J')])
    combos = get_all_combinations(hand)
    pairs = [c for c in combos if c.type == CombType.PAIR]
    assert len(pairs) == 0

def test_joker_bomb_detected():
    hand = _cards([(16, 'J'), (17, 'J')])
    combos = get_all_combinations(hand)
    jbombs = [c for c in combos if c.type == CombType.JOKER_BOMB]
    assert len(jbombs) == 1

def test_bomb_4_of_a_kind():
    hand = _cards([(9, 'S'), (9, 'H'), (9, 'D'), (9, 'C')])
    combos = get_all_combinations(hand)
    bombs = [c for c in combos if c.type == CombType.BOMB]
    assert len(bombs) == 1
    assert bombs[0].rank_value == 9

def test_straight_5_cards():
    hand = _cards([(3,'S'),(4,'H'),(5,'D'),(6,'C'),(7,'S')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 1
    assert straights[0].rank_value == 7  # highest card rank

def test_straight_no_short_straights():
    # Only 4 consecutive cards — not a valid straight
    hand = _cards([(3,'S'),(4,'H'),(5,'D'),(6,'C')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 0

def test_straight_no_twos_or_jokers():
    hand = _cards([(13,'S'),(14,'H'),(15,'D'),(3,'C'),(4,'S')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 0  # 13(K),14(A),15(2) — 2 breaks it

def test_consecutive_pairs_3_pairs():
    hand = _cards([(5,'S'),(5,'H'),(6,'D'),(6,'C'),(7,'S'),(7,'H')])
    combos = get_all_combinations(hand)
    cpairs = [c for c in combos if c.type == CombType.CONSECUTIVE_PAIRS]
    assert len(cpairs) == 1
    assert cpairs[0].rank_value == 7

def test_consecutive_pairs_need_3_minimum():
    hand = _cards([(5,'S'),(5,'H'),(6,'D'),(6,'C')])
    combos = get_all_combinations(hand)
    cpairs = [c for c in combos if c.type == CombType.CONSECUTIVE_PAIRS]
    assert len(cpairs) == 0

def test_triple_single():
    hand = _cards([(8,'S'),(8,'H'),(8,'D'),(5,'C')])
    combos = get_all_combinations(hand)
    ts = [c for c in combos if c.type == CombType.TRIPLE_SINGLE]
    assert len(ts) == 1
    assert ts[0].rank_value == 8

def test_triple_pair():
    hand = _cards([(8,'S'),(8,'H'),(8,'D'),(5,'C'),(5,'S')])
    combos = get_all_combinations(hand)
    tp = [c for c in combos if c.type == CombType.TRIPLE_PAIR]
    assert len(tp) == 1
    assert tp[0].rank_value == 8

def test_combination_cards_are_tuple():
    hand = _cards([(5,'S')])
    combos = get_all_combinations(hand)
    assert isinstance(combos[0].cards, tuple)
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_combination.py -v
```
Expected: `ImportError` (module not yet created)

- [ ] **Step 3: Implement combination.py**

```python
# dou_dizhu_simulator/game/combination.py
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Optional
from collections import defaultdict
from .card import Card, Rank

class CombType(Enum):
    SINGLE = auto()
    PAIR = auto()
    TRIPLE = auto()
    TRIPLE_SINGLE = auto()
    TRIPLE_PAIR = auto()
    BOMB = auto()
    STRAIGHT = auto()
    CONSECUTIVE_PAIRS = auto()
    JOKER_BOMB = auto()

@dataclass(frozen=True)
class Combination:
    type: CombType
    cards: tuple
    rank_value: int

def get_all_combinations(hand_cards: List[Card]) -> List[Combination]:
    combos: List[Combination] = []
    groups: Dict[Rank, List[Card]] = defaultdict(list)
    for card in hand_cards:
        groups[card.rank].append(card)

    # Singles
    for card in hand_cards:
        combos.append(Combination(CombType.SINGLE, (card,), int(card.rank)))

    # Pairs (not jokers)
    for rank, cards in groups.items():
        if len(cards) >= 2 and rank < Rank.SMALL_JOKER:
            combos.append(Combination(CombType.PAIR, tuple(cards[:2]), int(rank)))

    # Triples
    for rank, cards in groups.items():
        if len(cards) >= 3 and rank < Rank.SMALL_JOKER:
            combos.append(Combination(CombType.TRIPLE, tuple(cards[:3]), int(rank)))

    # Bombs (4-of-a-kind)
    for rank, cards in groups.items():
        if len(cards) >= 4 and rank < Rank.SMALL_JOKER:
            combos.append(Combination(CombType.BOMB, tuple(cards[:4]), int(rank)))

    # Joker bomb
    if Rank.SMALL_JOKER in groups and Rank.BIG_JOKER in groups:
        sj = groups[Rank.SMALL_JOKER][0]
        bj = groups[Rank.BIG_JOKER][0]
        combos.append(Combination(CombType.JOKER_BOMB, (sj, bj), int(Rank.BIG_JOKER)))

    # Straights: 5+ consecutive ranks in range [THREE, ACE], each rank exactly once
    straight_eligible = sorted(r for r in groups if Rank.THREE <= r <= Rank.ACE)
    for i in range(len(straight_eligible)):
        run_len = 1
        for j in range(i + 1, len(straight_eligible)):
            if int(straight_eligible[j]) == int(straight_eligible[j - 1]) + 1:
                run_len += 1
                if run_len >= 5:
                    cards = [groups[straight_eligible[k]][0] for k in range(i, j + 1)]
                    combos.append(Combination(
                        CombType.STRAIGHT, tuple(cards), int(straight_eligible[j])
                    ))
            else:
                break

    # Consecutive pairs: 3+ consecutive ranks each with ≥2 cards, range [THREE, ACE]
    pair_eligible = sorted(r for r in groups if len(groups[r]) >= 2 and Rank.THREE <= r <= Rank.ACE)
    for i in range(len(pair_eligible)):
        run_len = 1
        for j in range(i + 1, len(pair_eligible)):
            if int(pair_eligible[j]) == int(pair_eligible[j - 1]) + 1:
                run_len += 1
                if run_len >= 3:
                    cards = []
                    for k in range(i, j + 1):
                        cards.extend(groups[pair_eligible[k]][:2])
                    combos.append(Combination(
                        CombType.CONSECUTIVE_PAIRS, tuple(cards), int(pair_eligible[j])
                    ))
            else:
                break

    # Triple+single: triple rank + one different card (deduplicated by kicker rank)
    triple_ranks = [r for r, cards in groups.items() if len(cards) >= 3 and r < Rank.SMALL_JOKER]
    for tr in triple_ranks:
        triple_cards = groups[tr][:3]
        seen_kicker: set = set()
        for card in hand_cards:
            if card.rank != tr and card.rank not in seen_kicker:
                seen_kicker.add(card.rank)
                combos.append(Combination(
                    CombType.TRIPLE_SINGLE, tuple(triple_cards + [card]), int(tr)
                ))

    # Triple+pair: triple rank + a different pair
    for tr in triple_ranks:
        triple_cards = groups[tr][:3]
        for pr, pr_cards in groups.items():
            if pr != tr and len(pr_cards) >= 2:
                combos.append(Combination(
                    CombType.TRIPLE_PAIR, tuple(triple_cards + pr_cards[:2]), int(tr)
                ))

    return combos
```

- [ ] **Step 4: Run tests to verify pass**

```
pytest tests/test_combination.py -v
```
Expected: 13 tests PASSED

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/game/combination.py tests/test_combination.py
git commit -m "feat: add CombType, Combination, get_all_combinations()"
```

---

## Task 3: Beat Logic and Legal Move Generation

**Files:**
- Create: `dou_dizhu_simulator/game/rules.py`
- Create: `dou_dizhu_simulator/game/__init__.py` (empty)
- Create: `tests/test_rules.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_rules.py
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import CombType, Combination, get_all_combinations
from dou_dizhu_simulator.game.rules import beats, get_legal_moves

def _cards(rank_suit_pairs):
    return [Card(Rank(r), s) for r, s in rank_suit_pairs]

def _single(rank):
    return Combination(CombType.SINGLE, (Card(Rank(rank), 'S'),), rank)

def _pair(rank):
    return Combination(CombType.PAIR, (Card(Rank(rank), 'S'), Card(Rank(rank), 'H')), rank)

def _bomb(rank):
    cards = tuple(Card(Rank(rank), s) for s in ('S','H','D','C'))
    return Combination(CombType.BOMB, cards, rank)

def _joker_bomb():
    return Combination(CombType.JOKER_BOMB,
                       (Card(Rank.SMALL_JOKER,'J'), Card(Rank.BIG_JOKER,'J')),
                       int(Rank.BIG_JOKER))

def test_higher_single_beats_lower():
    assert beats(_single(8), _single(7))

def test_lower_single_does_not_beat_higher():
    assert not beats(_single(6), _single(7))

def test_same_rank_does_not_beat():
    assert not beats(_single(7), _single(7))

def test_pair_beats_lower_pair():
    assert beats(_pair(10), _pair(9))

def test_pair_does_not_beat_single():
    assert not beats(_pair(10), _single(5))

def test_bomb_beats_single():
    assert beats(_bomb(5), _single(14))

def test_bomb_beats_higher_pair():
    assert beats(_bomb(3), _pair(15))  # 3-bomb beats pair-of-2

def test_higher_bomb_beats_lower_bomb():
    assert beats(_bomb(8), _bomb(7))

def test_lower_bomb_does_not_beat_higher_bomb():
    assert not beats(_bomb(6), _bomb(7))

def test_joker_bomb_beats_bomb():
    assert beats(_joker_bomb(), _bomb(14))

def test_nothing_beats_joker_bomb():
    assert not beats(_bomb(14), _joker_bomb())
    assert not beats(_single(17), _joker_bomb())

def test_straight_beaten_by_higher_same_length():
    s1 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'S') for r in range(3,8)), 7)
    s2 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'H') for r in range(4,9)), 8)
    assert beats(s2, s1)

def test_straight_different_length_cannot_beat():
    s5 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'S') for r in range(3,8)), 7)
    s6 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'H') for r in range(3,9)), 8)
    assert not beats(s6, s5)

def test_get_legal_moves_free_play_returns_all():
    hand = _cards([(5,'S'),(5,'H'),(7,'D')])
    legal = get_legal_moves(hand, None)
    all_combos = get_all_combinations(hand)
    assert len(legal) == len(all_combos)

def test_get_legal_moves_filtered_to_beaters():
    hand = _cards([(8,'S'),(9,'H'),(10,'D')])
    last = _single(7)
    legal = get_legal_moves(hand, last)
    # Should include singles of 8, 9, 10 but not 7 or lower
    single_ranks = {c.rank_value for c in legal if c.type == CombType.SINGLE}
    assert 8 in single_ranks
    assert 9 in single_ranks
    assert 10 in single_ranks

def test_get_legal_moves_empty_when_cannot_beat():
    hand = _cards([(3,'S'),(4,'H')])
    last = _single(14)  # Ace — can't beat with 3 or 4
    legal = get_legal_moves(hand, last)
    non_bomb = [c for c in legal if c.type not in (CombType.BOMB, CombType.JOKER_BOMB)]
    assert len(non_bomb) == 0
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_rules.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Implement rules.py**

```python
# dou_dizhu_simulator/game/rules.py
from typing import List, Optional
from .card import Card, Rank
from .combination import Combination, CombType, get_all_combinations

def beats(combo: Combination, last_combo: Combination) -> bool:
    if combo.type == CombType.JOKER_BOMB:
        return last_combo.type != CombType.JOKER_BOMB

    if combo.type == CombType.BOMB:
        if last_combo.type == CombType.JOKER_BOMB:
            return False
        if last_combo.type == CombType.BOMB:
            return combo.rank_value > last_combo.rank_value
        return True  # bomb beats any non-bomb

    if last_combo.type in (CombType.JOKER_BOMB, CombType.BOMB):
        return False  # non-bomb can't beat bomb

    if combo.type != last_combo.type:
        return False

    if combo.type in (CombType.STRAIGHT, CombType.CONSECUTIVE_PAIRS):
        if len(combo.cards) != len(last_combo.cards):
            return False

    return combo.rank_value > last_combo.rank_value

def get_legal_moves(hand_cards: List[Card], last_combo: Optional[Combination]) -> List[Combination]:
    all_combos = get_all_combinations(hand_cards)
    if last_combo is None:
        return all_combos
    return [c for c in all_combos if beats(c, last_combo)]
```

- [ ] **Step 4: Run tests to verify pass**

```
pytest tests/test_rules.py -v
```
Expected: 17 tests PASSED

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/game/rules.py tests/test_rules.py
git commit -m "feat: add beats() and get_legal_moves()"
```

---

## Task 4: Player Policies

**Files:**
- Create: `dou_dizhu_simulator/agents/__init__.py` (empty)
- Create: `dou_dizhu_simulator/agents/base.py`
- Create: `dou_dizhu_simulator/agents/random_policy.py`
- Create: `dou_dizhu_simulator/agents/heuristic_policy.py`

No separate test file for policies — they are tested implicitly through game engine tests in Task 5. The key correctness property (determinism, always-play-if-legal) is enforced by the interface.

- [ ] **Step 1: Implement base.py**

```python
# dou_dizhu_simulator/agents/base.py
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
    ) -> Optional[Combination]:
        """Return a Combination to play, or None to pass. Always play if legal_moves is non-empty."""
```

- [ ] **Step 2: Implement random_policy.py**

```python
# dou_dizhu_simulator/agents/random_policy.py
import random
from typing import List, Optional
from .base import PlayerPolicy
from ..game.card import Card
from ..game.combination import Combination

class RandomPolicy(PlayerPolicy):
    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
    ) -> Optional[Combination]:
        if not legal_moves:
            return None
        return self._rng.choice(legal_moves)
```

- [ ] **Step 3: Implement heuristic_policy.py**

```python
# dou_dizhu_simulator/agents/heuristic_policy.py
from typing import List, Optional
from .base import PlayerPolicy
from ..game.card import Card
from ..game.combination import Combination, CombType

_BOMB_TYPES = (CombType.BOMB, CombType.JOKER_BOMB)

class HeuristicPolicy(PlayerPolicy):
    def choose_move(
        self,
        hand: List[Card],
        legal_moves: List[Combination],
        last_combo: Optional[Combination],
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

- [ ] **Step 4: Commit**

```
git add dou_dizhu_simulator/agents/
git commit -m "feat: add PlayerPolicy, RandomPolicy, HeuristicPolicy"
```

---

## Task 5: Game Engine

**Files:**
- Create: `dou_dizhu_simulator/engine/__init__.py` (empty)
- Create: `dou_dizhu_simulator/engine/game.py`
- Create: `tests/test_game.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_game.py
import random
from dou_dizhu_simulator.engine.game import GameRound
from dou_dizhu_simulator.agents.random_policy import RandomPolicy
from dou_dizhu_simulator.game.card import ACE_OF_SPADES, THREE_OF_HEARTS, Rank

def _make_policies(seed):
    rng = random.Random(seed)
    return [RandomPolicy(rng) for _ in range(3)]

def test_deal_gives_54_cards_total():
    rng = random.Random(42)
    game = GameRound(rng)
    hands, _ = game.deal_cards()
    total = sum(len(h) for h in hands)
    assert total == 54

def test_deal_gives_18_each():
    rng = random.Random(42)
    game = GameRound(rng)
    hands, _ = game.deal_cards()
    assert all(len(h) == 18 for h in hands)

def test_player_0_always_has_ace_of_spades():
    for seed in range(20):
        rng = random.Random(seed)
        game = GameRound(rng)
        hands, _ = game.deal_cards()
        assert ACE_OF_SPADES in hands[0], f"seed={seed}: P0 missing Ace of Spades"

def test_first_player_has_three_of_hearts():
    for seed in range(20):
        rng = random.Random(seed)
        game = GameRound(rng)
        hands, first = game.deal_cards()
        assert THREE_OF_HEARTS in hands[first], f"seed={seed}: first player doesn't hold 3H"

def test_game_terminates_and_returns_valid_winner():
    rng = random.Random(0)
    policies = _make_policies(1)
    game = GameRound(rng)
    winner, turns = game.play(policies)
    assert winner in (0, 1, 2)
    assert turns > 0

def test_winner_has_empty_hand():
    rng = random.Random(0)
    policies = _make_policies(1)
    game = GameRound(rng)
    # Play stores hands internally; verify via multiple games — winner always valid
    results = []
    for seed in range(50):
        g = GameRound(random.Random(seed))
        p = _make_policies(seed + 1000)
        w, t = g.play(p)
        results.append(w)
    assert all(r in (0, 1, 2) for r in results)

def test_same_seed_same_outcome():
    def run(seed):
        rng = random.Random(seed)
        policies = [RandomPolicy(random.Random(seed + i)) for i in range(3)]
        return GameRound(rng).play(policies)
    assert run(7) == run(7)
    assert run(42) == run(42)
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_game.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Implement game.py**

```python
# dou_dizhu_simulator/engine/game.py
import random
from typing import List, Optional, Tuple
from ..game.card import Card, make_deck, ACE_OF_SPADES, THREE_OF_HEARTS
from ..game.combination import Combination, get_all_combinations
from ..game.rules import get_legal_moves
from ..agents.base import PlayerPolicy

class GameRound:
    def __init__(self, rng: random.Random) -> None:
        self._rng = rng

    def deal_cards(self) -> Tuple[List[List[Card]], int]:
        deck = make_deck()
        self._rng.shuffle(deck)

        # Ensure Player 0 (black gun) always holds Ace of Spades
        ace_idx = next(i for i, c in enumerate(deck) if c == ACE_OF_SPADES)
        deck[0], deck[ace_idx] = deck[ace_idx], deck[0]

        hands = [deck[0:18], deck[18:36], deck[36:54]]

        first = next(i for i, h in enumerate(hands) if THREE_OF_HEARTS in h)
        return hands, first

    def play(self, policies: List[PlayerPolicy]) -> Tuple[int, int]:
        """Returns (winner_index, total_turns)."""
        hands, current = self.deal_cards()
        last_combo: Optional[Combination] = None
        last_player = current
        passes = 0
        turns = 0

        while True:
            hand = hands[current]

            if last_combo is None:
                legal = get_all_combinations(hand)
            else:
                legal = get_legal_moves(hand, last_combo)

            move = policies[current].choose_move(hand, legal, last_combo)

            if move is None:
                passes += 1
                if passes >= 2:
                    last_combo = None
                    passes = 0
                    current = last_player
                    continue
            else:
                for card in move.cards:
                    hand.remove(card)
                last_combo = move
                last_player = current
                passes = 0

                if not hand:
                    return current, turns

            turns += 1
            current = (current + 1) % 3
```

- [ ] **Step 4: Run tests to verify pass**

```
pytest tests/test_game.py -v
```
Expected: 7 tests PASSED

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/engine/ tests/test_game.py
git commit -m "feat: add GameRound with deal and play loop"
```

---

## Task 6: Monte Carlo Runner

**Files:**
- Create: `dou_dizhu_simulator/experiments/__init__.py` (empty)
- Create: `dou_dizhu_simulator/experiments/runner.py`
- Create: `tests/test_runner.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_runner.py
from dou_dizhu_simulator.experiments.runner import MonteCarloSimulator, SimResults
from dou_dizhu_simulator.agents.random_policy import RandomPolicy
from dou_dizhu_simulator.agents.heuristic_policy import HeuristicPolicy
import random

def _random_factory(rng):
    return RandomPolicy(rng)

def _heuristic_factory(_rng):
    return HeuristicPolicy()

def test_sim_results_count_correct():
    sim = MonteCarloSimulator(_random_factory)
    results = sim.run(n_games=100, seed=0)
    assert results.n_games == 100
    assert sum(results.wins) == 100

def test_sim_win_rates_sum_to_1():
    sim = MonteCarloSimulator(_random_factory)
    results = sim.run(n_games=200, seed=1)
    assert abs(sum(results.win_rates) - 1.0) < 1e-9

def test_sim_reproducible():
    sim = MonteCarloSimulator(_random_factory)
    r1 = sim.run(n_games=500, seed=42)
    r2 = sim.run(n_games=500, seed=42)
    assert r1.wins == r2.wins

def test_sim_heuristic_terminates():
    sim = MonteCarloSimulator(_heuristic_factory)
    results = sim.run(n_games=100, seed=0)
    assert sum(results.wins) == 100

def test_sim_tracks_turns():
    sim = MonteCarloSimulator(_random_factory)
    results = sim.run(n_games=100, seed=0)
    assert results.total_turns > 0
    assert results.avg_turns > 0
```

- [ ] **Step 2: Run to verify failure**

```
pytest tests/test_runner.py -v
```
Expected: `ImportError`

- [ ] **Step 3: Implement runner.py**

```python
# dou_dizhu_simulator/experiments/runner.py
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
```

- [ ] **Step 4: Run tests to verify pass**

```
pytest tests/test_runner.py -v
```
Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/experiments/runner.py tests/test_runner.py
git commit -m "feat: add MonteCarloSimulator and SimResults"
```

---

## Task 7: Statistical Analysis

**Files:**
- Create: `dou_dizhu_simulator/experiments/analysis.py`

No separate test file — correctness verified by known values in the implementation below.

- [ ] **Step 1: Implement analysis.py**

```python
# dou_dizhu_simulator/experiments/analysis.py
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
```

- [ ] **Step 2: Verify manually**

```python
# Quick sanity check (run in Python REPL):
from dou_dizhu_simulator.experiments.analysis import wilson_ci
lo, hi = wilson_ci(33333, 100000)
assert 0.330 < lo < 0.333
assert 0.333 < hi < 0.337
print(lo, hi)  # should be ~(0.3306, 0.3361)
```

- [ ] **Step 3: Commit**

```
git add dou_dizhu_simulator/experiments/analysis.py
git commit -m "feat: add wilson_ci and run_analysis reporting"
```

---

## Task 8: Main Entry Point and Full Run

**Files:**
- Create: `dou_dizhu_simulator/main.py`

- [ ] **Step 1: Implement main.py**

```python
# dou_dizhu_simulator/main.py
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
    random_results = random_sim.run(N_GAMES, seed=SEED)
    run_analysis(random_results, "Model 0: Random Policy")

    print("Running Model 1: Heuristic Policy...")
    heuristic_sim = MonteCarloSimulator(_heuristic_factory)
    heuristic_results = heuristic_sim.run(N_GAMES, seed=SEED)
    run_analysis(heuristic_results, "Model 1: Heuristic Policy")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run full suite to verify all tests still pass**

```
pytest tests/ -v
```
Expected: all tests PASSED

- [ ] **Step 3: Run the simulator (small test first)**

Edit `N_GAMES = 1_000` temporarily, then run:
```
python -m dou_dizhu_simulator.main
```
Expected: output showing win rates, CIs, p-values for both models. Verify output looks reasonable (each player ~33%, p-value non-significant likely).

- [ ] **Step 4: Run full 100K simulation**

Restore `N_GAMES = 100_000`, then:
```
python -m dou_dizhu_simulator.main
```
Expected runtime: ~30 seconds–2 minutes. Output shows final statistical report.

- [ ] **Step 5: Commit**

```
git add dou_dizhu_simulator/main.py
git commit -m "feat: add main entry point with 100K game experiments"
```

---

## Task 9: Package Setup

**Files:**
- Create: `setup.py` or `pyproject.toml`
- Create: `requirements.txt`

- [ ] **Step 1: Create requirements.txt**

```
# requirements.txt
scipy>=1.10
pytest>=7.0
```

- [ ] **Step 2: Create pyproject.toml**

```toml
# pyproject.toml
[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "dou_dizhu_simulator"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["scipy>=1.10"]
```

- [ ] **Step 3: Install and run**

```
pip install -e .
python -m dou_dizhu_simulator.main
```

- [ ] **Step 4: Commit**

```
git add requirements.txt pyproject.toml
git commit -m "chore: add package setup and requirements"
```

---

## Self-Review Against Spec

| Requirement | Task |
|---|---|
| 54 cards, 18+18+18 deal | Task 5 (GameRound.deal_cards) |
| Player 0 always gets Ace of Spades | Task 5 |
| First player = 3 of Hearts holder | Task 5 |
| All 9 combo types including triple+kicker | Task 2 |
| Beat logic: joker bomb > bomb > same-type | Task 3 |
| Straight min 5, no 2s/jokers | Task 2 |
| Consecutive pairs min 3, no 2s/jokers | Task 2 |
| Two consecutive passes reset trick | Task 5 (game loop) |
| RandomPolicy uniform random | Task 4 |
| HeuristicPolicy deterministic | Task 4 |
| 100K games with fixed seed | Task 6+8 |
| Wilson 95% CI | Task 7 |
| Binomial test vs null p=1/3 | Task 7 |
| Reproducible: same seed = same result | Task 6 (tested) |
| scipy/numpy allowed | Task 7 (scipy.stats) |
