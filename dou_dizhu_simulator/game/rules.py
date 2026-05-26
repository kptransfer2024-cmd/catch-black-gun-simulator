from typing import List, Optional
from .card import Card, Rank
from .combination import Combination, CombType, get_all_combinations


def beats(combo: Combination, last_combo: Combination) -> bool:
    """
    Determines if combo beats last_combo in Dou Dizhu.

    Rules:
    - JOKER_BOMB beats everything except another JOKER_BOMB
    - BOMB beats any non-bomb; higher rank bomb beats lower rank bomb
    - Non-bomb cannot beat BOMB or JOKER_BOMB
    - Non-bomb can only beat the same CombType
    - STRAIGHT and CONSECUTIVE_PAIRS must have same card count to be beatable
    - Higher rank_value beats lower rank_value (for same type + same length)
    """
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
    """
    Returns all legal moves for the given hand and last combo played.

    If last_combo is None, all combinations in the hand are legal (free play).
    Otherwise, only combinations that beat last_combo are legal.
    """
    all_combos = get_all_combinations(hand_cards)
    if last_combo is None:
        return all_combos
    return [c for c in all_combos if beats(c, last_combo)]
