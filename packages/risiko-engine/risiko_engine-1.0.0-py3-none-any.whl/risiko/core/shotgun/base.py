from __future__ import annotations

from typing import final, override

from attrs import define, evolve, field

from ..magazine import MagazineInterface, RisikoMagazine
from ..shell.interface import ShellInterface
from .exception import ShotgunLoadedException, ShotgunUnLoadedException
from .interface import ShotgunInterface


@define(frozen=True)
class RisikoShotgun(ShotgunInterface):
    """
    Represents the shotgun in the game, including its magazine and chamber.
    This class is immutable; all methods that modify the shotgun's state
    return a new RisikoShotgun instance.
    """

    magazine: MagazineInterface = field(factory=RisikoMagazine, kw_only=True)
    chamber: ShellInterface | None = field(default=None, kw_only=True)

    @final
    @override
    def load_chamber(self) -> RisikoShotgun:
        """
        Loads a shell from the magazine into the chamber.

        Returns:
            RisikoShotgun: A new RisikoShotgun instance with the chamber
            loaded and magazine updated.

        Raises:
            ShotgunLoadedException: If the chamber is already loaded.
        """

        if self.chamber is not None:
            raise ShotgunLoadedException("Shotgun is Already Loaded")

        new_chamber, new_magazine = self.magazine.eject_shell()

        return evolve(self, chamber=new_chamber, magazine=new_magazine)

    @final
    @override
    def unload_chamber(self) -> RisikoShotgun:
        """
        Unloads the shell from the chamber back into the magazine.

        Returns:
            RisikoShotgun: A new RisikoShotgun instance with the chamber empty
            and magazine updated.

        Raises:
            ShotgunUnLoadedException: If the chamber is already empty.
        """
        if self.chamber is None:
            raise ShotgunUnLoadedException(
                "Attempted to unload, chamber is already empty"
            )

        new_magazine = self.magazine.load_shell(self.chamber)
        return evolve(self, chamber=None, magazine=new_magazine)

    @final
    @override
    def fire(self) -> tuple[ShellInterface, RisikoShotgun]:
        """
        Fires the shell currently in the chamber.

        Returns:
            tuple[ShellInterface, RisikoShotgun]:
            A tuple containing the fired shell and a new RisikoShotgun instance with
            an empty chamber.

        Raises:
            ShotgunUnLoadedException: If the chamber is empty.
        """
        if self.chamber is None:
            raise ShotgunUnLoadedException(
                message="Attempted to fire, chamber is empty (Not Loaded)"
            )

        fired_shell = self.chamber

        return (fired_shell, evolve(self, chamber=None))
