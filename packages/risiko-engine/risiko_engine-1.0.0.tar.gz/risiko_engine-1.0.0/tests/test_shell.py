import pytest

from risiko.core.shell.base import RisikoShell
from risiko.core.shell.interface import ShellInterface


def test_shell_creation():
    """Test that a RisikoShell can be instantiated with valid properties."""
    shell = RisikoShell(shell_type="live", damage=1)
    assert shell.shell_type == "live"
    assert shell.damage == 1


def test_shell_creation_with_negative_damage_raises_exception():
    """Test that creating a shell with negative damage raises a ValueError."""
    with pytest.raises(ValueError):
        RisikoShell(shell_type="live", damage=-1)


def test_risikoshell_is_shellinterface():
    """Test that RisikoShell is a valid implementation of ShellInterface."""
    shell = RisikoShell(shell_type="live", damage=1)
    assert isinstance(shell, ShellInterface)
