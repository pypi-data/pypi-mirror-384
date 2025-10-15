from abc import ABC
from activegraf_python.communication.ComponentCommunicator import ComponentCommunicator
from activegraf_python.communication.GrafDataChangedEvent import GrafDataChangedEvent
from activegraf_python.communication.GrafDataRowStreamedData import GrafDataRowStreamedData
from activegraf_python.communication.GrafDataService import GrafDataService
from activegraf_python.communication.InitializeGrafDataContentStreamedMessage import InitializeGrafDataContentStreamedMessage
from activegraf_python.communication.ToggleGlobalLoadingRequest import ToggleGlobalLoadingRequest
from activegraf_python.models.GrafData import GrafData
from activegraf_python.models.GrafDataDefinition import GrafDataDefinition
from activegraf_python.models.GrafDataMutator import GrafDataMutator
from activegraf_python.models.CellData import CellData

class ActiveGrafData(ABC):
    __communicator: ComponentCommunicator

    _mutable_graf_data: GrafDataMutator = None
    _readonly_fields: set = None

    def __init__(self) -> None:
        super().__init__()
        self.__communicator = ComponentCommunicator()
        self.__graf_data_service = GrafDataService()
        self._readonly_fields = set()
        self.__init_grafdata()

    def start(self):
        self.__stream_grafdata()
        self.__graf_data_service.add_graf_data(self._mutable_graf_data)
        self._ready()

    def _init_graf_data_definition(self, id: str, name: str, categories: list[str] = [], series: list[str] = []) -> GrafDataDefinition:
        return GrafDataDefinition(id, self.__communicator.source, name, self.__communicator.source_uri, categories=list(map(lambda c: str(c), categories)), series=list(map(lambda s: str(s), series)))

    def _build_graf_data(self, graf_data) -> GrafData:
        pass

    def _ready(self):
        pass

    def _showLoadingIndicator(self):
        self.__communicator.send_and_forget(ToggleGlobalLoadingRequest(True))

    def _hideLoadingIndicator(self):
        self.__communicator.send_and_forget(ToggleGlobalLoadingRequest(False))

    def __init_grafdata(self):
        graf_data = GrafData()
        self._mutable_graf_data = GrafDataMutator(
            graf_data, self.__communicator)
        self._build_graf_data(graf_data)

    def __stream_grafdata(self):
        stream = self.__communicator.stream(InitializeGrafDataContentStreamedMessage(
            self._mutable_graf_data.graf_data.definition.id, self.__communicator.source, self._mutable_graf_data.graf_data.definition.name, self._mutable_graf_data.graf_data.definition.categories, self._mutable_graf_data.graf_data.definition.series))
        categories_length = len(
            self._mutable_graf_data.graf_data.definition.categories)
        for row in range(len(self._mutable_graf_data.graf_data.definition.series)):
            stream.send(GrafDataRowStreamedData(
                row, self._mutable_graf_data.graf_data.values[row*categories_length:(row+1)*categories_length]))
        stream.finish()

    def stop(self):
        self.__communicator.terminate()

    def __get_readonly_key(self, x: int, y: int):
        return "{},{}".format(x, y)

    def mark_readonly(self, x: int, y: int):
        self._readonly_fields.add(self.__get_readonly_key(x, y))

    def unmark_readonly(self, x: int, y: int):
        self._readonly_fields.remove(self.__get_readonly_key(x, y))

    def is_readonly(self, x: int, y: int) -> bool:
        return self.__get_readonly_key(x, y) in self._readonly_fields

    def clear_readonly(self):
        self._readonly_fields.clear()

    def get_grafData_mutator(self) -> GrafDataMutator:
        return self._mutable_graf_data
