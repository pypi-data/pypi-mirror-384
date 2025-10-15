from enum import Enum

class EpisodeStatus(Enum):
    PASS = "pass"
    FAILED = "failed"
    CANCELED = "canceled"
    ERROR = "error"