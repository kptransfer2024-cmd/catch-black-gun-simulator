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
        opponent_hand_sizes: Optional[List[int]] = None,
        ace_revealed: bool = False,
        last_player_idx: Optional[int] = None,
    ) -> Optional[Combination]:
        if not legal_moves:
            return None
        return self._rng.choice(legal_moves)
