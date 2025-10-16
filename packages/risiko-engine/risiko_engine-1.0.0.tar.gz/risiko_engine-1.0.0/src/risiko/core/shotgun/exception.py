from ..exception import RisikoException


class ShotgunException(RisikoException):
    """Base exception for the shotgun component"""

    pass


class ShotgunUnLoadedException(ShotgunException):
    """Raised when an operation requires a loaded shotgun, but it is not."""

    def __init__(self, message="Shotgun is not loaded"):
        """
        Initializes the ShotgunUnLoadedException.

        Args:
            message (str, optional):
                The error message. Defaults to "Shotgun is not loaded".
        """
        self.message = message
        super().__init__(self.message)


class ShotgunLoadedException(ShotgunException):
    """Raised when an operation requires an unloaded shotgun, but it is not."""

    def __init__(self, message="Shotgun is loaded"):
        """
        Initializes the ShotgunLoadedException.

        Args:
            message (str, optional): The error message. Defaults to "Shotgun is loaded".
        """
        self.message = message
        super().__init__(self.message)
