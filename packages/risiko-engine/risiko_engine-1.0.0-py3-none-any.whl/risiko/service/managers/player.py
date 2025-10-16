from __future__ import annotations

from types import MappingProxyType

from attrs import define, evolve, field

from ...core.player.exception import (
    InvalidPlayerClassException,
    PlayerIDExistsException,
    PlayerIDNotFoundException,
)
from ...core.player.interface import PlayerInterface


@define(frozen=True)
class PlayerManager:
    """
    Manages the state of all players in the game.

    This is an immutable class that holds a collection of players. Methods that
    modify the collection (e.g., adding or removing a player) will return a new
    instance of PlayerManager with the updated state.
    """

    _pool: dict[str, PlayerInterface] = field(factory=dict, alias="pool", kw_only=True)

    @property
    def player_pool(self) -> MappingProxyType[str, PlayerInterface]:
        """
        A read-only view of the dictionary of players,
        mapping player ID to object.
        """
        return MappingProxyType(self._pool)

    def get_player(self, player_id: str) -> PlayerInterface:
        """
        Retrieves a single player by their unique ID.

        Args:
            player_id: The unique identifier of the player to retrieve.

        Returns:
            PlayerInterface: The player object associated with the provided ID.

        Raises:
            PlayerIDNotFoundException: If no player with the given ID is found.
        """
        try:
            return self._pool[player_id]
        except KeyError:
            raise PlayerIDNotFoundException(
                id=player_id, info=f"Player with ID '{player_id}' not found."
            )

    def add_player(self, player: PlayerInterface) -> PlayerManager:
        """
        Adds a new player to the collection.

        Args:
            player: The player object to add.

        Returns:
            A new PlayerManager instance with the added player.

        Raises:
            PlayerIDExistsException: If a player with the same ID already exists.
            InvalidPlayerClassException: If the provided object is not a valid player.
        """
        if not isinstance(player, PlayerInterface):
            raise InvalidPlayerClassException(
                info=f"recieved {type(player)} instead of PlayerInterface"
            )

        if player.id in self._pool:
            raise PlayerIDExistsException(
                id=player.id, info=f"Player with ID '{player.id}' already exists."
            )

        new_pool = self._pool.copy()
        new_pool[player.id] = player

        return evolve(self, pool=new_pool)

    def update_player(self, player: PlayerInterface) -> PlayerManager:
        """
        Updates an existing player's state.

        The player is identified by the `id` attribute of the provided player object.

        Args:
            player: The player object with updated information.

        Returns:
            A new PlayerManager instance with the updated player.

        Raises:
            PlayerIDNotFoundException: If no player with the given ID is found.
            InvalidPlayerClassException: If the provided object is not a valid player.
        """

        if not isinstance(player, PlayerInterface):
            raise InvalidPlayerClassException(
                info=f"recieved {type(player)} instead of PlayerInterface"
            )

        if player.id not in self._pool:
            raise PlayerIDNotFoundException(
                id=player.id, info=f"Player with ID '{player.id}' not found for update."
            )

        new_pool = self._pool.copy()
        new_pool[player.id] = player

        return evolve(self, pool=new_pool)

    def remove_player(self, player_id: str) -> PlayerManager:
        """
        Removes a player from the collection by their ID.

        Args:
            player_id: The unique identifier of the player to remove.

        Returns:
            A new PlayerManager instance without the removed player.

        Raises:
            PlayerIDNotFoundException: If no player with the given ID is found.
        """
        if player_id not in self._pool:
            raise PlayerIDNotFoundException(
                id=player_id,
                info=f"Player with ID '{player_id}' not found for removal.",
            )

        new_pool = self._pool.copy()
        del new_pool[player_id]

        return evolve(self, pool=new_pool)
