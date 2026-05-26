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
