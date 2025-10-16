from .action import fire_shell, hit_shell
from .magazine import (
    clear_magazine,
    eject_magazine_shell,
    load_shell_to_magazine,
    remove_shell_from_magazine,
    shuffle_magazine,
)
from .player_management import add_player_to_game, remove_player_from_game
from .player_state import player_gain_charges, player_lose_charges
from .turn import advance_player_turn, reverse_turn_order
from .weapon import (
    replace_chamber_shell_from_shotgun,
    shotgun_load_shell_in_chamber,
    unload_shotgun_chamber,
)

__all__ = [
    "fire_shell",
    "hit_shell",
    "shotgun_load_shell_in_chamber",
    "unload_shotgun_chamber",
    "replace_chamber_shell_from_shotgun",
    "eject_magazine_shell",
    "load_shell_to_magazine",
    "remove_shell_from_magazine",
    "shuffle_magazine",
    "clear_magazine",
    "add_player_to_game",
    "remove_player_from_game",
    "player_gain_charges",
    "player_lose_charges",
    "advance_player_turn",
    "reverse_turn_order",
]
