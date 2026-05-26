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


# ── Danger mode ───────────────────────────────────────────────────────────────

def test_danger_mode_overrides_protection_when_following():
    # Consec pairs [77,88,99] are all protected; following PAIR[6H,6S]
    # Without danger mode → PASS; with danger mode (opponent has 2 cards) → plays a pair
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)

    assert TacticalPolicy().choose_move(hand, legal, last, [15, 15]) is None
    move = TacticalPolicy().choose_move(hand, legal, last, [2, 15])
    assert move is not None
    assert move.type == CombType.PAIR


def test_danger_mode_uses_bomb_when_following():
    # Only a JOKER_BOMB can beat opponent's BOMB; normally saves bombs
    # In danger mode: plays the joker bomb
    from dou_dizhu_simulator.game.card import Card, Rank
    sj = Card(Rank.SMALL_JOKER, 'J')
    bj = Card(Rank.BIG_JOKER, 'J')
    last = Combination(CombType.BOMB,
        (card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D')), 9)
    hand = [sj, bj, card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    legal = get_legal_moves(hand, last)

    assert TacticalPolicy().choose_move(hand, legal, last, [15, 15]) is None
    move = TacticalPolicy().choose_move(hand, legal, last, [2, 15])
    assert move is not None
    assert move.type == CombType.JOKER_BOMB


def test_danger_mode_leads_with_bomb():
    # Free lead; hand has bomb + isolated singles; normally never leads with bomb
    # In danger mode: max(key=len) picks the 4-card bomb over 1-card singles
    hand = [card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D'),
            card(3,'H'), card(5,'C'), card(7,'D')]
    legal = get_legal_moves(hand, None)

    move_safe = TacticalPolicy().choose_move(hand, legal, None, [15, 15])
    assert move_safe.type != CombType.BOMB

    move_danger = TacticalPolicy().choose_move(hand, legal, None, [3, 15])
    assert move_danger.type == CombType.BOMB


def test_danger_mode_inactive_without_sizes():
    # When opponent_hand_sizes is None, no danger mode — same as ComboAwarePolicy
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)
    assert TacticalPolicy().choose_move(hand, legal, last) is None


def test_danger_threshold_boundary():
    # Opponent with exactly 4 cards does NOT trigger danger; exactly 3 does
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)
    assert TacticalPolicy().choose_move(hand, legal, last, [4, 15]) is None
    assert TacticalPolicy().choose_move(hand, legal, last, [3, 15]) is not None
