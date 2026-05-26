from typing import List, Optional
from .tactical_policy import TacticalPolicy
from .combo_policy import _BOMB_TYPES
from ..game.card import Card
from ..game.combination import Combination

_COALITION_DANGER_THRESHOLD = 3


class CoalitionPolicy(TacticalPolicy):
    """
    Model 4: Coalition-aware policy for Player 1 and Player 2.

    Before P0 plays the Ace of Spades: behaves identically to TacticalPolicy.
    After the Ace of Spades is revealed: P1 and P2 enter coalition mode —
      - Pass whenever the coalition partner currently holds the trick (let them keep lead)
      - Beat P0 aggressively when P0 holds the trick (ignore protection)
      - Play max cards when P0 is close to winning or own hand is near-empty
    P0 (player_idx=0) always behaves like TacticalPolicy regardless.
    """

    def __init__(self, player_idx: int) -> None:
        self._player_idx = player_idx

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

        # P0 plays like TacticalPolicy always; non-coalition before ace is shown
        if self._player_idx == 0 or not ace_revealed:
            return super().choose_move(
                hand, legal_moves, last_combo, opponent_hand_sizes,
                ace_revealed, last_player_idx,
            )

        # --- Coalition mode (P1 or P2, ace revealed) ---

        p0_size = self._p0_hand_size(opponent_hand_sizes)
        p0_danger = p0_size is not None and p0_size <= _COALITION_DANGER_THRESHOLD

        # Finish fast: own hand nearly empty, or P0 about to win
        if p0_danger or len(hand) <= 5:
            return max(legal_moves, key=lambda c: len(c.cards))

        # Free lead: play normally
        if last_combo is None:
            return self._lead(hand, legal_moves)

        # Following: key decision based on who currently holds the trick
        if last_player_idx == 0:
            return self._beat_p0(legal_moves)

        # Partner holds the trick — pass to give them the next lead
        return None

    def _beat_p0(self, legal_moves: List[Combination]) -> Optional[Combination]:
        """Beat P0 with minimum card, ignoring protection. Use bombs if needed."""
        non_bombs = [m for m in legal_moves if m.type not in _BOMB_TYPES]
        if non_bombs:
            return min(non_bombs, key=lambda c: (c.rank_value, len(c.cards)))
        return min(legal_moves, key=lambda c: c.rank_value)

    def _p0_hand_size(self, opponent_hand_sizes: Optional[List[int]]) -> Optional[int]:
        """Extract P0's hand size from the relative opponent_hand_sizes list."""
        if opponent_hand_sizes is None:
            return None
        # opp_sizes = [next_player_size, prev_player_size]
        # For P1 (idx 1): next=P2, prev=P0  → P0 is at index 1
        # For P2 (idx 2): next=P0, prev=P1  → P0 is at index 0
        if self._player_idx == 1:
            return opponent_hand_sizes[1]
        return opponent_hand_sizes[0]
