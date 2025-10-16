from __future__ import annotations

from collections import deque

from attrs import Factory, define, evolve, field
from attrs.validators import in_

from ...core.player.exception import PlayerIDExistsException, PlayerIDNotFoundException


@define(frozen=True)
class TurnManager:
    """Manages the turn order and direction of play for players in the game.
    It is an immutable class; all methods that modify the order or direction
    return a new TurnManager instance.
    """

    _order: deque[str] = field(default=Factory(deque), alias="order", kw_only=True)
    _direction: int = field(
        default=1,
        converter=int,
        validator=in_((-1, 1)),
        alias="direction",
        kw_only=True,
    )

    @property
    def current_player_id(self) -> str:
        """
        Returns the ID of the player whose turn it currently is.

        Returns:
            str: The ID of the current player.

        Raises:
            PlayerIDNotFoundException: If the order is empty.
        """
        try:
            return self._order[0]

        except IndexError:
            raise PlayerIDNotFoundException(
                id="<None>", info="Player order is empty, cannot get current player."
            )

    @property
    def turn_order(self) -> tuple[str, ...]:
        """
        Returns the current turn order as a tuple of player IDs.

        Returns:
            tuple[str,...]: A tuple of player IDs representing the turn order.

        Raises:
            ValueError: If the turn order is empty.
        """
        if not self._order:  # if order is empty
            raise ValueError("Turn order is empty")

        return tuple(self._order)

    def remove_id(self, id: str) -> TurnManager:
        """
        Removes a player from the turn order.

        Args:
            id (str): The ID of the player to remove.

        Returns:
            TurnManager: A new TurnManager instance with the player removed.

        Raises:
            PlayerIDNotFoundException: If the player ID is not found in the turn order.
        """
        try:
            new_order = self._order.copy()

            new_order.remove(id)

            return evolve(self, order=new_order)

        except ValueError:
            raise PlayerIDNotFoundException(
                id=id, info="There is no player with this ID."
            )

    def add_id(self, id: str) -> TurnManager:
        """
        Adds a player to the end of the order.

        Args:
            id (str): The ID of the player to add.

        Returns:
            TurnManager: A new TurnManager instance with the player added.

        Raises:
            PlayerIDExistsException: If the player ID already exists in the turn order.
        """
        if id in self._order:
            raise PlayerIDExistsException(id=id, info="couldn't able to add the player")

        new_order = self._order.copy()

        new_order.append(id)

        return evolve(self, order=new_order)

    def advance(self, turns: int) -> TurnManager:
        """
        Advances the order by a specified number of turns.

        Args:
            turns (int, optional): The number of turns to advance.

        Returns:
            TurnManager: A new TurnManager instance with the advanced order.
        """
        new_order = self._order.copy()

        new_order.rotate(-(turns * self._direction))

        return evolve(self, order=new_order)

    def reverse_order(self) -> TurnManager:
        """
        Reverses the direction of the order.

        Returns:
            TurnManager: A new TurnManager instance with the reversed direction.
        """
        return evolve(self, direction=self._direction * -1)
