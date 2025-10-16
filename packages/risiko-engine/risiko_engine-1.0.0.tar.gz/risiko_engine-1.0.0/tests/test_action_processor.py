from collections import deque

import pytest
from attrs import evolve

from risiko.core.player.base import RisikoPlayer
from risiko.core.player.exception import PlayerDeadException, PlayerInvalidTurnException
from risiko.core.shell.base import RisikoShell
from risiko.core.shotgun.base import RisikoShotgun
from risiko.core.shotgun.exception import (
    ShotgunUnLoadedException,
)  # For when shotgun is empty
from risiko.service.managers.player import PlayerManager
from risiko.service.managers.turn import TurnManager
from risiko.service.processors import action
from risiko.service.risiko_state import RisikoState


@pytest.fixture
def player1():
    return RisikoPlayer(id="p1", charges=3)


@pytest.fixture
def player2():
    return RisikoPlayer(id="p2", charges=2)


@pytest.fixture
def player3_dead():
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


# --- Test cases for fire_shell ---
def test_fire_shell_success(initial_game_state, player1, live_shell):
    # Setup: player1's turn, player1 alive, shotgun loaded
    loaded_shotgun = RisikoShotgun(chamber=live_shell)
    state_with_loaded_shotgun = evolve(initial_game_state, shotgun=loaded_shotgun)

    fired_shell, new_state = action.fire_shell(state_with_loaded_shotgun, player1.id)
    assert fired_shell == live_shell
    assert new_state.shotgun.chamber is None


def test_fire_shell_shooter_dead_raises_exception(
    initial_game_state, player3_dead, live_shell
):
    # Setup: player3_dead's turn, player3_dead dead, shotgun loaded
    player_manager_with_dead = initial_game_state.player.add_player(
        player3_dead
    ).update_player(player3_dead)
    turn_manager_dead_player_turn = TurnManager(
        order=deque([player3_dead.id, initial_game_state.turns.current_player_id])
    )
    loaded_shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(
        initial_game_state,
        player=player_manager_with_dead,
        turns=turn_manager_dead_player_turn,
        shotgun=loaded_shotgun,
    )

    with pytest.raises(PlayerDeadException):
        action.fire_shell(state, player3_dead.id)


def test_fire_shell_not_shooters_turn_raises_exception(
    initial_game_state, player2, live_shell
):
    # Setup: player2 not turn, player2 alive, shotgun loaded
    loaded_shotgun = RisikoShotgun(chamber=live_shell)
    state = evolve(initial_game_state, shotgun=loaded_shotgun)

    with pytest.raises(PlayerInvalidTurnException):
        action.fire_shell(state, player2.id)


def test_fire_shell_shotgun_empty_raises_exception(initial_game_state, player1):
    # Setup: player1's turn, player1 alive, shotgun empty
    empty_shotgun = RisikoShotgun(chamber=None)
    state = evolve(initial_game_state, shotgun=empty_shotgun)

    with pytest.raises(
        ShotgunUnLoadedException
    ):  # This exception comes from RisikoShotgun.fire()
        action.fire_shell(state, player1.id)


# --- Test cases for hit_shell ---
def test_hit_shell_success_target_loses_charges(
    initial_game_state, player2, live_shell
):
    # Setup: player2 has 2 charges, live_shell has 1 damage
    new_state = action.hit_shell(initial_game_state, player2.id, live_shell)
    updated_player2 = new_state.player.get_player(player2.id)
    assert updated_player2.charges == 1


def test_hit_shell_target_dead_raises_exception(
    initial_game_state, player3_dead, live_shell
):
    # Setup: player3_dead is dead
    player_manager_with_dead = initial_game_state.player.add_player(
        player3_dead
    ).update_player(player3_dead)
    state = evolve(initial_game_state, player=player_manager_with_dead)

    with pytest.raises(PlayerDeadException):
        action.hit_shell(state, player3_dead.id, live_shell)


def test_hit_shell_damage_zero_charges_unchanged(
    initial_game_state, player2, blank_shell
):
    # Setup: player2 has 2 charges, blank_shell has 0 damage
    new_state = action.hit_shell(initial_game_state, player2.id, blank_shell)
    updated_player2 = new_state.player.get_player(player2.id)
    assert updated_player2.charges == 2  # Charges should remain the same


def test_hit_shell_damage_more_than_charges_results_in_zero(
    initial_game_state, player2, live_shell
):
    # Setup: player2 has 2 charges, live_shell has 1 damage (repeated hit)
    # First hit
    state_after_first_hit = action.hit_shell(initial_game_state, player2.id, live_shell)
    # Second hit
    new_state = action.hit_shell(state_after_first_hit, player2.id, live_shell)
    updated_player2 = new_state.player.get_player(player2.id)
    assert updated_player2.charges == 0  # Should not go negative
