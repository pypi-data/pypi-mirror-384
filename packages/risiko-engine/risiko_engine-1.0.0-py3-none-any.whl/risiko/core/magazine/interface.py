from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..shell import ShellInterface


@runtime_checkable
class MagazineInterface(Protocol):
    """
    Interface for a magazine, defining its core behaviors and properties.
    Implementations should be immutable, returning new instances on state changes.
    """

    @property
    def tube(self) -> tuple[ShellInterface, ...]:
        """
        Returns the deque of shells currently in the magazine tube.
        """
        ...

    def load_shell(self, shell: ShellInterface) -> MagazineInterface:
        """
        Loads a single shell into the magazine.

        Args:
            shell (ShellInterface): The shell object to add to the magazine.

        Returns:
            MagazineInterface: A new magazine instance with the loaded shell.
        """
        ...

    def eject_shell(self) -> tuple[ShellInterface, MagazineInterface]:
        """
        Ejects the first shell from the magazine.

        Returns:
            Tuple[ShellInterface, MagazineInterface]:
                A tuple containing the ejected shell and a new magazine instance.
        """
        ...

    def unload_shell(self, shell: ShellInterface) -> MagazineInterface:
        """
        Unloads a single shell from the magazine.

        Args:
            shell (ShellInterface): The shell object to remove from the magazine.

        Returns:
            MagazineInterface: A new magazine instance with the unloaded shell.
        """
        ...

    def clear(self) -> MagazineInterface:
        """
        Clears all shells from the magazine.

        Returns:
            MagazineInterface: A new magazine instance with an empty magazine.
        """
        ...
