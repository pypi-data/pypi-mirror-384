import pytest

from risiko.core.magazine.base import RisikoMagazine as MagazineBase
from risiko.core.magazine.exception import MagazineEmptyException
from risiko.core.shell.base import RisikoShell


# Define some concrete shell types for testing
class BuckshotShell(RisikoShell):
    pass


class SlugShell(RisikoShell):
    pass


def test_magazine_creation():
    """Test that a generic magazine can be instantiated with a specific shell type."""
    magazine = MagazineBase()
    assert len(magazine.tube) == 0


def test_load_and_eject_correct_shell_type():
    """Test that loading and ejecting the correct shell type works."""
    magazine = MagazineBase()
    buckshot = BuckshotShell(shell_type="buckshot", damage=1)

    # Load a shell
    loaded_magazine = magazine.load_shell(buckshot)
    assert len(loaded_magazine.tube) > 0
    assert loaded_magazine.tube[0] == buckshot

    # Eject a shell
    ejected_shell, empty_magazine = loaded_magazine.eject_shell()
    assert ejected_shell == buckshot
    assert isinstance(ejected_shell, BuckshotShell)
    assert len(empty_magazine.tube) == 0


def test_type_safety_concept():
    """
    This test doesn't fail at runtime but demonstrates the concept of type safety.
    A static type checker like mypy would flag the commented-out line as an error.
    """
    magazine = MagazineBase()

    # mypy would raise an error on the following line:
    # error: Argument 1 to "load_round" of "MagazineBase" has incompatible
    # type "list[SlugShell]"; expected "Iterable[BuckshotShell]"
    # loaded_magazine = magazine.load_round([slug])

    assert len(magazine.tube) == 0


def test_eject_from_empty_magazine_raises_exception():
    """Test that ejecting from an empty magazine raises MagazineEmptyException."""
    magazine = MagazineBase()
    with pytest.raises(MagazineEmptyException):
        magazine.eject_shell()


def test_clear_empty_magazine_raises_exception():
    """Test that clearing an already empty magazine raises MagazineEmptyException."""
    magazine = MagazineBase()
    with pytest.raises(MagazineEmptyException):
        magazine.clear()


def test_load_multiple_shells_and_eject_in_order():
    """Test loading multiple shells and ejecting them in FIFO order."""
    magazine = MagazineBase()
    shell1 = BuckshotShell(shell_type="buckshot", damage=1)
    shell2 = BuckshotShell(shell_type="buckshot", damage=1)

    loaded_magazine = magazine.load_shell(shell1).load_shell(shell2)
    assert len(loaded_magazine.tube) > 0
    assert len(loaded_magazine.tube) == 2

    ejected_shell1, magazine_after_1_eject = loaded_magazine.eject_shell()
    assert ejected_shell1 == shell1
    assert len(magazine_after_1_eject.tube) == 1

    ejected_shell2, magazine_after_2_eject = magazine_after_1_eject.eject_shell()
    assert ejected_shell2 == shell2
    assert len(magazine_after_2_eject.tube) == 0


def test_tube_property_is_immutable():
    """Test that the 'tube' property is an immutable tuple."""
    magazine = MagazineBase()
    shell = BuckshotShell(shell_type="buckshot", damage=1)
    loaded_magazine = magazine.load_shell(shell)

    with pytest.raises(TypeError):
        # Attempt to modify the tube; this should fail as tuples are immutable
        loaded_magazine.tube[0] = shell
