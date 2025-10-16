import pytest

from risiko.core.magazine.base import RisikoMagazine as MagazineBase
from risiko.core.magazine.exception import MagazineEmptyException
from risiko.core.shell.base import RisikoShell
from risiko.core.shotgun.base import RisikoShotgun
from risiko.core.shotgun.exception import (
    ShotgunLoadedException,
    ShotgunUnLoadedException,
)


@pytest.fixture
def live_shell():
    return RisikoShell(shell_type="live", damage=1)


@pytest.fixture
def blank_shell():
    return RisikoShell(shell_type="blank", damage=0)


def test_shotgun_creation():
    """Test that a RisikoShotgun can be instantiated."""
    shotgun = RisikoShotgun()
    assert shotgun.chamber is None
    assert len(shotgun.magazine.tube) == 0


def test_load_chamber_when_already_loaded_raises_exception(live_shell):
    """Test loading the chamber when it's already loaded raises an exception."""
    shotgun = RisikoShotgun(chamber=live_shell)
    with pytest.raises(ShotgunLoadedException):
        shotgun.load_chamber()


def test_load_chamber_from_empty_magazine_raises_exception():
    """Test loading the chamber from an empty magazine raises an exception."""
    shotgun = RisikoShotgun()
    with pytest.raises(MagazineEmptyException):
        shotgun.load_chamber()


def test_unload_chamber_when_empty_raises_exception():
    """Test unloading the chamber when it's already empty raises an exception."""
    shotgun = RisikoShotgun()
    with pytest.raises(ShotgunUnLoadedException):
        shotgun.unload_chamber()


def test_fire_when_chamber_is_empty_raises_exception():
    """Test firing the shotgun when the chamber is empty raises an exception."""
    shotgun = RisikoShotgun()
    with pytest.raises(ShotgunUnLoadedException):
        shotgun.fire()


def test_full_sequence_load_fire(live_shell):
    """Test a full sequence of loading the magazine, loading the chamber, and firing."""
    magazine = MagazineBase().load_shell(live_shell)
    shotgun = RisikoShotgun(magazine=magazine)

    # Load chamber
    loaded_shotgun = shotgun.load_chamber()
    assert loaded_shotgun.chamber == live_shell
    assert len(loaded_shotgun.magazine.tube) == 0

    # Fire
    fired_shell, final_shotgun = loaded_shotgun.fire()
    assert fired_shell == live_shell
    assert final_shotgun.chamber is None


def test_sequence_with_unload(live_shell):
    """Test a sequence with unloading the chamber."""
    magazine = MagazineBase().load_shell(live_shell)
    shotgun = RisikoShotgun(magazine=magazine)

    # Load chamber
    loaded_shotgun = shotgun.load_chamber()
    assert loaded_shotgun.chamber == live_shell

    # Unload chamber
    unloaded_shotgun = loaded_shotgun.unload_chamber()
    assert unloaded_shotgun.chamber is None
    assert len(unloaded_shotgun.magazine.tube) > 0
    assert unloaded_shotgun.magazine.tube[0] == live_shell


def test_repeated_load_fire_sequence(live_shell):
    """Test repeated load chamber and fire operations."""
    magazine = (
        MagazineBase()
        .load_shell(live_shell)
        .load_shell(live_shell)
        .load_shell(live_shell)
    )
    shotgun = RisikoShotgun(magazine=magazine)

    # First load and fire
    loaded_shotgun = shotgun.load_chamber()
    fired_shell, shotgun_after_fire = loaded_shotgun.fire()
    assert fired_shell == live_shell
    assert shotgun_after_fire.chamber is None
    assert len(shotgun_after_fire.magazine.tube) == 2

    # Second load and fire
    loaded_shotgun_2 = shotgun_after_fire.load_chamber()
    fired_shell_2, shotgun_after_fire_2 = loaded_shotgun_2.fire()
    assert fired_shell_2 == live_shell
    assert shotgun_after_fire_2.chamber is None
    assert len(shotgun_after_fire_2.magazine.tube) == 1

    # Third load and fire
    loaded_shotgun_3 = shotgun_after_fire_2.load_chamber()
    fired_shell_3, shotgun_after_fire_3 = loaded_shotgun_3.fire()
    assert fired_shell_3 == live_shell
    assert shotgun_after_fire_3.chamber is None
    assert len(shotgun_after_fire_3.magazine.tube) == 0

    # Attempt to load from empty magazine should raise exception
    with pytest.raises(MagazineEmptyException):
        shotgun_after_fire_3.load_chamber()
