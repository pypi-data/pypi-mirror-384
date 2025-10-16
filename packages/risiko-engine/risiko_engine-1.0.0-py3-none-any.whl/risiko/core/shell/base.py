from attrs import define, field
from attrs.validators import ge, instance_of

from .interface import ShellInterface


@define(frozen=True)
class RisikoShell(ShellInterface):
    """
    Represents a generic shell with a specific type and damage value.

    This class is immutable and serves as a base for different types of shells
    in the game.
    """

    shell_type: str = field(kw_only=True, validator=instance_of(str))
    damage: int = field(validator=(ge(0), instance_of(int)), kw_only=True)
