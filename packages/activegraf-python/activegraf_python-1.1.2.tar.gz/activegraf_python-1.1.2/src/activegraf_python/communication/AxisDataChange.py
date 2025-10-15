from activegraf_python.models.CellData import CellData


class AxisDataChanged:
    kind: int
    axis: int
    at: int
    values: list[CellData]

    def __init__(self, axis: int, at: int, values: list[CellData]):
        self.kind = 2
        self.axis = axis
        self.at = at
        self.values = values

    @classmethod
    def from_dict(cls, data: dict):
        if data == None:
            return None
        values = []
        for value in data['values']:
            values.append(value)
        return cls(data['axis'], data['at'], values)