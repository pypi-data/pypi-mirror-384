from ..exception import RisikoException


class MagazineException(RisikoException):
    """Base exception for magazine-related errors."""

    pass


class MagazineEmptyException(MagazineException):
    """Raised when an operation is attempted on an empty magazine."""

    def __init__(self, info) -> None:
        super().__init__(f"Magazine is empty - {info}")
