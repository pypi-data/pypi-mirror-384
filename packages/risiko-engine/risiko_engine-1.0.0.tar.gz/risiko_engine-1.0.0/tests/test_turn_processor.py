from collections import deque

import pytest

from risiko.core.player.exception import PlayerIDNotFoundException
from risiko.service.managers.turn import TurnManager
from risiko.service.processors import turn as turn_processor
from risiko.service.risiko_state import RisikoState


@pytest.fixture
def player_ids():
    return ["p1", "p2", "p3"]


@pytest.fixture
def initial_game_state(player_ids):
    turn_manager = TurnManager(order=deque(player_ids))
    return RisikoState(turns=turn_manager)


@pytest.fixture
def empty_game_state():
    return RisikoState(
        turns=TurnManager(order=deque())
    )  # Assuming current_player_id can be None


# --- Test cases for advance_player_turn ---
def test_advance_player_turn_success_single_turn(initial_game_state):
    new_state = turn_processor.advance_player_turn(initial_game_state, 1)
    assert new_state.turns.current_player_id == "p2"
    assert new_state.turns.turn_order == ("p2", "p3", "p1")


def test_advance_player_turn_success_multiple_turns(initial_game_state):
    new_state = turn_processor.advance_player_turn(initial_game_state, 2)
    assert new_state.turns.current_player_id == "p3"
    assert new_state.turns.turn_order == ("p3", "p1", "p2")


def test_advance_player_turn_success_zero_turns(initial_game_state):
    new_state = turn_processor.advance_player_turn(initial_game_state, 0)
    assert new_state.turns.current_player_id == "p1"
    assert new_state.turns.turn_order == ("p1", "p2", "p3")
    assert new_state == initial_game_state  # Should be identical if no change


def test_advance_player_turn_empty_order_raises_exception(empty_game_state):
    new_state = turn_processor.advance_player_turn(empty_game_state, 1)
    with pytest.raises(PlayerIDNotFoundException):
        _ = new_state.turns.current_player_id


# --- Test cases for reverse_turn_order ---
def test_reverse_turn_order_once(initial_game_state):
    new_state = turn_processor.reverse_turn_order(initial_game_state)
    assert new_state.turns._direction == -1
    assert new_state.turns.turn_order == (
        "p1",
        "p2",
        "p3",
    )  # Order itself doesn't change, only direction


def test_reverse_turn_order_twice(initial_game_state):
    state_reversed_once = turn_processor.reverse_turn_order(initial_game_state)
    state_reversed_twice = turn_processor.reverse_turn_order(state_reversed_once)
    assert state_reversed_twice.turns._direction == 1
    assert state_reversed_twice.turns.turn_order == ("p1", "p2", "p3")
    assert state_reversed_twice == initial_game_state  # Should be identical
