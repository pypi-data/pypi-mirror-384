import pytest

from risiko.core.player.base import RisikoPlayer as PlayerBase
from risiko.core.player.exception import (
    PlayerIDExistsException,
    PlayerIDNotFoundException,
)
from risiko.service.managers.player import PlayerManager


class TestPlayerManager:
    """Test cases for PlayerManager functionality"""

    def test_get_player_existing(self):
        """Test retrieving an existing player"""
        player = PlayerBase(id="player1", charges=3)
        manager = PlayerManager().add_player(player)

        result = manager.get_player("player1")
        assert result == player
        assert result.id == "player1"
        assert result.charges == 3

    def test_get_player_nonexistent(self):
        """Test retrieving a non-existent player raises exception"""
        manager = PlayerManager()

        with pytest.raises(PlayerIDNotFoundException):
            manager.get_player("nonexistent")

    def test_get_all_player_empty(self):
        """Test getting all players when pool is empty"""
        manager = PlayerManager()
        assert len(manager.player_pool) == 0

    def test_get_all_player_with_players(self):
        """Test getting all players when pool has players"""
        player1 = PlayerBase(id="player1", charges=3)
        player2 = PlayerBase(id="player2", charges=3)
        manager = PlayerManager().add_player(player1).add_player(player2)

        result = manager.player_pool
        assert len(result) == 2
        assert result["player1"] == player1
        assert result["player2"] == player2

    def test_add_player_success(self):
        """Test successfully adding a new player"""
        manager = PlayerManager()
        player = PlayerBase(id="new_player", charges=3)

        new_manager = manager.add_player(player)
        assert len(new_manager.player_pool) == 1
        assert new_manager.get_player("new_player") == player

    def test_add_player_duplicate_id(self):
        """Test adding a player with duplicate ID raises exception"""
        player1 = PlayerBase(id="player1", charges=3)
        player2 = PlayerBase(id="player1", charges=3)  # Same ID
        manager = PlayerManager().add_player(player1)

        with pytest.raises(PlayerIDExistsException):
            manager.add_player(player2)

    def test_update_player_success(self):
        """Test successfully updating an existing player"""
        original_player = PlayerBase(id="player1", charges=3)
        updated_player = PlayerBase(id="player1", charges=2)
        manager = PlayerManager().add_player(original_player)

        new_manager = manager.update_player(updated_player)
        result = new_manager.get_player("player1")
        assert result.charges == 2

    def test_update_player_nonexistent(self):
        """Test updating a non-existent player raises exception"""
        player = PlayerBase(id="nonexistent", charges=3)
        manager = PlayerManager()

        with pytest.raises(PlayerIDNotFoundException):
            manager.update_player(player)

    def test_remove_player_success(self):
        """Test successfully removing a player"""
        player = PlayerBase(id="player1", charges=3)
        manager = PlayerManager().add_player(player)

        new_manager = manager.remove_player("player1")

        # Assert that getting all players now returns an empty dict
        assert len(new_manager.player_pool) == 0

        with pytest.raises(PlayerIDNotFoundException):
            new_manager.get_player("player1")

    def test_remove_player_nonexistent(self):
        """Test removing a non-existent player raises exception"""
        manager = PlayerManager()

        with pytest.raises(PlayerIDNotFoundException):
            manager.remove_player("nonexistent")

    def test_immutability(self):
        """Test that PlayerManager operations return new instances"""
        player = PlayerBase(id="player1", charges=3)
        manager = PlayerManager()

        # Original manager should remain unchanged
        new_manager = manager.add_player(player)

        # Check the original manager is still empty
        assert len(manager.player_pool) == 0

        # Check the new manager has one player
        assert len(new_manager.player_pool) == 1

        # Test that they are different objects
        assert manager is not new_manager
