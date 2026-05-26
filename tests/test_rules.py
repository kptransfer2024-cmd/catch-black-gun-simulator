from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import CombType, Combination, get_all_combinations
from dou_dizhu_simulator.game.rules import beats, get_legal_moves

def _cards(rank_suit_pairs):
    return [Card(Rank(r), s) for r, s in rank_suit_pairs]

def _single(rank):
    return Combination(CombType.SINGLE, (Card(Rank(rank), 'S'),), rank)

def _pair(rank):
    return Combination(CombType.PAIR, (Card(Rank(rank), 'S'), Card(Rank(rank), 'H')), rank)

def _bomb(rank):
    cards = tuple(Card(Rank(rank), s) for s in ('S','H','D','C'))
    return Combination(CombType.BOMB, cards, rank)

def _joker_bomb():
    return Combination(CombType.JOKER_BOMB,
                       (Card(Rank.SMALL_JOKER,'J'), Card(Rank.BIG_JOKER,'J')),
                       int(Rank.BIG_JOKER))

def test_higher_single_beats_lower():
    assert beats(_single(8), _single(7))

def test_lower_single_does_not_beat_higher():
    assert not beats(_single(6), _single(7))

def test_same_rank_does_not_beat():
    assert not beats(_single(7), _single(7))

def test_pair_beats_lower_pair():
    assert beats(_pair(10), _pair(9))

def test_pair_does_not_beat_single():
    assert not beats(_pair(10), _single(5))

def test_bomb_beats_single():
    assert beats(_bomb(5), _single(14))

def test_bomb_beats_higher_pair():
    assert beats(_bomb(3), _pair(15))  # 3-bomb beats pair-of-2

def test_higher_bomb_beats_lower_bomb():
    assert beats(_bomb(8), _bomb(7))

def test_lower_bomb_does_not_beat_higher_bomb():
    assert not beats(_bomb(6), _bomb(7))

def test_joker_bomb_beats_bomb():
    assert beats(_joker_bomb(), _bomb(14))

def test_nothing_beats_joker_bomb():
    assert not beats(_bomb(14), _joker_bomb())
    assert not beats(_single(17), _joker_bomb())

def test_straight_beaten_by_higher_same_length():
    s1 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'S') for r in range(3,8)), 7)
    s2 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'H') for r in range(4,9)), 8)
    assert beats(s2, s1)

def test_straight_different_length_cannot_beat():
    s5 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'S') for r in range(3,8)), 7)
    s6 = Combination(CombType.STRAIGHT,
                     tuple(Card(Rank(r),'H') for r in range(3,9)), 8)
    assert not beats(s6, s5)

def test_get_legal_moves_free_play_returns_all():
    hand = _cards([(5,'S'),(5,'H'),(7,'D')])
    legal = get_legal_moves(hand, None)
    all_combos = get_all_combinations(hand)
    assert len(legal) == len(all_combos)

def test_get_legal_moves_filtered_to_beaters():
    hand = _cards([(8,'S'),(9,'H'),(10,'D')])
    last = _single(7)
    legal = get_legal_moves(hand, last)
    single_ranks = {c.rank_value for c in legal if c.type == CombType.SINGLE}
    assert 8 in single_ranks
    assert 9 in single_ranks
    assert 10 in single_ranks

def test_get_legal_moves_empty_when_cannot_beat():
    hand = _cards([(3,'S'),(4,'H')])
    last = _single(14)  # Ace — can't beat with 3 or 4
    legal = get_legal_moves(hand, last)
    non_bomb = [c for c in legal if c.type not in (CombType.BOMB, CombType.JOKER_BOMB)]
    assert len(non_bomb) == 0

def _triple(rank):
    cards = tuple(Card(Rank(rank), s) for s in ('S', 'H', 'D'))
    return Combination(CombType.TRIPLE, cards, rank)

def _consecutive_pairs(start_rank, num_pairs):
    cards = []
    for r in range(start_rank, start_rank + num_pairs):
        cards.append(Card(Rank(r), 'S'))
        cards.append(Card(Rank(r), 'H'))
    return Combination(CombType.CONSECUTIVE_PAIRS, tuple(cards), start_rank + num_pairs - 1)

def test_higher_triple_beats_lower():
    assert beats(_triple(9), _triple(8))

def test_triple_does_not_beat_pair():
    assert not beats(_triple(9), _pair(8))

def test_consecutive_pairs_higher_beats_lower_same_length():
    cp1 = _consecutive_pairs(5, 3)  # 5-6-7 pairs, rank_value=7
    cp2 = _consecutive_pairs(6, 3)  # 6-7-8 pairs, rank_value=8
    assert beats(cp2, cp1)

def test_consecutive_pairs_different_length_cannot_beat():
    cp3 = _consecutive_pairs(5, 3)  # 3 pairs
    cp4 = _consecutive_pairs(5, 4)  # 4 pairs
    assert not beats(cp4, cp3)
