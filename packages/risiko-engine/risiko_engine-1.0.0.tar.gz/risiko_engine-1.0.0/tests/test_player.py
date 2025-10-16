import pytest

from risiko.core.player.base import RisikoPlayer as PlayerBase
from risiko.core.player.exception import PlayerDeadException


@pytest.fixture
def player():
    return PlayerBase(id="player1", charges=3)


def test_player_creation():
    """Test that a PlayerBase can be instantiated with valid properties."""
    p = PlayerBase(id="test", charges=5)
    assert p.id == "test"
    assert p.charges == 5


def test_create_player_with_negative_charges_raises_exception():
    """Test that creating a player with negative charges raises a ValueError."""
    with pytest.raises(ValueError):
        PlayerBase(id="test", charges=-1)


def test_lose_charges_normal(player):
    """Test losing a normal amount of charges."""
    new_player = player.lose_charges(1)
    assert new_player.charges == 2


def test_lose_charges_more_than_available(player):
    """Test that losing more charges than available results in 0 charges."""
    new_player = player.lose_charges(5)
    assert new_player.charges == 0


def test_lose_charges_when_dead_raises_exception():
    """Test that losing charges when already at 0 raises PlayerDeadException."""
    dead_player = PlayerBase(id="dead", charges=0)
    with pytest.raises(PlayerDeadException):
        dead_player.lose_charges(1)


def test_lose_negative_charges_raises_exception(player):
    """Test that losing a negative amount of charges raises a ValueError."""
    with pytest.raises(ValueError):
        player.lose_charges(-1)


def test_gain_charges_normal(player):
    """Test gaining a normal amount of charges."""
    new_player = player.gain_charges(2)
    assert new_player.charges == 5


def test_gain_negative_charges_raises_exception(player):
    """Test that gaining a negative amount of charges raises a ValueError."""
    with pytest.raises(ValueError):
        player.gain_charges(-1)


def test_lose_charges_exactly_to_zero(player):
    """Test losing exactly the amount of charges to reach zero."""
    player_with_one_charge = PlayerBase(id="player_one", charges=1)
    new_player = player_with_one_charge.lose_charges(1)
    assert new_player.charges == 0


def test_gain_zero_charges(player):
    """Test gaining zero charges should not change the player's charges."""
    new_player = player.gain_charges(0)
    assert new_player.charges == player.charges
    assert (
        new_player == player
    )  # Due to immutability, if no change, should be same object
