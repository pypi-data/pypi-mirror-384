from itertools import chain
from events import Events
from activegraf_python.communication.AxisChanged import AxisChanged
from activegraf_python.communication.AxisDataChange import AxisDataChanged
from activegraf_python.communication.CellValueChanged import CellValueChanged
from activegraf_python.communication.ComponentCommunicator import ComponentCommunicator
from activegraf_python.communication.GrafDataChange import GrafDataChange
from activegraf_python.communication.GrafDataChangedEvent import GrafDataChangedEvent
from activegraf_python.communication.HandleGrafDataChangesRequest import HandleGrafDataChangesRequest
from activegraf_python.models.GrafData import GrafData
from activegraf_python.models.CellData import CellData
from activegraf_python.models.Place import Place
from activegraf_python.utils.CellDataUtils import CellDataUtils


class GrafDataMutator:
    __communicator: ComponentCommunicator
    graf_data: GrafData
    events: Events

    def __init__(self, graf_data: GrafData, communicator: ComponentCommunicator) -> None:
        self.graf_data = graf_data
        self.__communicator = communicator
        self.events = Events()

    def get(self, y: int, x: int) -> CellData:
        return self.graf_data.values[y*len(self.graf_data.definition.categories) + x]

    def __send_single_cell_change(self, y: int, x: int):
        changes = [[GrafDataChange(None, None, CellValueChanged(
            Place(x, y, 1, 1), [[self.get(y, x)]]))]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def __send_full_change(self, values: list[list[CellData]]):
        series_length = len(values)
        categories_length = len(values[0])
        changes = [[GrafDataChange(None, None, CellValueChanged(
            Place(0, 0, categories_length, series_length), values))]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def set(self, y: int, x: int, value: CellData):
        self.graf_data.values[y *
                              len(self.graf_data.definition.categories) + x] = value
        self.__send_single_cell_change(y, x)

    def set_full(self, values: list[list[CellData]]):
        self.graf_data.values = list(chain.from_iterable(values))
        self.__send_full_change(values)

    def set_categories(self, values: list[CellData]):
        changes = [[GrafDataChange(AxisDataChanged(1, 0, values), None, None)]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def set_series(self, values: list[CellData]):
        changes = [[GrafDataChange(AxisDataChanged(0, 0, values), None, None)]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def insert_series(self, at: int, amount: int):
        changes = [[GrafDataChange(None, AxisChanged(0, 0, at, amount), None)]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def delete_series(self, at: int, amount: int):
        changes = [[GrafDataChange(None, AxisChanged(0, 1, at, amount), None)]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def insert_categories(self, at: int, amount: int):
        changes = [[GrafDataChange(None, AxisChanged(1, 0, at, amount), None)]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def delete_categories(self, at: int, amount: int):
        changes = [[GrafDataChange(None, AxisChanged(1, 1, at, amount), None)]]
        self.__handle_changes(changes)
        self.__send_changes(changes)

    def __send_changes(self, changes: list[list[GrafDataChange]]):
        self.__communicator.send_and_forget(HandleGrafDataChangesRequest(
            self.graf_data.definition.id, self.graf_data.definition.sourceUri, changes))

    def __set_silently(self, y: int, x: int, value: CellData):
        self.graf_data.values[y *
                              len(self.graf_data.definition.categories) + x] = value

    def handle_changes(self, graf_data_changed_event: GrafDataChangedEvent):
        self.__handle_changes(graf_data_changed_event.changes, True)

    def __handle_changes(self, batch: list[list[GrafDataChange]], remote: bool = False):
        for changes in batch:
            for change in changes:
                self.__handle_cell_value_changed(change)
                self.__handle_axis_data_changed(change)
                self.__handle_axis_changed(change)
        if remote:
            self.events.changes_applied()

    def __handle_cell_value_changed(self, graf_data_change: GrafDataChange):
        if graf_data_change.cellValueChanged == None:
            return

        change = graf_data_change.cellValueChanged
        for y in range(change.place.y, change.place.y + change.place.height):
            for x in range(change.place.x, change.place.x + change.place.width):
                self.__set_silently(
                    y, x, change.values[y - change.place.y][x - change.place.x])
                self.events.on_value_changed(x, y)

    def __handle_axis_data_changed(self, graf_data_change: GrafDataChange):
        if graf_data_change.axisDataChanged == None:
            return

        change = graf_data_change.axisDataChanged
        if change.axis == 0:
            axis = self.graf_data.definition.series
        else:
            axis = self.graf_data.definition.categories

        for i in range(change.at, change.at+len(change.values)):
            new_value = change.values[change.at+i].value
            axis[i] = new_value

    def __handle_axis_changed(self, graf_data_change: GrafDataChange):
        if graf_data_change.axisChanged == None:
            return

        change = graf_data_change.axisChanged

        if change.axis == 0:
            if change.change == 0:
                for i in range(change.at, change.at + change.size):
                    self.__insert_series(i)
            else:
                for i in reversed(range(change.at, change.at + change.size)):
                    self.__delete_series(i)
        else:
            if change.change == 0:
                for i in range(change.at, change.at + change.size):
                    self.__insert_category(i)
            else:
                for i in reversed(range(change.at, change.at + change.size)):
                    self.__delete_category(i)

    def __insert_series(self, at: int):
        axis = self.graf_data.definition.series
        axis.insert(at, "")

        if self.graf_data.values == None:
            return

        insertPosition = len(self.graf_data.definition.categories) * at
        for _ in range(0, len(self.graf_data.definition.categories)):
            self.graf_data.values.insert(insertPosition, CellDataUtils.empty())

    def __insert_category(self, at: int):
        axis = self.graf_data.definition.categories
        axis.insert(at, "")

        if self.graf_data.values == None:
            return

        step = len(self.graf_data.definition.categories)
        size = len(self.graf_data.definition.categories) * \
            len(self.graf_data.definition.series)
        for i in reversed(range(at, size-at, step)):
            self.graf_data.values.insert(i, CellDataUtils.empty())

    def __delete_series(self, at: int):
        axis = self.graf_data.definition.series
        del axis[at]
        if self.graf_data.values == None:
            return

        insertPosition = len(self.graf_data.definition.categories) * at
        for _ in range(0, len(self.graf_data.definition.categories)):
            del self.graf_data.values[insertPosition]

    def __delete_category(self, at: int):
        axis = self.graf_data.definition.categories
        del axis[at]
        if self.graf_data.values == None:
            return

        step = len(self.graf_data.definition.categories)
        for i in range(len(self.graf_data.values), 0, step):
            del self.graf_data.values[i]
