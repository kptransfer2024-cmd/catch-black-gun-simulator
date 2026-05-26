import pytest
from dou_dizhu_simulator.agents.coalition_refined_policy import CoalitionRefinedPolicy, _BOMB_DEPLOY_THRESHOLD
from dou_dizhu_simulator.agents.tactical_policy import TacticalPolicy
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import Combination, CombType
from dou_dizhu_simulator.game.rules import get_legal_moves


def card(rank_val: int, suit: str) -> Card:
    return Card(Rank(rank_val), suit)


# ── Feature 2: Tempo transfer ─────────────────────────────────────────────────

def test_sacrificer_leads_cheap_single_not_combo():
    # P1 has 9 cards (more than partner P2's 5) → P1 is sacrificer
    # Hand has a pair of 9s and scattered singles; sacrificer should lead cheapest single
    hand = [card(3,'C'), card(9,'H'), card(9,'S'), card(12,'H'), card(14,'C'),
            card(5,'D'), card(6,'H'), card(8,'C'), card(11,'D')]
    legal = get_legal_moves(hand, None)
    # opp_sizes for P1: [P2_size, P0_size] = [5, 10]
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, None, [5, 10], ace_revealed=True
    )
    assert move is not None
    assert move.type == CombType.SINGLE
    assert move.rank_value == 3  # cheapest unprotected single


def test_priority_player_leads_combo_not_single():
    # P1 has 6 cards (fewer than partner P2's 10) → P1 is priority
    # Priority player should lead normally (best combo first)
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'), card(9,'H'), card(9,'S')]
    legal = get_legal_moves(hand, None)
    # opp_sizes for P1: [P2_size, P0_size] = [10, 15]
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, None, [10, 15], ace_revealed=True
    )
    assert move is not None
    assert move.type == CombType.STRAIGHT  # leads straight (best combo)


# ── Feature 3: Selective coalition bombing ────────────────────────────────────

def test_sacrificer_uses_bomb_to_beat_p0_regular_move():
    # P1 has more cards than P2 → P1 is sacrificer
    # P0 leads pair of 5s; P1 has bomb of 3s and pair of 7s
    # Sacrificer should use bomb (rank 3 < pair rank 7)
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    hand = [card(3,'H'), card(3,'S'), card(3,'C'), card(3,'D'),   # bomb of 3s
            card(7,'H'), card(7,'S'),                              # pair of 7s
            card(10,'C'), card(11,'D'), card(12,'H')]              # singles, 9 cards total
    legal = get_legal_moves(hand, last)
    # opp_sizes for P1 (idx=1): [P2_size=5, P0_size=12]
    # P1 has 9 cards > P2's 5 → sacrificer
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, last, [5, 12], ace_revealed=True, last_player_idx=0
    )
    assert move is not None
    assert move.type == CombType.BOMB
    assert move.rank_value == 3  # minimum bomb used


def test_priority_player_saves_bomb_when_p0_far():
    # P1 has fewer cards than P2 → P1 is priority
    # P0 has many cards (> BOMB_DEPLOY_THRESHOLD) → priority player saves bomb
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    hand = [card(3,'H'), card(3,'S'), card(3,'C'), card(3,'D'),   # bomb of 3s
            card(7,'H'), card(7,'S'),                              # pair of 7s
            card(10,'C'), card(11,'D')]                            # singles, 8 cards total
    legal = get_legal_moves(hand, last)
    # opp_sizes for P1: [P2_size=10, P0_size=15]
    # P1 has 8 cards < P2's 10 → priority player; P0 has 15 cards > BOMB_DEPLOY_THRESHOLD
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, last, [10, 15], ace_revealed=True, last_player_idx=0
    )
    assert move is not None
    assert move.type == CombType.PAIR   # uses pair of 7s, saves bomb
    assert move.rank_value == 7


def test_priority_player_deploys_bomb_when_p0_close():
    # P1 is priority but P0 has <= BOMB_DEPLOY_THRESHOLD cards → use bomb
    last = Combination(CombType.PAIR, (card(5,'H'), card(5,'S')), 5)
    hand = [card(3,'H'), card(3,'S'), card(3,'C'), card(3,'D'),   # bomb of 3s
            card(7,'H'), card(7,'S'),                              # pair of 7s
            card(10,'C'), card(11,'D')]                            # singles, 8 cards total
    legal = get_legal_moves(hand, last)
    # opp_sizes for P1: [P2_size=10, P0_size=BOMB_DEPLOY_THRESHOLD]
    # P1 has 8 < P2's 10 → priority; but P0 is at threshold → deploy bomb
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, last, [10, _BOMB_DEPLOY_THRESHOLD], ace_revealed=True, last_player_idx=0
    )
    assert move is not None
    assert move.type == CombType.BOMB


# ── Feature 1: Priority determines role ──────────────────────────────────────

def test_equal_hand_sizes_treated_as_priority():
    # Tie in hand sizes → i_am_priority=True (len <= partner_size) → lead normally
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'),
            card(9,'H'), card(9,'S')]
    legal = get_legal_moves(hand, None)
    # opp_sizes for P1: [P2_size=7, P0_size=15] (equal hand sizes)
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, None, [7, 15], ace_revealed=True
    )
    assert move is not None
    assert move.type == CombType.STRAIGHT  # leads combo (priority behavior)


def test_p2_priority_protocol_correct_partner_index():
    # P2 (idx=2): partner = P1, which is opp_sizes[1]
    # opp_sizes for P2: [P0_size, P1_size] = [15, 5]
    # P2 has 9 cards > P1's 5 → P2 is sacrificer → tempo transfer
    hand = [card(3,'C'), card(9,'H'), card(9,'S'), card(12,'H'), card(14,'C'),
            card(5,'D'), card(6,'H'), card(8,'C'), card(11,'D')]
    legal = get_legal_moves(hand, None)
    move = CoalitionRefinedPolicy(2).choose_move(
        hand, legal, None, [15, 5], ace_revealed=True
    )
    assert move is not None
    assert move.type == CombType.SINGLE
    assert move.rank_value == 3


# ── Inherited behavior still works ───────────────────────────────────────────

def test_p0_danger_overrides_all():
    # P0 has <= 3 cards → play max regardless of priority/sacrifice
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, None)
    move = CoalitionRefinedPolicy(1).choose_move(
        hand, legal, None, [15, 3], ace_revealed=True
    )
    assert move is not None
    assert len(move.cards) == max(len(m.cards) for m in legal)


def test_before_ace_revealed_acts_like_tactical():
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'),
            card(9,'H'), card(9,'S'), card(14,'C')]
    legal = get_legal_moves(hand, None)
    refined = CoalitionRefinedPolicy(1)
    tactical = TacticalPolicy()
    assert refined.choose_move(hand, legal, None, [10, 15], ace_revealed=False) == \
           tactical.choose_move(hand, legal, None, [10, 15])
