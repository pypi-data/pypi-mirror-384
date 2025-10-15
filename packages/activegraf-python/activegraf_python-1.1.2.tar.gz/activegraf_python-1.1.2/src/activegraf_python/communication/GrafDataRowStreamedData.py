from activegraf_python.models.CellData import CellData


class GrafDataRowStreamedData:
    index: int
    data: list[CellData]

    def __init__(self, index: int, data: list[CellData] = []):
        self.index = index
        self.data = data
