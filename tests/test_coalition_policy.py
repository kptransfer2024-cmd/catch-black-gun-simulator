import pytest
from dou_dizhu_simulator.agents.coalition_policy import CoalitionPolicy
from dou_dizhu_simulator.agents.tactical_policy import TacticalPolicy
from dou_dizhu_simulator.game.card import Card, Rank
from dou_dizhu_simulator.game.combination import Combination, CombType
from dou_dizhu_simulator.game.rules import get_legal_moves
from dou_dizhu_simulator.experiments.runner import MonteCarloSimulator


def card(rank_val: int, suit: str) -> Card:
    return Card(Rank(rank_val), suit)


# ── Before ace is revealed: behaves like TacticalPolicy ──────────────────────

def test_coalition_inactive_before_ace_revealed():
    # P1 hasn't seen ace — should behave identically to TacticalPolicy
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'),
            card(9,'H'), card(9,'S'), card(14,'C')]
    legal = get_legal_moves(hand, None)
    coalition = CoalitionPolicy(1)
    tactical = TacticalPolicy()
    assert coalition.choose_move(hand, legal, None, [18, 18], ace_revealed=False) == \
           tactical.choose_move(hand, legal, None, [18, 18])


def test_p0_always_acts_like_tactical():
    # P0 (player_idx=0) ignores coalition mode even when ace_revealed=True
    hand = [card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D'), card(7,'H'),
            card(9,'H'), card(9,'S'), card(14,'C')]
    legal = get_legal_moves(hand, None)
    coalition_p0 = CoalitionPolicy(0)
    tactical = TacticalPolicy()
    move_c = coalition_p0.choose_move(hand, legal, None, [18, 18], ace_revealed=True)
    move_t = tactical.choose_move(hand, legal, None, [18, 18])
    assert move_c == move_t


# ── Coalition: pass when partner holds the trick ──────────────────────────────

def test_p1_passes_when_partner_holds_trick():
    # last_player_idx=2 (P2, the partner, holds trick): P1 should pass
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(9,'H'), card(9,'S'), card(3,'C'), card(5,'D'), card(10,'H'), card(11,'S')]
    legal = get_legal_moves(hand, last)
    move = CoalitionPolicy(1).choose_move(
        hand, legal, last, [4, 10], ace_revealed=True, last_player_idx=2
    )
    assert move is None


def test_p2_passes_when_partner_holds_trick():
    # last_player_idx=1 (P1, the partner, holds trick): P2 should pass
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(9,'H'), card(9,'S'), card(3,'C'), card(5,'D'), card(10,'H'), card(11,'S')]
    legal = get_legal_moves(hand, last)
    move = CoalitionPolicy(2).choose_move(
        hand, legal, last, [10, 4], ace_revealed=True, last_player_idx=1
    )
    assert move is None


# ── Coalition: beat P0 aggressively when P0 holds the trick ──────────────────

def test_p1_beats_p0_ignoring_protection():
    # P0 leads a pair of 6s; P1 has a protected pair of 7s (part of consec 7-8-9)
    # Normal follow would pass (protection); coalition beats P0 anyway
    last = Combination(CombType.PAIR, (card(6,'H'), card(6,'S')), 6)
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, last)

    # TacticalPolicy would pass (all pairs are protected)
    assert TacticalPolicy().choose_move(hand, legal, last, [15, 15]) is None

    # CoalitionPolicy beats P0 with minimum pair
    move = CoalitionPolicy(1).choose_move(
        hand, legal, last, [15, 15], ace_revealed=True, last_player_idx=0
    )
    assert move is not None
    assert move.type == CombType.PAIR
    assert move.rank_value == 7  # minimum pair that beats 6


def test_coalition_uses_bomb_to_beat_p0_when_only_option():
    # P0 plays a BOMB; only a JOKER_BOMB can beat it
    # Normal follow would pass (save bombs); coalition uses joker bomb
    sj = Card(Rank.SMALL_JOKER, 'J')
    bj = Card(Rank.BIG_JOKER, 'J')
    last = Combination(CombType.BOMB,
        (card(9,'H'), card(9,'S'), card(9,'C'), card(9,'D')), 9)
    hand = [sj, bj, card(3,'H'), card(4,'S'), card(5,'C'), card(6,'D')]
    legal = get_legal_moves(hand, last)

    assert TacticalPolicy().choose_move(hand, legal, last, [15, 15]) is None

    move = CoalitionPolicy(1).choose_move(
        hand, legal, last, [15, 15], ace_revealed=True, last_player_idx=0
    )
    assert move is not None
    assert move.type == CombType.JOKER_BOMB


# ── Finish-fast overrides ─────────────────────────────────────────────────────

def test_p0_danger_triggers_finish_fast():
    # P0 has 3 cards (danger); P1 should dump most cards at once
    hand = [card(7,'H'), card(7,'S'), card(8,'D'), card(8,'C'),
            card(9,'H'), card(9,'D'), card(3,'C')]
    legal = get_legal_moves(hand, None)
    # For P1 (idx=1): opp_sizes[1] = P0 size = 3
    move = CoalitionPolicy(1).choose_move(
        hand, legal, None, [15, 3], ace_revealed=True, last_player_idx=None
    )
    assert move is not None
    assert len(move.cards) == max(len(m.cards) for m in legal)


def test_own_hand_small_triggers_finish_fast():
    # Own hand ≤ 5 → play max cards regardless of coalition state
    hand = [card(9,'H'), card(9,'S'), card(9,'C'), card(3,'D'), card(5,'H')]
    legal = get_legal_moves(hand, None)
    move = CoalitionPolicy(1).choose_move(
        hand, legal, None, [15, 15], ace_revealed=True
    )
    assert move is not None
    assert len(move.cards) == max(len(m.cards) for m in legal)


# ── Runner accepts list of 3 factories ───────────────────────────────────────

def test_runner_accepts_factory_list():
    factories = [
        lambda _rng: TacticalPolicy(),
        lambda _rng: CoalitionPolicy(1),
        lambda _rng: CoalitionPolicy(2),
    ]
    results = MonteCarloSimulator(factories).run(50, seed=0)
    assert results.n_games == 50
    assert sum(results.wins) == 50


def test_runner_single_factory_still_works():
    results = MonteCarloSimulator(lambda _rng: TacticalPolicy()).run(20, seed=0)
    assert results.n_games == 20
    assert sum(results.wins) == 20
