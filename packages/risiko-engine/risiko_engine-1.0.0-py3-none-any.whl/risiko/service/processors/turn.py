from attrs import evolve

from ..risiko_state import RisikoState


def advance_player_turn(game_state: RisikoState, turns: int = 1) -> RisikoState:
    """
    Advances the player turn by a specified number of turns.

    Args:
        game_state (RisikoState): The current state of the game.
        turns (int, optional): The number of turns to advance. Defaults to 1.

    Returns:
        RisikoState: A new game state with the advanced turn order.
    """

    new_turn_manager = game_state.turns.advance(turns=turns)

    return evolve(game_state, turns=new_turn_manager)


def reverse_turn_order(game_state: RisikoState) -> RisikoState:
    """
    Reverses the direction of the player turn order.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        RisikoState: A new game state with the reversed turn order direction.
    """

    new_turn_manager = game_state.turns.reverse_order()
    return evolve(game_state, turns=new_turn_manager)
