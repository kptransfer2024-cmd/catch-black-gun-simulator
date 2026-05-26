from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import (
    CombType, Combination, get_all_combinations
)

def _cards(rank_suit_pairs):
    return [Card(Rank(r), s) for r, s in rank_suit_pairs]

def test_single_from_one_card():
    hand = _cards([(5, 'S')])
    combos = get_all_combinations(hand)
    singles = [c for c in combos if c.type == CombType.SINGLE]
    assert len(singles) == 1
    assert singles[0].rank_value == 5

def test_pair_detected():
    hand = _cards([(7, 'S'), (7, 'H')])
    combos = get_all_combinations(hand)
    pairs = [c for c in combos if c.type == CombType.PAIR]
    assert len(pairs) == 1
    assert pairs[0].rank_value == 7

def test_no_pair_from_jokers():
    hand = _cards([(16, 'J'), (17, 'J')])
    combos = get_all_combinations(hand)
    pairs = [c for c in combos if c.type == CombType.PAIR]
    assert len(pairs) == 0

def test_joker_bomb_detected():
    hand = _cards([(16, 'J'), (17, 'J')])
    combos = get_all_combinations(hand)
    jbombs = [c for c in combos if c.type == CombType.JOKER_BOMB]
    assert len(jbombs) == 1

def test_bomb_4_of_a_kind():
    hand = _cards([(9, 'S'), (9, 'H'), (9, 'D'), (9, 'C')])
    combos = get_all_combinations(hand)
    bombs = [c for c in combos if c.type == CombType.BOMB]
    assert len(bombs) == 1
    assert bombs[0].rank_value == 9

def test_straight_5_cards():
    hand = _cards([(3,'S'),(4,'H'),(5,'D'),(6,'C'),(7,'S')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 1
    assert straights[0].rank_value == 7  # highest card rank

def test_straight_no_short_straights():
    # Only 4 consecutive cards — not a valid straight
    hand = _cards([(3,'S'),(4,'H'),(5,'D'),(6,'C')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 0

def test_straight_no_twos_or_jokers():
    hand = _cards([(13,'S'),(14,'H'),(15,'D'),(3,'C'),(4,'S')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 0  # 13(K),14(A),15(2) — 2 breaks it

def test_consecutive_pairs_3_pairs():
    hand = _cards([(5,'S'),(5,'H'),(6,'D'),(6,'C'),(7,'S'),(7,'H')])
    combos = get_all_combinations(hand)
    cpairs = [c for c in combos if c.type == CombType.CONSECUTIVE_PAIRS]
    assert len(cpairs) == 1
    assert cpairs[0].rank_value == 7

def test_consecutive_pairs_need_3_minimum():
    hand = _cards([(5,'S'),(5,'H'),(6,'D'),(6,'C')])
    combos = get_all_combinations(hand)
    cpairs = [c for c in combos if c.type == CombType.CONSECUTIVE_PAIRS]
    assert len(cpairs) == 0

def test_triple_single():
    hand = _cards([(8,'S'),(8,'H'),(8,'D'),(5,'C')])
    combos = get_all_combinations(hand)
    ts = [c for c in combos if c.type == CombType.TRIPLE_SINGLE]
    assert len(ts) == 1
    assert ts[0].rank_value == 8

def test_triple_pair():
    hand = _cards([(8,'S'),(8,'H'),(8,'D'),(5,'C'),(5,'S')])
    combos = get_all_combinations(hand)
    tp = [c for c in combos if c.type == CombType.TRIPLE_PAIR]
    assert len(tp) == 1
    assert tp[0].rank_value == 8

def test_combination_cards_are_tuple():
    hand = _cards([(5,'S')])
    combos = get_all_combinations(hand)
    assert isinstance(combos[0].cards, tuple)

def test_straight_multiple_from_6_consecutive_cards():
    # With 3,4,5,6,7,8 a player can form three valid straights:
    # (3,4,5,6,7), (4,5,6,7,8), and (3,4,5,6,7,8)
    hand = _cards([(3,'S'),(4,'H'),(5,'D'),(6,'C'),(7,'S'),(8,'H')])
    combos = get_all_combinations(hand)
    straights = [c for c in combos if c.type == CombType.STRAIGHT]
    assert len(straights) == 3
    lengths = sorted(len(c.cards) for c in straights)
    assert lengths == [5, 5, 6]
