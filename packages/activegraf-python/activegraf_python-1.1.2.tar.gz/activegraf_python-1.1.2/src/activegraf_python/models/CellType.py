from enum import IntEnum


class CellType(IntEnum):
    Empty = 0
    Integer = 1
    Double = 2
    Boolean = 3
    String = 4
    Date = 5
    Time = 6
    Unknown = 7
