from activegraf_python.communication.ComponentCommunicator import ComponentCommunicator
from activegraf_python.communication.GrafDataChangedEvent import GrafDataChangedEvent
from activegraf_python.models.GrafDataMutator import GrafDataMutator


class GrafDataService(object):
    __communicator: ComponentCommunicator
    __registered_graf_datas: dict[str, GrafDataMutator] = {}

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GrafDataService, cls).__new__(cls)
            cls.instance.__communicator = ComponentCommunicator()
            cls.instance.init()
        return cls.instance
    
    def init(self):
        self.__communicator.subscribe(
            GrafDataChangedEvent, self.__handle_graf_data_changes)

    def __handle_graf_data_changes(self, data):
        event = GrafDataChangedEvent.from_dict(data['body'])
        key = self.__get_key(event.id, event.sourceUri)
        if key in self.__registered_graf_datas:
            mutator = self.__registered_graf_datas[key]
            mutator.handle_changes(event)

    def add_graf_data(self, graf_data_mutator: GrafDataMutator):
        self.__registered_graf_datas[self.__get_key_from_graf_data(graf_data_mutator)] = graf_data_mutator

    def __get_key_from_graf_data(self, graf_data_mutator: GrafDataMutator):
        return self.__get_key(graf_data_mutator.graf_data.definition.id, graf_data_mutator.graf_data.definition.sourceUri)
    
    def __get_key(self, id: str, source_uri: str):
        return "{0}@{1}".format(id, source_uri)