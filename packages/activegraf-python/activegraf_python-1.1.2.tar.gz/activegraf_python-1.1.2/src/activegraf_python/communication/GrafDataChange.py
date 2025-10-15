from dataclasses import dataclass
from activegraf_python.communication.AxisChanged import AxisChanged
from activegraf_python.communication.AxisDataChange import AxisDataChanged
from activegraf_python.communication.CellValueChanged import CellValueChanged


@dataclass
class GrafDataChange:
    axisDataChanged: AxisDataChanged
    axisChanged: AxisChanged
    cellValueChanged: CellValueChanged

    @classmethod
    def from_dict(cls, data: dict):
        return cls(None, None, CellValueChanged.from_dict(data["cellValueChanged"]))
