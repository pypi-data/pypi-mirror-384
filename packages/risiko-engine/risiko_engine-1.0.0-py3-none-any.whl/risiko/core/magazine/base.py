from __future__ import annotations

from collections import deque
from typing import final, override

from attrs import define, evolve, field

from ..shell import ShellInterface, ShellNotFoundException
from .exception import MagazineEmptyException
from .interface import MagazineInterface


@define(frozen=True)
class RisikoMagazine(MagazineInterface):
    """Represents the shotgun's magazine, holding a deque of shells.
    This class is immutable; all methods that modify the magazine's state
    return a new MagazineBase instance.
    """

    _tube: deque[ShellInterface] = field(factory=deque, alias="tube", kw_only=True)

    @property
    @final
    @override
    def tube(self) -> tuple[ShellInterface, ...]:
        return tuple(self._tube)

    @final
    @override
    def load_shell(self, shell: ShellInterface) -> RisikoMagazine:
        """
        Load a single shell object into the magazine.

        Args:
            shell (ShellInterface): A shell object to add to the magazine.

        Returns:
            MagazineBase: A new MagazineBase instance with the added shells.
        """

        new_tube = self._tube.copy()
        new_tube.append(shell)

        return evolve(self, tube=new_tube)

    @final
    @override
    def eject_shell(self) -> tuple[ShellInterface, RisikoMagazine]:
        """
        Ejects the first shell from the magazine.

        Returns:
            tuple[ShellInterface, MagazineBase]: containing the ejected shell
                and a new RisikoMagazine instance.

        Raises:
            MagazineEmptyException: If the magazine is empty.
        """
        if not self.tube:
            raise MagazineEmptyException(info="Failed to Eject Shell")

        new_tube = self._tube.copy()

        shell = new_tube.popleft()

        return (shell, evolve(self, tube=new_tube))

    @final
    @override
    def unload_shell(self, shell: ShellInterface) -> RisikoMagazine:
        """
        Unloads a single shell from the magazine.

        Args:
            shell (ShellInterface): The shell object to remove from the magazine.

        Returns:
            MagazineBase: A new MagazineBase instance with the unloaded shell.

        Raises:
            ShellNotFoundException: If the shell is not found in the magazine.
        """
        try:
            new_tube = self._tube.copy()
            new_tube.remove(shell)
        except ValueError:
            raise ShellNotFoundException(f"Shell not found in magazine: {shell}")

        return evolve(self, tube=new_tube)

    @final
    @override
    def clear(self) -> RisikoMagazine:
        """
        Clears all shells from the magazine.

        Returns:
            MagazineBase: A new MagazineBase instance with an empty magazine.

        Raises:
            MagazineEmptyException: If the magazine is already empty.
        """
        if not self.tube:
            raise MagazineEmptyException(info="failed to clear magazine")

        new_tube = self._tube.copy()
        new_tube.clear()

        return evolve(self, tube=new_tube)
