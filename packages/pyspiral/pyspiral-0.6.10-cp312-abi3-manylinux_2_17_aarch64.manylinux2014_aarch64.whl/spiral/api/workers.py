from enum import Enum, IntEnum


class CPU(IntEnum):
    ONE = 1
    TWO = 2
    FOUR = 4
    EIGHT = 8

    def __str__(self):
        return str(self.value)


class Memory(str, Enum):
    MB_512 = "512Mi"
    GB_1 = "1Gi"
    GB_2 = "2Gi"
    GB_4 = "4Gi"
    GB_8 = "8Gi"

    def __str__(self):
        return self.value


class GcpRegion(str, Enum):
    US_EAST4 = "us-east4"
    EUROPE_WEST4 = "europe-west4"

    def __str__(self):
        return self.value


class ResourceClass(str, Enum):
    """Resource class for text index sync."""

    SMALL = "small"
    LARGE = "large"

    def __str__(self):
        return self.value
