from collections import deque

import pytest

from risiko.core.player.base import RisikoPlayer as PlayerBase
from risiko.core.player.exception import (
    PlayerIDExistsException,
    PlayerIDNotFoundException,
)
from risiko.service.managers.player import PlayerManager
from risiko.service.managers.turn import TurnManager
from risiko.service.processors import player_management as player_management_processor
from risiko.service.risiko_state import RisikoState


@pytest.fixture
def player1():
    return PlayerBase(id="p1", charges=3)


@pytest.fixture
def player2():
    return PlayerBase(id="p2", charges=2)


@pytest.fixture
def initial_game_state():
    return RisikoState()


@pytest.fixture
def game_state_with_players(player1, player2):
    player_manager = PlayerManager().add_player(player1).add_player(player2)
    turn_manager = TurnManager(order=deque([player1.id, player2.id]))
    return RisikoState(player=player_manager, turns=turn_manager)


# --- Test cases for add_player_to_game ---
def test_add_player_to_game_success_empty_state(initial_game_state):
    new_player = PlayerBase(id="new_p", charges=5)
    new_state = player_management_processor.add_player_to_game(
        initial_game_state, new_player
    )
    assert new_state.player.get_player("new_p").charges == 5
    assert new_state.turns.turn_order == ("new_p",)


def test_add_player_to_game_success_with_existing_players(game_state_with_players):
    new_player = PlayerBase(id="new_p", charges=5)
    new_state = player_management_processor.add_player_to_game(
        game_state_with_players, new_player
    )
    assert new_state.player.get_player("new_p").charges == 5
    assert new_state.turns.turn_order == ("p1", "p2", "new_p")


def test_add_player_to_game_duplicate_id_raises_exception(game_state_with_players):
    duplicate_player = PlayerBase(id="p1", charges=5)
    with pytest.raises(PlayerIDExistsException):
        player_management_processor.add_player_to_game(
            game_state_with_players, duplicate_player
        )


def test_add_player_to_game_negative_charges_raises_value_error(initial_game_state):
    with pytest.raises(ValueError):
        # The ValueError should now be raised by PlayerBase during its creation
        # before add_player_to_game is even called.
        # This test now verifies that PlayerBase itself prevents negative charges.
        player_management_processor.add_player_to_game(
            initial_game_state, PlayerBase(id="new_p", charges=-1)
        )


# --- Test cases for remove_player_from_game ---
def test_remove_player_from_game_success(game_state_with_players):
    new_state = player_management_processor.remove_player_from_game(
        game_state_with_players, "p1"
    )
    with pytest.raises(PlayerIDNotFoundException):
        new_state.player.get_player("p1")
    assert new_state.turns.turn_order == ("p2",)


def test_remove_player_from_game_non_existent_raises_exception(game_state_with_players):
    with pytest.raises(PlayerIDNotFoundException):
        player_management_processor.remove_player_from_game(
            game_state_with_players, "non_existent_p"
        )
