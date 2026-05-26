from dou_dizhu_simulator.game.card import (
    Card, Rank, ACE_OF_SPADES, THREE_OF_HEARTS, make_deck
)

def test_deck_has_54_cards():
    assert len(make_deck()) == 54

def test_deck_no_duplicates():
    deck = make_deck()
    assert len(set(deck)) == 54

def test_deck_contains_ace_of_spades():
    assert ACE_OF_SPADES in make_deck()

def test_deck_contains_three_of_hearts():
    assert THREE_OF_HEARTS in make_deck()

def test_rank_ordering():
    assert Rank.THREE < Rank.ACE < Rank.TWO < Rank.SMALL_JOKER < Rank.BIG_JOKER

def test_card_is_immutable():
    import pytest
    with pytest.raises(Exception):
        ACE_OF_SPADES.rank = Rank.TWO

def test_ace_of_spades_identity():
    deck = make_deck()
    aces_spades = [c for c in deck if c.rank == Rank.ACE and c.suit == 'S']
    assert len(aces_spades) == 1
    assert aces_spades[0] == ACE_OF_SPADES
