from attrs import evolve

from ...core.shell import InvalidShell, ShellInterface
from ..risiko_state import RisikoState


def shotgun_load_shell_in_chamber(game_state: RisikoState):
    """
    Loads a shell from the magazine into the shotgun's chamber.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        RisikoState: A new game state with the shotgun's chamber loaded.

    Raises:
        ShotgunLoadedException: If the chamber is already loaded.
    """
    new_shotgun = game_state.shotgun.load_chamber()

    return evolve(game_state, shotgun=new_shotgun)


def unload_shotgun_chamber(game_state: RisikoState):
    """

    Unloads the shell from the shotgun's chamber back into the magazine.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        RisikoState: A new game state with the shotgun's chamber unloaded.

    """

    new_shotgun = game_state.shotgun.unload_chamber()

    return evolve(game_state, shotgun=new_shotgun)


def replace_chamber_shell_from_shotgun(
    game_state: RisikoState, shell: ShellInterface
) -> RisikoState:
    """
    Replaces the shell in the shotgun's chamber with a new shell.

    Args:
        game_state (RisikoState): The current state of the game.
        shell (ShellInterface): The shell to place in the chamber.

    Returns:
        RisikoState: A new game state with the shell replaced in the chamber.
    """

    if not isinstance(shell, ShellInterface):
        raise InvalidShell(
            f"Invalid object provided. Expected a ShellInterface, but got "
            f"{type(shell)}."
        )

    return evolve(
        game_state,
        shotgun=evolve(game_state.shotgun, chamber=shell),
    )
