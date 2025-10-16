from attrs import evolve

from ..risiko_state import RisikoState


def player_lose_charges(
    game_state: RisikoState, player_id: str, charges: int
) -> RisikoState:
    """
    Makes a player lose a specified number of charges.

    Args:

        game_state (RisikoState): The current state of the game.
        player_id (str): The ID of the player who will lose charges.
        charges_to_lose (int): The number of charges to deduct.

    Returns:
        RisikoState: A new game state with the player's updated charges.
    """

    player = game_state.player.get_player(player_id=player_id)

    updated_player = player.lose_charges(amt=charges)

    new_player_manager = game_state.player.update_player(player=updated_player)

    return evolve(game_state, player=new_player_manager)


def player_gain_charges(
    game_state: RisikoState, player_id: str, charges: int
) -> RisikoState:
    """
    Makes a player gain a specified number of charges.

    Args:
        game_state (RisikoState): The current state of the game.
        player_id (str): The ID of the player who will gain charges.
        charges_to_gain (int): The number of charges to add.

    Returns:
        RisikoState: A new game state with the player's updated charges.
    """

    player = game_state.player.get_player(player_id=player_id)

    updated_player = player.gain_charges(amt=charges)

    new_player_manager = game_state.player.update_player(player=updated_player)

    return evolve(game_state, player=new_player_manager)
