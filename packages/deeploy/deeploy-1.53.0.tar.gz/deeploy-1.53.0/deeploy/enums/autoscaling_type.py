from enum import Enum


class AutoScalingType(Enum):
    """Class that contains type of autoscaling"""

    CONCURRENCY = 0
    CPU = 1
