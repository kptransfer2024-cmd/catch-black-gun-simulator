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
