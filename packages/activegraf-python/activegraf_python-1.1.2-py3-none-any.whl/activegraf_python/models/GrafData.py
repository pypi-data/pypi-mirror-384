from activegraf_python.models.CellData import CellData
from activegraf_python.models.GrafDataDefinition import GrafDataDefinition


class GrafData:
    definition: GrafDataDefinition
    values: list[CellData] = []
