import jsonpickle
from signalrcore.subject import Subject


class StreamChannel:
    __subject: Subject

    def __init__(self, subject: Subject) -> None:
        self.__subject = subject

    def send(self, data):
        self.__subject.next(jsonpickle.encode(data, unpicklable=False))

    def finish(self):
        self.__subject.complete()
