from attrs import define, field
from attrs.validators import instance_of

from ..core import RisikoShotgun
from ..core.shotgun import ShotgunInterface
from .managers import PlayerManager, TurnManager


@define(frozen=True)
class RisikoState:
    """
    Represents the live snapshot of the game state.
    This class is an immutable data container.
    State modifications should be performed via Processors.
    """

    shotgun: ShotgunInterface = field(
        factory=RisikoShotgun, validator=instance_of(ShotgunInterface)
    )
    player: PlayerManager = field(
        factory=PlayerManager, validator=instance_of(PlayerManager)
    )
    turns: TurnManager = field(factory=TurnManager, validator=instance_of(TurnManager))
