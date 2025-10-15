from activegraf_python.models.CellData import CellData
from activegraf_python.models.Place import Place


class CellValueChanged:
    kind: int
    place: Place
    values: list[list[CellData]]

    def __init__(self, place: Place, values: list[list[CellData]]):
        self.kind = 0
        self.place = place
        self.values = values

    @classmethod
    def from_dict(cls, data: dict):
        if data == None:
            return None
        values = []
        for row in data['values']:
            local_row = []
            for cell in row:
                local_row.append(CellData.from_dict(cell))
            values.append(local_row)
        return cls(Place.from_dict(data['place']), values)
