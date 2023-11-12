from enum import Enum

class EdgeSensorAdminState(str, Enum):
    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"

class EdgeSensorOperatingState(str, Enum):
    UP = "UP"
    DOWN = "DOWN"