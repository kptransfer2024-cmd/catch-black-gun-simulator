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


def _maximal_sequences(
    combos: List[Combination], hand: List[Card], comb_type: CombType
) -> List[Combination]:
    """Return only maximal (non-extendable) sequences of the given type from combos."""
    hand_ranks = set(int(c.rank) for c in hand if Rank.THREE <= c.rank <= Rank.ACE)
    result = []
    for m in combos:
        if m.type != comb_type:
            continue
        card_ranks = [int(c.rank) for c in m.cards]
        # For consecutive pairs, each rank appears twice; deduplicate
        unique_ranks = sorted(set(card_ranks))
        min_r, max_r = unique_ranks[0], unique_ranks[-1]
        can_extend_left = (min_r - 1) >= 3 and (min_r - 1) in hand_ranks
        can_extend_right = (max_r + 1) <= 14 and (max_r + 1) in hand_ranks
        if not can_extend_left and not can_extend_right:
            result.append(m)
    return result


def _lead_sort_key(combo: Combination):
    cat = _LEAD_CATEGORY.get(combo.type, 4)
    if cat == 0:
        return (0, combo.rank_value, -len(combo.cards))
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
        if last_combo is None:
            if len(hand) <= 5:
                return max(legal_moves, key=lambda c: len(c.cards))
            return self._lead(hand, legal_moves)
        return self._follow(hand, legal_moves, last_combo)

    def _lead(self, hand: List[Card], legal_moves: List[Combination]) -> Combination:
        # Build candidate pool: non-bomb combos in LEAD_CATEGORY,
        # using only maximal straights and consecutive pair runs
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

        # Last resort: minimum non-bomb move
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
