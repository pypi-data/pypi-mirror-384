from typing import Protocol, runtime_checkable


@runtime_checkable
class ShellInterface(Protocol):
    """
    Interface for a shell, defining its properties.

    Implementations of this protocol should be immutable.
    """

    damage: int
    shell_type: str
