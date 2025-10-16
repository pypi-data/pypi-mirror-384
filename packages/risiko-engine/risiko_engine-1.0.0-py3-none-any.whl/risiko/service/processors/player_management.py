from attrs import evolve

from ...core.player import PlayerInterface
from ..risiko_state import RisikoState


def add_player_to_game(game_state: RisikoState, player: PlayerInterface) -> RisikoState:
    """
    Adds a new player to the game.

    Args:
        game_state (RisikoState): The current state of the game.
        player (PlayerInterface): The player object to add.

    Returns:
        RisikoState: A new game state with the player added.
    """
    new_player_manager = game_state.player.add_player(player=player)
    new_turn_manager = game_state.turns.add_id(id=player.id)

    return evolve(game_state, player=new_player_manager, turns=new_turn_manager)


def remove_player_from_game(game_state: RisikoState, id: str) -> RisikoState:
    """
    Removes a player from the game.

    Args:
        game_state (RisikoState): The current state of the game.
        id (str): The ID of the player to remove.

    Returns:
        RisikoState: A new game state with the player removed.
    """

    new_player_manager = game_state.player.remove_player(player_id=id)

    new_turn_manager = game_state.turns.remove_id(id=id)

    return evolve(game_state, player=new_player_manager, turns=new_turn_manager)
