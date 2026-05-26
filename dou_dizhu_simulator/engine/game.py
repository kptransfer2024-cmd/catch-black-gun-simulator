import random
from typing import List, Optional, Tuple
from ..game.card import Card, make_deck, ACE_OF_SPADES, THREE_OF_HEARTS
from ..game.combination import Combination
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

    def play(self, policies: List[PlayerPolicy], trace: bool = False) -> Tuple[int, int]:
        """Returns (winner_index, total_turns)."""
        hands, current = self.deal_cards()
        last_combo: Optional[Combination] = None
        last_player = current
        ace_revealed = False
        passes = 0
        turns = 0

        if trace:
            print(f"\n{'-'*60}")
            print(f"  DEAL")
            print(f"{'-'*60}")
            for i, h in enumerate(hands):
                label = " [BLACK GUN]" if i == 0 else ""
                sorted_hand = sorted(h, key=lambda c: int(c.rank))
                print(f"  P{i}{label}: {sorted_hand}")
            print(f"  First player: P{current}")

        while True:
            hand = hands[current]
            legal = get_legal_moves(hand, last_combo)
            opp_sizes = [len(hands[(current + 1) % 3]), len(hands[(current + 2) % 3])]
            move = policies[current].choose_move(
                hand, legal, last_combo, opp_sizes, ace_revealed, last_player
            )

            if trace:
                trick_str = f"(trick: {last_combo})" if last_combo else "(free lead)"
                if move is None:
                    print(f"  T{turns:>3}  P{current} [{len(hand):>2} cards]  PASS  {trick_str}")
                else:
                    print(f"  T{turns:>3}  P{current} [{len(hand):>2} cards]  plays {move.type.name}  {list(move.cards)}  {trick_str}")

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
                if current == 0 and not ace_revealed:
                    ace_revealed = ACE_OF_SPADES in move.cards

                if not hand:
                    if trace:
                        label = " (BLACK GUN)" if current == 0 else ""
                        print(f"\n  >> P{current}{label} wins in {turns} turns")
                    return current, turns

            turns += 1
            current = (current + 1) % 3
