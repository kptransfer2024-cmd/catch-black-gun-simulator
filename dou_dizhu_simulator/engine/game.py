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
