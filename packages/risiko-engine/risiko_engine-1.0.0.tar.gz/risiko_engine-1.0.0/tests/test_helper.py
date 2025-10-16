from collections import deque

import pytest
from attrs import evolve

from risiko.core.magazine.base import RisikoMagazine as MagazineBase
from risiko.core.player.base import RisikoPlayer
from risiko.core.player.exception import (
    PlayerIDNotFoundException,
)  # Assuming this exception exists
from risiko.core.shell.base import RisikoShell
from risiko.core.shotgun.base import RisikoShotgun
from risiko.service import helper
from risiko.service.managers.player import PlayerManager
from risiko.service.managers.turn import TurnManager
from risiko.service.risiko_state import RisikoState


@pytest.fixture
def player1():
    return RisikoPlayer(id="p1", charges=3)


@pytest.fixture
def player2():
    return RisikoPlayer(id="p2", charges=2)


@pytest.fixture
def player3():
    return RisikoPlayer(id="p3", charges=0)  # Dead player


@pytest.fixture
def live_shell():
    return RisikoShell(shell_type="live", damage=1)


@pytest.fixture
def blank_shell():
    return RisikoShell(shell_type="blank", damage=0)


@pytest.fixture
def initial_game_state(player1, player2):
    player_manager = PlayerManager().add_player(player1).add_player(player2)
    turn_manager = TurnManager(order=deque([player1.id, player2.id]))
    return RisikoState(player=player_manager, turns=turn_manager)


# --- Test cases for is_game_over ---
def test_is_game_over_false_multiple_players_alive(initial_game_state):
    assert not helper.is_game_over(initial_game_state)


def test_is_game_over_true_one_player_alive(initial_game_state, player1, player2):
    # Make player2 dead
    dead_player2 = evolve(player2, charges=0)
    dead_player_manager = initial_game_state.player.update_player(dead_player2)
    state_one_alive = evolve(initial_game_state, player=dead_player_manager)
    assert helper.is_game_over(state_one_alive)


def test_is_game_over_true_zero_players_alive(player1, player2):
    # Make all players dead
    dead_player1 = evolve(player1, charges=0)
    dead_player2 = evolve(player2, charges=0)
    player_manager_with_dead_players = (
        PlayerManager().add_player(dead_player1).add_player(dead_player2)
    )
    state_zero_alive = RisikoState(player=player_manager_with_dead_players)
    assert helper.is_game_over(state_zero_alive)


# --- Test cases for is_player_alive ---
def test_is_player_alive_true(initial_game_state, player1):
    assert helper.is_player_alive(initial_game_state, player1.id)


def test_is_player_alive_false(initial_game_state, player2):
    dead_player2 = evolve(player2, charges=0)
    dead_player_manager = initial_game_state.player.update_player(dead_player2)
    state_with_dead_player = evolve(initial_game_state, player=dead_player_manager)
    assert not helper.is_player_alive(state_with_dead_player, player2.id)


def test_is_player_alive_player_not_found(initial_game_state):
    with pytest.raises(
        PlayerIDNotFoundException
    ):  # Assuming PlayerNotFoundException is raised
        helper.is_player_alive(initial_game_state, "non_existent_player")


# --- Test cases for is_player_turn ---
def test_is_player_turn_true(initial_game_state, player1):
    assert helper.is_player_turn(initial_game_state, player1.id)


def test_is_player_turn_false(initial_game_state, player2):
    assert not helper.is_player_turn(initial_game_state, player2.id)


# --- Test cases for can_player_act ---
def test_can_player_act_true(initial_game_state, player1, live_shell):
    # Setup: player1's turn, player1 alive, shotgun loaded
    loaded_shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(initial_game_state, shotgun=loaded_shotgun)
    assert helper.can_player_act(state, player1.id)


def test_can_player_act_false_not_turn(initial_game_state, player2, live_shell):
    # Setup: player2 not turn, player2 alive, shotgun loaded
    loaded_shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(initial_game_state, shotgun=loaded_shotgun)
    assert not helper.can_player_act(state, player2.id)


def test_can_player_act_false_not_alive(initial_game_state, player1, live_shell):
    # Setup: player1's turn, player1 dead, shotgun loaded
    dead_player1 = evolve(player1, charges=0)
    dead_player_manager = initial_game_state.player.update_player(dead_player1)
    loaded_shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(
        initial_game_state, player=dead_player_manager, shotgun=loaded_shotgun
    )
    assert not helper.can_player_act(state, player1.id)  # player1 is now dead


def test_can_player_act_false_shotgun_not_loaded(initial_game_state, player1):
    # Setup: player1's turn, player1 alive, shotgun not loaded
    unloaded_shotgun = RisikoShotgun(chamber=None)
    state = evolve(initial_game_state, shotgun=unloaded_shotgun)
    assert not helper.can_player_act(state, player1.id)


# --- Test cases for can_load_shell ---
def test_can_load_shell_true(initial_game_state, live_shell):
    # Setup: chamber empty, magazine not empty
    magazine = MagazineBase().load_shell(live_shell)
    shotgun = RisikoShotgun(chamber=None, magazine=magazine)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert helper.can_load_shell(state)


def test_can_load_shell_false_chamber_not_empty(initial_game_state, live_shell):
    # Setup: chamber not empty, magazine not empty
    magazine = MagazineBase().load_shell(live_shell)
    shotgun = RisikoShotgun(chamber=live_shell, magazine=magazine)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert not helper.can_load_shell(state)


def test_can_load_shell_false_magazine_empty(initial_game_state):
    # Setup: chamber empty, magazine empty
    shotgun = RisikoShotgun(chamber=None, magazine=MagazineBase())
    state = evolve(initial_game_state, shotgun=shotgun)
    assert not helper.can_load_shell(state)


# --- Test cases for can_fire_shotgun ---
def test_can_fire_shotgun_true(initial_game_state, live_shell):
    # Setup: chamber not empty
    shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert helper.can_fire_shotgun(state)


def test_can_fire_shotgun_false(initial_game_state):
    # Setup: chamber empty
    shotgun = RisikoShotgun(chamber=None)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert not helper.can_fire_shotgun(state)


# --- Test cases for can_clear_magazine ---
def test_can_clear_magazine_true(initial_game_state, live_shell):
    # Setup: magazine not empty
    magazine = MagazineBase().load_shell(live_shell)
    shotgun = RisikoShotgun(magazine=magazine)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert helper.can_clear_magazine(state)


def test_can_clear_magazine_false(initial_game_state):
    # Setup: magazine empty
    shotgun = RisikoShotgun(magazine=MagazineBase())
    state = evolve(initial_game_state, shotgun=shotgun)
    assert not helper.can_clear_magazine(state)


# --- Test cases for is_magazine_empty ---
def test_is_magazine_empty_true(initial_game_state):
    shotgun = RisikoShotgun(magazine=MagazineBase())
    state = evolve(initial_game_state, shotgun=shotgun)
    assert helper.is_magazine_empty(state)


def test_is_magazine_empty_false(initial_game_state, live_shell):
    magazine = MagazineBase().load_shell(live_shell)
    shotgun = RisikoShotgun(magazine=magazine)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert not helper.is_magazine_empty(state)


# --- Test cases for is_chamber_empty ---
def test_is_chamber_empty_true(initial_game_state):
    shotgun = RisikoShotgun(chamber=None)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert helper.is_chamber_empty(state)


def test_is_chamber_empty_false(initial_game_state, live_shell):
    shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(initial_game_state, shotgun=shotgun)
    assert not helper.is_chamber_empty(state)


# --- Test cases for is_valid_target ---
def test_is_valid_target_true(initial_game_state, player2):
    # player2 is alive and not current player (player1)
    assert helper.is_valid_target(initial_game_state, player2.id)


def test_is_valid_target_false_dead_player(initial_game_state, player1, player2):
    # player2 is dead
    dead_player2 = evolve(player2, charges=0)
    dead_player_manager = initial_game_state.player.update_player(dead_player2)
    state = evolve(initial_game_state, player=dead_player_manager)
    assert not helper.is_valid_target(state, player2.id)


def test_is_valid_target_false_current_player(initial_game_state, player1):
    # player1 is current player
    assert not helper.is_valid_target(initial_game_state, player1.id)


def test_is_valid_target_player_not_found(initial_game_state):
    with pytest.raises(
        PlayerIDNotFoundException
    ):  # Assuming PlayerNotFoundException is raised
        helper.is_valid_target(initial_game_state, "non_existent_player")


# --- Test cases for can_start_game ---
def test_can_start_game_true(initial_game_state):
    # 2 players
    assert helper.can_start_game(initial_game_state)


def test_can_start_game_false_one_player(player1):
    player_manager = PlayerManager().add_player(player1)
    state = RisikoState(player=player_manager)
    assert not helper.can_start_game(state)


def test_can_start_game_false_zero_players():
    state = RisikoState(player=PlayerManager())
    assert not helper.can_start_game(state)
