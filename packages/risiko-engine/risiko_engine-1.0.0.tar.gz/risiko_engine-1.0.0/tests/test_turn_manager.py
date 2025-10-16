from collections import deque

import pytest

from risiko.core.player.exception import (
    PlayerIDExistsException,
    PlayerIDNotFoundException,
)
from risiko.service.managers.turn import TurnManager


class TestTurnManager:
    """Test cases for TurnManager functionality"""

    def test_current_player_id_with_players(self):
        """Test getting current player ID when players exist"""
        manager = TurnManager(order=deque(["player1", "player2", "player3"]))
        assert manager.current_player_id == "player1"

    def test_current_player_id_empty(self):
        """Test getting current player ID when order is empty raises exception"""
        manager = TurnManager(order=deque())

        with pytest.raises(PlayerIDNotFoundException):
            _ = manager.current_player_id

    def test_turn_order_with_players(self):
        """Test getting turn order when players exist"""
        manager = TurnManager(order=deque(["player1", "player2", "player3"]))
        assert manager.turn_order == ("player1", "player2", "player3")

    def test_turn_order_empty(self):
        """Test getting turn order when empty raises exception"""
        manager = TurnManager(order=deque())

        with pytest.raises(ValueError):
            _ = manager.turn_order

    def test_remove_id_existing(self):
        """Test removing an existing player ID"""
        manager = TurnManager(order=deque(["player1", "player2", "player3"]))
        new_manager = manager.remove_id("player2")

        assert new_manager.turn_order == ("player1", "player3")
        assert manager.turn_order == (
            "player1",
            "player2",
            "player3",
        )  # Original unchanged

    def test_remove_id_nonexistent(self):
        """Test removing a non-existent player ID raises exception"""
        manager = TurnManager(order=deque(["player1", "player2"]))

        with pytest.raises(PlayerIDNotFoundException):
            manager.remove_id("nonexistent")

    def test_add_id_new(self):
        """Test adding a new player ID"""
        manager = TurnManager(order=deque(["player1", "player2"]))
        new_manager = manager.add_id("player3")

        assert new_manager.turn_order == ("player1", "player2", "player3")
        assert manager.turn_order == ("player1", "player2")  # Original unchanged

    def test_add_id_duplicate(self):
        """Test adding a duplicate player ID raises exception"""
        manager = TurnManager(order=deque(["player1", "player2"]))

        with pytest.raises(PlayerIDExistsException):
            manager.add_id("player1")

    def test_advance_forward_single_turn(self):
        """Test advancing forward by one turn"""
        manager = TurnManager(order=deque(["player1", "player2", "player3"]))
        new_manager = manager.advance(1)

        assert new_manager.current_player_id == "player2"
        assert new_manager.turn_order == ("player2", "player3", "player1")

    def test_advance_forward_multiple_turns(self):
        """Test advancing forward by multiple turns"""
        manager = TurnManager(order=deque(["player1", "player2", "player3", "player4"]))
        new_manager = manager.advance(2)

        assert new_manager.current_player_id == "player3"
        assert new_manager.turn_order == ("player3", "player4", "player1", "player2")

    def test_advance_backward_single_turn(self):
        """Test advancing backward by one turn"""
        manager = TurnManager(
            order=deque(["player1", "player2", "player3"]), direction=-1
        )
        new_manager = manager.advance(1)

        assert new_manager.current_player_id == "player3"
        assert new_manager.turn_order == ("player3", "player1", "player2")

    def test_advance_backward_multiple_turns(self):
        """Test advancing backward by multiple turns"""
        manager = TurnManager(
            order=deque(["player1", "player2", "player3", "player4"]), direction=-1
        )
        new_manager = manager.advance(2)

        assert new_manager.current_player_id == "player3"
        assert new_manager.turn_order == ("player3", "player4", "player1", "player2")

    def test_reverse_order_forward_to_backward(self):
        """Test reversing order from forward to backward"""
        manager = TurnManager(
            order=deque(["player1", "player2", "player3"]), direction=1
        )
        new_manager = manager.reverse_order()

        assert new_manager._direction == -1
        assert new_manager.turn_order == (
            "player1",
            "player2",
            "player3",
        )  # Order unchanged

    def test_reverse_order_backward_to_forward(self):
        """Test reversing order from backward to forward"""
        manager = TurnManager(
            order=deque(["player1", "player2", "player3"]), direction=-1
        )
        new_manager = manager.reverse_order()

        assert new_manager._direction == 1
        assert new_manager.turn_order == (
            "player1",
            "player2",
            "player3",
        )  # Order unchanged

    def test_immutability(self):
        """Test that TurnManager operations return new instances"""
        manager = TurnManager(order=deque(["player1", "player2"]))

        # Original manager should remain unchanged
        new_manager = manager.add_id("player3")
        assert len(manager.turn_order) == 2
        assert len(new_manager.turn_order) == 3

        # Test that they are different objects
        assert manager is not new_manager
