from dataclasses import dataclass
from enum import IntEnum
from typing import List


class Rank(IntEnum):
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    TWO = 15
    SMALL_JOKER = 16
    BIG_JOKER = 17


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: str  # 'S' 'H' 'D' 'C' for normal cards; 'J' for jokers

    def __repr__(self) -> str:
        names = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'T',
                 11: 'J', 12: 'Q', 13: 'K', 14: 'A', 15: '2', 16: 'Sj', 17: 'Bj'}
        return f"{names[int(self.rank)]}{self.suit}"


ACE_OF_SPADES = Card(Rank.ACE, 'S')
THREE_OF_HEARTS = Card(Rank.THREE, 'H')


def make_deck() -> List[Card]:
    deck = []
    for rank_val in range(3, 16):  # 3 through 2
        for suit in ('S', 'H', 'D', 'C'):
            deck.append(Card(Rank(rank_val), suit))
    deck.append(Card(Rank.SMALL_JOKER, 'J'))
    deck.append(Card(Rank.BIG_JOKER, 'J'))
    return deck
