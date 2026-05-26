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
