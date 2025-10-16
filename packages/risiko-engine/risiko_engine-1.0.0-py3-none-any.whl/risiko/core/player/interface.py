from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PlayerInterface(Protocol):
    """
    Interface for a player, defining their attributes and core behaviors.
    Implementations should be immutable, returning new instances on state changes.
    """

    id: str
    charges: int

    def lose_charges(self, amt: int) -> PlayerInterface:
        """Reduces the player's charges by a given amount.

        Since the player is immutable, this method returns a new player instance
        with the adjusted charge count.

        Args:
            amt: The number of charges to lose. Must be a positive integer.

        Returns:
            A new PlayerInterface instance with the reduced charges.
        """
        ...

    def gain_charges(self, amt: int) -> PlayerInterface:
        """Increases the player's charges by a given amount.

        Since the player is immutable, this method returns a new player instance
        with the adjusted charge count.

        Args:
            amt: The number of charges to gain. Must be a positive integer.

        Returns:
            A new PlayerInterface instance with the increased charges.
        """
        ...
