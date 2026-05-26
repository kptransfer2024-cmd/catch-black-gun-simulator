from collections import defaultdict
from typing import List, Optional, Set
from .base import PlayerPolicy
from ..game.card import Card, Rank
from ..game.combination import Combination, CombType

_BOMB_TYPES = (CombType.BOMB, CombType.JOKER_BOMB)
_HIGH_PAIR_RANK = 13   # K=13, A=14, 2=15 all get soft protection
_WEAK_TRICK_RANK = 7   # opponent pair rank <= 7 triggers soft protection

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
