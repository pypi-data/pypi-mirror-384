import builtins
import math

from activegraf_python.models.CellData import CellData
from activegraf_python.models.CellType import CellType


class CellDataUtils:
    @staticmethod
    def createFrom(x, read_only=False):
        match type(x):
            case builtins.str:
                return CellData(x, int(CellType.String), read_only)
            case builtins.int:
                return CellData(x, int(CellType.Integer), read_only)
            case builtins.float:
                if (math.isnan(x)):
                    raise TypeError("NaN value is not allowed")
                return CellData(x, int(CellType.Double), read_only)
            case builtins.bool:
                return CellData(x, int(CellType.Boolean), read_only)
            case _:
                return CellData(None, int(CellType.Empty), read_only)

    @staticmethod
    def empty():
        return CellData(None, int(CellType.Empty), False)