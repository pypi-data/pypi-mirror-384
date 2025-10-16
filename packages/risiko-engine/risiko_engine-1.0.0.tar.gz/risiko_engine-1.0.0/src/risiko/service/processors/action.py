from attrs import evolve

from ...core.player.exception import PlayerDeadException, PlayerInvalidTurnException
from ...core.shell.interface import ShellInterface
from ..helper import is_player_alive, is_player_turn
from ..risiko_state import RisikoState


def fire_shell(
    game_state: RisikoState, shooter_id: str
) -> tuple[ShellInterface, RisikoState]:
    """
    Fires a shell from the shotgun, updating the game state.

    Args:
        game_state (RisikoState): The current state of the game.
        shooter_id (str): The ID of the player attempting to fire.

    Returns:
        Tuple[ShellInterface, RisikoState]: A tuple containing the fired
            shell and the new game state.

    Raises:
        PlayerDeadException: If the shooter is not alive.
        PlayerInvalidTurnException: If it's not the shooter's turn.
    """
    if not is_player_alive(game_state, player_id=shooter_id):
        raise PlayerDeadException(id=shooter_id, info="Please Remove the dead player")

    if not is_player_turn(game_state=game_state, player_id=shooter_id):
        raise PlayerInvalidTurnException(
            id=shooter_id, info="coudln't able to fire the shell"
        )

    fired_shell, new_shotgun = game_state.shotgun.fire()

    return (fired_shell, evolve(game_state, shotgun=new_shotgun))


def hit_shell(
    game_state: RisikoState, target_id: str, fired_shell: ShellInterface
) -> RisikoState:
    """
    Applies the effect of a fired shell to a target player.

    Args:
        game_state (RisikoState): The current state of the game.
        target_id (str): The ID of the player being targeted.
        fired_shell (ShellInterface): The shell that was fired.

    Returns:
        RisikoState: A new game state with the target player's charges updated.

    Raises:
        PlayerDeadException: If the target player is not alive.
    """
    if not is_player_alive(game_state=game_state, player_id=target_id):
        raise PlayerDeadException(id=target_id, info="Please Remove the dead player")

    target_player = game_state.player.get_player(player_id=target_id)

    updated_player = target_player.lose_charges(amt=fired_shell.damage)

    new_player_manager = game_state.player.update_player(player=updated_player)

    return evolve(game_state, player=new_player_manager)
