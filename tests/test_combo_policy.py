import pytest
from dou_dizhu_simulator.agents.combo_policy import _get_protected_cards
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import Combination, CombType


def card(rank_val: int, suit: str) -> Card:
    return Card(Rank(rank_val), suit)


# ── triple / bomb ──────────────────────────────────────────────────────────

def test_triple_core_protected():
    hand = [card(7,'H'), card(7,'S'), card(7,'C'), card(12,'D')]
    p = _get_protected_cards(hand)
    assert card(7,'H') in p
    assert card(7,'S') in p
    assert card(7,'C') in p
    assert card(12,'D') not in p


def test_bomb_all_four_protected():
    hand = [card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D'), card(3,'H')]
    p = _get_protected_cards(hand)
    assert all(card(9, s) in p for s in ('H','S','C','D'))
    assert card(3,'H') not in p


# ── straight ───────────────────────────────────────────────────────────────

def test_straight_exactly_5_protected():
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S')]
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


def test_straight_4_not_protected():
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    p = _get_protected_cards(hand)
    assert len(p) == 0


def test_straight_7_protected():
    hand = [card(r,'H') for r in range(3, 10)]  # 3-9
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


def test_two_separate_straights_both_protected():
    # [3-7] and [9-K]: gap at 8
    hand = [card(r,'H') for r in [3,4,5,6,7,9,10,11,12,13]]
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


# ── consecutive pairs ─────────────────────────────────────────────────────

def test_consec_pairs_3_protected():
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D')]
    p = _get_protected_cards(hand)
    assert all(c in p for c in hand)


def test_consec_pairs_2_not_protected():
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'), card(9,'H')]
    p = _get_protected_cards(hand)
    assert len(p) == 0


def test_consec_pairs_standalone_pair_not_protected():
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D'), card(13,'H'), card(13,'S')]
    p = _get_protected_cards(hand)
    assert card(3,'H') in p
    assert card(13,'H') not in p
    assert card(13,'S') not in p


# ── high standalone pair soft-protection ──────────────────────────────────

def test_high_pair_protected_against_weak_trick():
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    p = _get_protected_cards(hand, last)
    assert card(13,'H') in p
    assert card(13,'S') in p
    assert card(3,'D') not in p


def test_high_pair_not_protected_against_strong_trick():
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]
    last = Combination(CombType.PAIR, (card(8,'H'), card(8,'S')), 8)
    p = _get_protected_cards(hand, last)
    assert len(p) == 0


def test_ace_pair_protected_against_weak_trick():
    hand = [card(14,'H'), card(14,'S')]
    last = Combination(CombType.PAIR, (card(7,'H'), card(7,'S')), 7)
    p = _get_protected_cards(hand, last)
    assert card(14,'H') in p
    assert card(14,'S') in p


def test_two_protected_against_weak_trick():
    hand = [card(15,'H'), card(15,'S')]
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    p = _get_protected_cards(hand, last)
    assert card(15,'H') in p
    assert card(15,'S') in p


def test_high_pair_protection_only_for_pair_trick():
    hand = [card(13,'H'), card(13,'S')]
    last = Combination(CombType.SINGLE, (card(5,'H'),), 5)
    p = _get_protected_cards(hand, last)
    assert len(p) == 0


from dou_dizhu_simulator.agents.combo_policy import ComboAwarePolicy
from dou_dizhu_simulator.game.rules import get_legal_moves


def policy() -> ComboAwarePolicy:
    return ComboAwarePolicy()


# ── LEADING FREELY ────────────────────────────────────────────────────────

def test_lead_straight_preferred_over_pair():
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S'),
            card(9,'H'), card(9,'S'), card(13,'D'), card(14,'C')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT


def test_lead_longest_straight_first():
    hand = [card(r,'H') for r in range(3, 10)] + [card(14,'S'), card(14,'H')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT
    assert len(move.cards) == 7


def test_lead_lower_rank_straight_first_same_length():
    hand = ([card(r,'H') for r in [3,4,5,6,7]] +
            [card(r,'S') for r in [9,10,11,12,13]] +
            [card(14,'C')])
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT
    assert move.rank_value == 7   # top card of [3-7] = 7


def test_lead_triple_pair_over_triple_single():
    hand = [card(5,'H'), card(5,'S'), card(5,'C'),
            card(9,'H'), card(9,'S'),
            card(3,'D'), card(4,'D'), card(7,'D'), card(8,'D'), card(13,'D')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.TRIPLE_PAIR


def test_lead_triple_single_over_plain_triple():
    hand = [card(5,'H'), card(5,'S'), card(5,'C'),
            card(3,'D'), card(4,'D'), card(7,'D'), card(8,'D'),
            card(11,'S'), card(13,'H')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.TRIPLE_SINGLE


def test_lead_pair_over_single():
    hand = [card(3,'H'), card(3,'S'),
            card(7,'C'), card(9,'D'), card(12,'H'), card(14,'S'), card(14,'C'), card(15,'D')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.PAIR
    assert move.rank_value == 3


def test_lead_consecutive_pairs_over_standalone_pair():
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D'), card(13,'H'), card(13,'S'), card(9,'C')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.CONSECUTIVE_PAIRS


def test_lead_lowest_single_when_no_combos():
    # All different ranks, no pairs, no straights — falls back to singles
    hand = [card(3,'H'), card(5,'S'), card(7,'C'), card(9,'D'), card(11,'H'), card(13,'S')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.SINGLE
    assert move.rank_value == 3


# ── FOLLOWING A TRICK ─────────────────────────────────────────────────────

def test_follow_plays_isolated_single_not_straight_card():
    # Hand [3,4,5,6,7,A]; opponent played SINGLE[6H]
    # 7 is in protected straight [34567]; A is isolated -> play A
    last = Combination(CombType.SINGLE, (card(6,'H'),), 6)
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S'), card(14,'C')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is not None
    assert move.cards[0] == card(14,'C')


def test_follow_pass_to_protect_straight():
    # Hand [3,4,5,6,7]; opponent played SINGLE[6H]
    # Only 7 can beat it, but 7 is in protected straight -> PASS
    last = Combination(CombType.SINGLE, (card(6,'H'),), 6)
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'S')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


def test_follow_pass_high_pair_vs_weak_pair():
    # Hand [KH, KS, 3D]; opponent played PAIR[55] (rank 5 <= 7) -> KK soft-protected -> PASS
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


def test_follow_play_high_pair_vs_strong_trick():
    # Hand [KH, KS, 3D]; opponent played PAIR[88] (rank 8 > 7) -> KK NOT protected -> play it
    last = Combination(CombType.PAIR, (card(8,'H'), card(8,'S')), 8)
    hand = [card(13,'H'), card(13,'S'), card(3,'D')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is not None
    assert move.type == CombType.PAIR
    assert move.rank_value == 13


def test_follow_prefers_standalone_pair_over_consec_pair_run():
    # consec pairs [33,44,55] all protected; KK standalone, rank 13 > 8 -> plays KK
    last = Combination(CombType.PAIR, (card(8,'H'), card(8,'S')), 8)
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'),
            card(5,'H'), card(5,'D'), card(13,'H'), card(13,'S'), card(9,'C')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is not None
    assert move.type == CombType.PAIR
    assert move.rank_value == 13


def test_follow_pass_when_all_pairs_in_consec_run():
    # consec pairs [77,88,99]; opponent played PAIR[66] -> all responses protected -> PASS
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


def test_follow_pass_preserves_bombs():
    # Following a BOMB: only JOKER_BOMB can beat it; non_bombs is empty -> PASS
    from dou_dizhu_simulator.game.card import Card, Rank
    sj = Card(Rank.SMALL_JOKER, 'J')
    bj = Card(Rank.BIG_JOKER, 'J')
    last = Combination(CombType.BOMB, (card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D')), 9)
    hand = [sj, bj, card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    legal = get_legal_moves(hand, last)
    move = policy().choose_move(hand, legal, last)
    assert move is None


# ── ENDGAME ───────────────────────────────────────────────────────────────

def test_endgame_maximises_card_count():
    # Hand <= 5; plays move with most cards
    hand = [card(3,'H'), card(3,'S'), card(4,'D'), card(4,'C'), card(5,'H')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert len(move.cards) >= 2


def test_endgame_plays_combo_over_single():
    # Hand [3,3,K]; plays pair[33] not single
    hand = [card(3,'H'), card(3,'S'), card(13,'D')]
    legal = get_legal_moves(hand, None)
    move = policy().choose_move(hand, legal, None)
    assert move.type == CombType.PAIR
    assert len(move.cards) == 2
