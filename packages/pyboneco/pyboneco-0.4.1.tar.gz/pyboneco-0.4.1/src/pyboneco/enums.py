from enum import IntEnum, StrEnum


class BonecoDeviceClass(StrEnum):
    FAN = "fan"
    HUMIDIFIER = "humidifier"
    SIMPLE_CLIMATE = "simple_climate"
    TOP_CLIMATE = "top_climate"


class BonecoAuthState(IntEnum):
    AUTH_ERROR = -1
    GOT_NONCE = 0
    CONFIRM_WAITING = 1
    CONFIRMED = 2
    GOT_DEVICE_KEY = 3
    AUTH_SUCCESS = 9


class BonecoOperationMode(IntEnum):
    NONE = 0
    HUMIDIFIER = 1
    PURIFIER = 2
    HYBRID = 3


class BonecoModeStatus(IntEnum):
    CUSTOM = 0
    AUTO = 1
    BABY = 2
    SLEEP = 3


class BonecoTimerStatus(IntEnum):
    OFF = 0
    ACTIVE_OFF = 1
    ACTIVE_ON = 2
    RESERVED = 3
