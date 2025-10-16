from collections import deque

import pytest
from attrs import evolve

from risiko.core.magazine.base import RisikoMagazine as MagazineBase
from risiko.core.magazine.exception import MagazineEmptyException
from risiko.core.shell import InvalidShell
from risiko.core.shell.base import RisikoShell as ShellBase
from risiko.core.shotgun.base import RisikoShotgun as ShotgunBase
from risiko.core.shotgun.exception import (
    ShotgunLoadedException,
    ShotgunUnLoadedException,
)
from risiko.service.processors import weapon as weapon_processor
from risiko.service.risiko_state import RisikoState


@pytest.fixture
def live_shell():
    return ShellBase(shell_type="live", damage=1)


@pytest.fixture
def blank_shell():
    return ShellBase(shell_type="blank", damage=0)


@pytest.fixture
def initial_game_state():
    return RisikoState()


@pytest.fixture
def game_state_with_loaded_magazine(initial_game_state, live_shell):
    magazine = MagazineBase(tube=deque([live_shell]))
    shotgun = ShotgunBase(magazine=magazine)
    return evolve(initial_game_state, shotgun=shotgun)


@pytest.fixture
def game_state_with_loaded_chamber(initial_game_state, live_shell):
    shotgun = ShotgunBase(chamber=live_shell)
    return evolve(initial_game_state, shotgun=shotgun)


# --- Test cases for shotgun_load_shell ---
def test_shotgun_load_shell_success(game_state_with_loaded_magazine, live_shell):
    new_state = weapon_processor.shotgun_load_shell_in_chamber(
        game_state_with_loaded_magazine
    )
    assert new_state.shotgun.chamber == live_shell
    assert len(new_state.shotgun.magazine.tube) == 0


def test_shotgun_load_shell_chamber_already_loaded_raises_exception(
    game_state_with_loaded_chamber,
):
    with pytest.raises(ShotgunLoadedException):
        weapon_processor.shotgun_load_shell_in_chamber(game_state_with_loaded_chamber)


def test_shotgun_load_shell_magazine_empty_raises_exception(initial_game_state):
    with pytest.raises(MagazineEmptyException):
        weapon_processor.shotgun_load_shell_in_chamber(initial_game_state)


# --- Test cases for unload_shotgun_chamber ---
def test_unload_shotgun_chamber_success(game_state_with_loaded_chamber, live_shell):
    new_state = weapon_processor.unload_shotgun_chamber(game_state_with_loaded_chamber)
    assert new_state.shotgun.chamber is None
    assert len(new_state.shotgun.magazine.tube) == 1
    assert new_state.shotgun.magazine.tube[0] == live_shell


def test_unload_shotgun_chamber_empty_raises_exception(initial_game_state):
    with pytest.raises(ShotgunUnLoadedException):
        weapon_processor.unload_shotgun_chamber(initial_game_state)


# --- Test cases for replace_chamber_shell_from_shotgun ---
def test_replace_chamber_shell_from_shotgun_success_empty_chamber(
    initial_game_state, live_shell
):
    new_state = weapon_processor.replace_chamber_shell_from_shotgun(
        initial_game_state, live_shell
    )
    assert new_state.shotgun.chamber == ShellBase(shell_type="live", damage=1)


def test_replace_chamber_shell_from_shotgun_success_loaded_chamber(
    game_state_with_loaded_chamber, blank_shell
):
    new_state = weapon_processor.replace_chamber_shell_from_shotgun(
        game_state_with_loaded_chamber, blank_shell
    )
    assert new_state.shotgun.chamber == ShellBase(shell_type="blank", damage=0)


def test_replace_chamber_shell_from_shotgun_invalid_shell_raises_exception(
    initial_game_state,
):
    with pytest.raises(InvalidShell):
        weapon_processor.replace_chamber_shell_from_shotgun(
            initial_game_state, "not_a_shell"
        )
