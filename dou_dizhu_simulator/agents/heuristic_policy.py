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
