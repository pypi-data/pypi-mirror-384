from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..magazine.interface import MagazineInterface
from ..shell.interface import ShellInterface


@runtime_checkable
class ShotgunInterface(Protocol):
    """Interface for a shotgun, defining its core behaviors and properties.
    Implementations should be immutable, returning new instances on state changes.
    """

    magazine: MagazineInterface
    chamber: ShellInterface | None

    def load_chamber(self) -> ShotgunInterface:
        """
        Loads a shell from the magazine into the chamber.

        Returns:
            ShotgunInterface: A new shotgun instance with the chamber loaded.
        """
        ...

    def unload_chamber(self) -> ShotgunInterface:
        """
        Unloads the shell from the chamber, typically back into the magazine.

        Returns:
            ShotgunInterface: A new shotgun instance with the chamber unloaded.
        """
        ...

    def fire(self) -> tuple[ShellInterface, ShotgunInterface]:
        """
        Fires the shell currently in the chamber.

        Returns:
            tuple[ShellInterface, ShotgunInterface]: A tuple containing the fired
                shell and a new shotgun instance with an empty chamber.
        """
        ...
