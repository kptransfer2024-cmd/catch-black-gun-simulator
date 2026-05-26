from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict
from collections import defaultdict
from .card import Card, Rank


class CombType(Enum):
    SINGLE = auto()
    PAIR = auto()
    TRIPLE = auto()
    TRIPLE_SINGLE = auto()
    TRIPLE_PAIR = auto()
    BOMB = auto()
    STRAIGHT = auto()
    CONSECUTIVE_PAIRS = auto()
    JOKER_BOMB = auto()


@dataclass(frozen=True)
class Combination:
    type: CombType
    cards: tuple
    rank_value: int


def get_all_combinations(hand_cards: List[Card]) -> List[Combination]:
    combos: List[Combination] = []
    groups: Dict[Rank, List[Card]] = defaultdict(list)
    for card in hand_cards:
        groups[card.rank].append(card)

    # Singles
    for card in hand_cards:
        combos.append(Combination(CombType.SINGLE, (card,), int(card.rank)))

    # Pairs (not jokers)
    for rank, cards in groups.items():
        if len(cards) >= 2 and rank < Rank.SMALL_JOKER:
            combos.append(Combination(CombType.PAIR, tuple(cards[:2]), int(rank)))

    # Triples
    for rank, cards in groups.items():
        if len(cards) >= 3 and rank < Rank.SMALL_JOKER:
            combos.append(Combination(CombType.TRIPLE, tuple(cards[:3]), int(rank)))

    # Bombs (4-of-a-kind)
    for rank, cards in groups.items():
        if len(cards) >= 4 and rank < Rank.SMALL_JOKER:
            combos.append(Combination(CombType.BOMB, tuple(cards[:4]), int(rank)))

    # Joker bomb
    if Rank.SMALL_JOKER in groups and Rank.BIG_JOKER in groups:
        sj = groups[Rank.SMALL_JOKER][0]
        bj = groups[Rank.BIG_JOKER][0]
        combos.append(Combination(CombType.JOKER_BOMB, (sj, bj), int(Rank.BIG_JOKER)))

    # Straights: 5+ consecutive ranks in range [THREE, ACE], each rank exactly once
    straight_eligible = sorted(r for r in groups if Rank.THREE <= r <= Rank.ACE)
    for i in range(len(straight_eligible)):
        run_len = 1
        for j in range(i + 1, len(straight_eligible)):
            if int(straight_eligible[j]) == int(straight_eligible[j - 1]) + 1:
                run_len += 1
                if run_len >= 5:
                    cards = [groups[straight_eligible[k]][0] for k in range(i, j + 1)]
                    combos.append(Combination(
                        CombType.STRAIGHT, tuple(cards), int(straight_eligible[j])
                    ))
            else:
                break

    # Consecutive pairs: 3+ consecutive ranks each with >=2 cards, range [THREE, ACE]
    pair_eligible = sorted(r for r in groups if len(groups[r]) >= 2 and Rank.THREE <= r <= Rank.ACE)
    for i in range(len(pair_eligible)):
        run_len = 1
        for j in range(i + 1, len(pair_eligible)):
            if int(pair_eligible[j]) == int(pair_eligible[j - 1]) + 1:
                run_len += 1
                if run_len >= 3:
                    cards = []
                    for k in range(i, j + 1):
                        cards.extend(groups[pair_eligible[k]][:2])
                    combos.append(Combination(
                        CombType.CONSECUTIVE_PAIRS, tuple(cards), int(pair_eligible[j])
                    ))
            else:
                break

    # Triple+single: triple rank + one different card (deduplicated by kicker rank)
    triple_ranks = [r for r, cards in groups.items() if len(cards) >= 3 and r < Rank.SMALL_JOKER]
    for tr in triple_ranks:
        triple_cards = groups[tr][:3]
        seen_kicker: set = set()
        for card in hand_cards:
            if card.rank != tr and card.rank not in seen_kicker:
                seen_kicker.add(card.rank)
                combos.append(Combination(
                    CombType.TRIPLE_SINGLE, tuple(triple_cards + [card]), int(tr)
                ))

    # Triple+pair: triple rank + a different pair
    for tr in triple_ranks:
        triple_cards = groups[tr][:3]
        for pr, pr_cards in groups.items():
            if pr != tr and len(pr_cards) >= 2:
                combos.append(Combination(
                    CombType.TRIPLE_PAIR, tuple(triple_cards + pr_cards[:2]), int(tr)
                ))

    return combos
