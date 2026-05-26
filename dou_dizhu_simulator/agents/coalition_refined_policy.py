from typing import List, Optional
from .coalition_policy import CoalitionPolicy, _COALITION_DANGER_THRESHOLD
from .combo_policy import _BOMB_TYPES, _get_protected_cards
from ..game.card import Card
from ..game.combination import Combination, CombType

_BOMB_DEPLOY_THRESHOLD = 4  # deploy bombs against P0 when P0 has <= this many cards


class CoalitionRefinedPolicy(CoalitionPolicy):
    """
    Model 5: Coalition with three refinements over Model 4.

    1. Priority protocol — the coalition member with fewer cards is the "winner
       candidate"; the other is the sacrificer and hands off control completely.

    2. Tempo transfer — the sacrificer leads the cheapest unprotected single on
       a free lead, making it easy for the partner to take the trick and the lead.

    3. Selective coalition bombing — the sacrificer ignores bomb conservation and
       uses bombs to beat P0's moves; the priority player also bombs P0 when P0
       has <= BOMB_DEPLOY_THRESHOLD cards remaining.
    """

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

        if self._player_idx == 0 or not ace_revealed:
            return super().choose_move(
                hand, legal_moves, last_combo, opponent_hand_sizes,
                ace_revealed, last_player_idx,
            )

        # --- Coalition refined mode ---
        p0_size = self._p0_hand_size(opponent_hand_sizes)
        partner_size = self._partner_hand_size(opponent_hand_sizes)

        p0_danger = p0_size is not None and p0_size <= _COALITION_DANGER_THRESHOLD

        if p0_danger or len(hand) <= 5:
            return max(legal_moves, key=lambda c: len(c.cards))

        # Feature 1: priority protocol
        # Whoever has fewer cards is the winner candidate; the other is the sacrificer.
        i_am_priority = partner_size is None or len(hand) <= partner_size

        if last_combo is None:
            # Feature 2: tempo transfer
            if not i_am_priority:
                return self._tempo_transfer(hand, legal_moves)
            return self._lead(hand, legal_moves)

        if last_player_idx == 0:
            # Feature 3: selective coalition bombing
            # Sacrificer always includes bombs; priority player does so when P0 is close.
            use_bombs = (not i_am_priority) or (
                p0_size is not None and p0_size <= _BOMB_DEPLOY_THRESHOLD
            )
            return self._beat_p0_refined(legal_moves, use_bombs)

        # Partner holds trick: pass
        return None

    def _tempo_transfer(
        self, hand: List[Card], legal_moves: List[Combination]
    ) -> Combination:
        """Lead cheapest unprotected single so partner can easily take the trick."""
        protected = _get_protected_cards(hand)
        singles = [m for m in legal_moves if m.type == CombType.SINGLE]
        unprotected = [m for m in singles if m.cards[0] not in protected]
        pool = unprotected if unprotected else singles
        if pool:
            return min(pool, key=lambda c: c.rank_value)
        return self._lead(hand, legal_moves)

    def _beat_p0_refined(
        self, legal_moves: List[Combination], use_bombs: bool
    ) -> Optional[Combination]:
        """
        Beat P0 with minimum card.
        use_bombs=True: bombs are included as candidates (sacrificer / P0 near win).
        use_bombs=False: prefer non-bombs to preserve them for later.
        """
        if use_bombs:
            return min(legal_moves, key=lambda c: (c.rank_value, len(c.cards)))
        non_bombs = [m for m in legal_moves if m.type not in _BOMB_TYPES]
        if non_bombs:
            return min(non_bombs, key=lambda c: (c.rank_value, len(c.cards)))
        return min(legal_moves, key=lambda c: c.rank_value)

    def _partner_hand_size(
        self, opponent_hand_sizes: Optional[List[int]]
    ) -> Optional[int]:
        """Extract coalition partner's hand size from the relative opp_sizes list."""
        if opponent_hand_sizes is None:
            return None
        # opp_sizes = [next_player, prev_player]
        # For P1 (idx=1): next=P2 (partner), prev=P0  → partner at index 0
        # For P2 (idx=2): next=P0,           prev=P1  → partner at index 1
        if self._player_idx == 1:
            return opponent_hand_sizes[0]
        return opponent_hand_sizes[1]
