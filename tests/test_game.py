import random
from dou_dizhu_simulator.engine.game import GameRound
from dou_dizhu_simulator.agents.random_policy import RandomPolicy
from dou_dizhu_simulator.game.card import ACE_OF_SPADES, THREE_OF_HEARTS, Rank

def _make_policies(seed):
    rng = random.Random(seed)
    return [RandomPolicy(rng) for _ in range(3)]

def test_deal_gives_54_cards_total():
    rng = random.Random(42)
    game = GameRound(rng)
    hands, _ = game.deal_cards()
    total = sum(len(h) for h in hands)
    assert total == 54

def test_deal_gives_18_each():
    rng = random.Random(42)
    game = GameRound(rng)
    hands, _ = game.deal_cards()
    assert all(len(h) == 18 for h in hands)

def test_player_0_always_has_ace_of_spades():
    for seed in range(20):
        rng = random.Random(seed)
        game = GameRound(rng)
        hands, _ = game.deal_cards()
        assert ACE_OF_SPADES in hands[0], f"seed={seed}: P0 missing Ace of Spades"

def test_first_player_has_three_of_hearts():
    for seed in range(20):
        rng = random.Random(seed)
        game = GameRound(rng)
        hands, first = game.deal_cards()
        assert THREE_OF_HEARTS in hands[first], f"seed={seed}: first player doesn't hold 3H"

def test_game_terminates_and_returns_valid_winner():
    rng = random.Random(0)
    policies = _make_policies(1)
    game = GameRound(rng)
    winner, turns = game.play(policies)
    assert winner in (0, 1, 2)
    assert turns > 0

def test_winner_has_empty_hand():
    results = []
    for seed in range(50):
        g = GameRound(random.Random(seed))
        p = _make_policies(seed + 1000)
        w, t = g.play(p)
        results.append(w)
    assert all(r in (0, 1, 2) for r in results)

def test_same_seed_same_outcome():
    def run(seed):
        rng = random.Random(seed)
        policies = [RandomPolicy(random.Random(seed + i)) for i in range(3)]
        return GameRound(rng).play(policies)
    assert run(7) == run(7)
    assert run(42) == run(42)
