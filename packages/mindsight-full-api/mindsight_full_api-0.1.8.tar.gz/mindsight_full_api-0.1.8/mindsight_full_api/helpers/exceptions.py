"""Module providing exceptions structure"""


class FullAnalyticsExceptions(Exception):
    """Full Analytics api base exceptions"""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class BadRequestException(FullAnalyticsExceptions):
    """Bad Request From api"""

    def __init__(self, message: str) -> None:
        super().__init__(f"ERROR: {message}")


class ServerErrorException(FullAnalyticsExceptions):
    """Server Error From api"""

    def __init__(self, message: str) -> None:
        super().__init__(f"ERROR: {message}")
