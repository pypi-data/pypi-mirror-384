from enum import Enum

class ReturnCode(Enum):
    """Enum used by __main__ for return codes"""
    OK = 0
    FILE_EXISTS = 1
    FILE_NOT_ACCESSIBLE = 2
    MISSING_INPUT_FILES = 3
