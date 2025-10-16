from collections import deque

import pytest

from risiko.core.player.base import RisikoPlayer as PlayerBase
from risiko.core.player.exception import PlayerDeadException, PlayerIDNotFoundException
from risiko.service.managers.player import PlayerManager
from risiko.service.managers.turn import TurnManager
from risiko.service.processors import player_state as player_state_processor
from risiko.service.risiko_state import RisikoState


@pytest.fixture
def player1():
    return PlayerBase(id="p1", charges=3)


@pytest.fixture
def player2():
    return PlayerBase(id="p2", charges=1)


@pytest.fixture
def player3_dead():
    return PlayerBase(id="p3", charges=0)


@pytest.fixture
def initial_game_state():
    return RisikoState()


@pytest.fixture
def game_state_with_players(player1, player2, player3_dead):
    player_manager = (
        PlayerManager().add_player(player1).add_player(player2).add_player(player3_dead)
    )
    turn_manager = TurnManager(order=deque([player1.id, player2.id, player3_dead.id]))
    return RisikoState(player=player_manager, turns=turn_manager)


# --- Test cases for player_lose_charges ---
def test_player_lose_charges_success_player_alive(game_state_with_players, player1):
    new_state = player_state_processor.player_lose_charges(
        game_state_with_players, player1.id, 1
    )
    updated_player = new_state.player.get_player(player1.id)
    assert updated_player.charges == 2


def test_player_lose_charges_success_player_becomes_dead(
    game_state_with_players, player2
):
    new_state = player_state_processor.player_lose_charges(
        game_state_with_players, player2.id, 1
    )
    updated_player = new_state.player.get_player(player2.id)
    assert updated_player.charges == 0


def test_player_lose_charges_non_existent_player_raises_exception(
    game_state_with_players,
):
    with pytest.raises(PlayerIDNotFoundException):
        player_state_processor.player_lose_charges(
            game_state_with_players, "non_existent_p", 1
        )


def test_player_lose_charges_player_already_dead_raises_exception(
    game_state_with_players, player3_dead
):
    with pytest.raises(PlayerDeadException):
        player_state_processor.player_lose_charges(
            game_state_with_players, player3_dead.id, 1
        )


def test_player_lose_charges_negative_amount_raises_value_error(
    game_state_with_players, player1
):
    with pytest.raises(ValueError):
        player_state_processor.player_lose_charges(
            game_state_with_players, player1.id, -1
        )


# --- Test cases for player_gain_charges ---
def test_player_gain_charges_success(game_state_with_players, player1):
    new_state = player_state_processor.player_gain_charges(
        game_state_with_players, player1.id, 2
    )
    updated_player = new_state.player.get_player(player1.id)
    assert updated_player.charges == 5


def test_player_gain_charges_non_existent_player_raises_exception(
    game_state_with_players,
):
    with pytest.raises(PlayerIDNotFoundException):
        player_state_processor.player_gain_charges(
            game_state_with_players, "non_existent_p", 1
        )


def test_player_gain_charges_negative_amount_raises_value_error(
    game_state_with_players, player1
):
    with pytest.raises(ValueError):
        player_state_processor.player_gain_charges(
            game_state_with_players, player1.id, -1
        )
