from .risiko_state import RisikoState


def is_game_over(game_state: RisikoState) -> bool:
    """
    Checks if the game has reached an end condition.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if the game is over, False otherwise.
    """
    alive_players = [p for p in game_state.player.player_pool.values() if p.charges > 0]
    return len(alive_players) <= 1


def is_player_alive(game_state: RisikoState, player_id: str) -> bool:
    """
    Checks if a specific player is alive (has charges > 0).

    Args:
        game_state (RisikoState): The current state of the game.
        player_id (str): The ID of the player to check.

    Returns:
        bool: True if the player is alive, False otherwise.
    """
    return game_state.player.get_player(player_id).charges > 0


def is_player_turn(game_state: RisikoState, player_id: str) -> bool:
    """
    Checks if it is currently the specified player's turn.

    Args:
        game_state (RisikoState): The current state of the game.
        player_id (str): The ID of the player to check.

    Returns:
        bool: True if it's the player's turn, False otherwise.
    """
    return game_state.turns.current_player_id == player_id


def can_player_act(game_state: RisikoState, player_id: str) -> bool:
    """
    Checks if a specific player is allowed to take an action.

    Args:
        game_state (RisikoState): The current state of the game.
        player_id (str): The ID of the player to check.

    Returns:
        bool: True if the player can act, False otherwise.
    """
    is_shotgun_loaded = game_state.shotgun.chamber is not None

    return (
        is_player_turn(game_state, player_id)
        and is_player_alive(game_state, player_id)
        and is_shotgun_loaded
    )


def can_load_shell(game_state: RisikoState) -> bool:
    """
    Checks if a shell can be loaded into the shotgun's chamber.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if a shell can be loaded, False otherwise.
    """
    return (
        game_state.shotgun.chamber is None and len(game_state.shotgun.magazine.tube) > 0
    )


def can_fire_shotgun(game_state: RisikoState) -> bool:
    """
    Checks if the shotgun can be fired (i.e., if the chamber is not empty).

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if the shotgun can be fired, False otherwise.
    """
    return game_state.shotgun.chamber is not None


def can_clear_magazine(game_state: RisikoState) -> bool:
    """
    Checks if the magazine can be cleared.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if the magazine can be cleared, False otherwise.
    """
    return len(game_state.shotgun.magazine.tube) > 0


def is_magazine_empty(game_state: RisikoState) -> bool:
    """
    Checks if the shotgun's magazine is empty.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if the magazine is empty, False otherwise.
    """
    return not game_state.shotgun.magazine.tube


def is_chamber_empty(game_state: RisikoState) -> bool:
    """
    Checks if the shotgun's chamber is empty.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if the chamber is empty, False otherwise.
    """
    return game_state.shotgun.chamber is None


def is_valid_target(game_state: RisikoState, target_player_id: str) -> bool:
    """
    Checks if a player is a valid target for an action.

    Args:
        game_state (RisikoState): The current state of the game.
        target_player_id (str): The ID of the player to check as a target.

    Returns:
        bool: True if the player is a valid target, False otherwise.
    """
    # A valid target must be alive and not the current player
    return (
        is_player_alive(game_state, target_player_id)
        and game_state.turns.current_player_id != target_player_id
    )


def can_start_game(game_state: RisikoState) -> bool:
    """
    Checks if the game can be started.

    Args:
        game_state (RisikoState): The current state of the game.

    Returns:
        bool: True if the game can be started, False otherwise.
    """
    # Requires at least two players to start the game
    return len(game_state.player.player_pool) >= 2
