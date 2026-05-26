import pytest
from dou_dizhu_simulator.agents.tactical_policy import TacticalPolicy, _kicker_cards, _smart_lead_key
from dou_dizhu_simulator.agents.combo_policy import _get_protected_cards
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import Combination, CombType
from dou_dizhu_simulator.game.rules import get_legal_moves


def card(rank_val: int, suit: str) -> Card:
    return Card(Rank(rank_val), suit)


# ── _kicker_cards ─────────────────────────────────────────────────────────────

def test_kicker_cards_triple_single():
    triple = (card(5,'H'), card(5,'S'), card(5,'C'))
    combo = Combination(CombType.TRIPLE_SINGLE, triple + (card(13,'D'),), 5)
    assert _kicker_cards(combo) == [card(13,'D')]


def test_kicker_cards_triple_pair():
    triple = (card(5,'H'), card(5,'S'), card(5,'C'))
    combo = Combination(CombType.TRIPLE_PAIR, triple + (card(13,'D'), card(13,'H')), 5)
    kickers = _kicker_cards(combo)
    assert len(kickers) == 2
    assert all(int(c.rank) == 13 for c in kickers)


# ── _smart_lead_key ───────────────────────────────────────────────────────────

def test_smart_lead_key_unprotected_kicker_sorts_first():
    triple = (card(9,'H'), card(9,'S'), card(9,'C'))
    protected = {card(7,'H')}
    combo_protected = Combination(CombType.TRIPLE_SINGLE, triple + (card(7,'H'),), 9)
    combo_unprotected = Combination(CombType.TRIPLE_SINGLE, triple + (card(14,'C'),), 9)
    assert _smart_lead_key(combo_unprotected, protected) < _smart_lead_key(combo_protected, protected)


def test_smart_lead_key_straight_still_beats_triple():
    protected = set()
    straight = Combination(CombType.STRAIGHT,
        (card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H')), 7)
    triple_single = Combination(CombType.TRIPLE_SINGLE,
        (card(9,'H'), card(9,'S'), card(9,'C'), card(14,'C')), 9)
    assert _smart_lead_key(straight, protected) < _smart_lead_key(triple_single, protected)


def test_smart_lead_key_non_kicker_combo_unchanged():
    protected = set()
    pair_low = Combination(CombType.PAIR, (card(3,'H'), card(3,'S')), 3)
    pair_high = Combination(CombType.PAIR, (card(9,'H'), card(9,'S')), 9)
    assert _smart_lead_key(pair_low, protected) < _smart_lead_key(pair_high, protected)


# ── TacticalPolicy._lead integration ─────────────────────────────────────────

def test_lead_picks_unprotected_kicker_over_protected():
    # Hand: triple 9s + straight [3-7] (protects 3,4,5,6,7) + isolated A
    # Pass only TRIPLE_SINGLE combos to _lead to isolate kicker-selection logic.
    hand = [card(9,'H'), card(9,'S'), card(9,'C'),
            card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'),
            card(14,'C')]
    triple = (card(9,'H'), card(9,'S'), card(9,'C'))
    combo_protected_kicker = Combination(CombType.TRIPLE_SINGLE, triple + (card(7,'H'),), 9)
    combo_unprotected_kicker = Combination(CombType.TRIPLE_SINGLE, triple + (card(14,'C'),), 9)

    policy = TacticalPolicy()
    move = policy._lead(hand, [combo_protected_kicker, combo_unprotected_kicker])
    assert move == combo_unprotected_kicker


def test_lead_normal_behavior_inherited():
    # Without special scenario, TacticalPolicy leads with straight (cat 0 priority)
    hand = ([card(r,'H') for r in [3,4,5,6,7]] +
            [card(9,'H'), card(9,'S'), card(14,'C'), card(3,'S')])
    legal = get_legal_moves(hand, None)
    move = TacticalPolicy().choose_move(hand, legal, None)
    assert move.type == CombType.STRAIGHT
