import pytest

from risiko.core.shotgun.base import RisikoShotgun as ShotgunBase
from risiko.service.managers.player import PlayerManager
from risiko.service.managers.turn import TurnManager
from risiko.service.risiko_state import RisikoState


def test_risiko_state_creation():
    """Test that RisikoState can be instantiated with default values."""
    state = RisikoState()
    assert isinstance(state.shotgun, ShotgunBase)
    assert isinstance(state.player, PlayerManager)
    assert isinstance(state.turns, TurnManager)


def test_risiko_state_immutability():
    """Test that RisikoState attributes cannot be modified directly."""
    state = RisikoState()
    with pytest.raises(AttributeError):
        state.shotgun = ShotgunBase()
    with pytest.raises(AttributeError):
        state.player = PlayerManager()
    with pytest.raises(AttributeError):
        state.turns = TurnManager()
