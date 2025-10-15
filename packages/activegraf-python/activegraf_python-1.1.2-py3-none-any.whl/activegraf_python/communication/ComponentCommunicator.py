import jsonpickle
import threading
import os
import __main__

from signalrcore.hub_connection_builder import BaseHubConnection, HubConnectionBuilder
from signalrcore.subject import Subject
from typing import Callable
from activegraf_python.communication.Message import Message
from activegraf_python.communication.MessageHeader import MessageHeader
from activegraf_python.communication.StreamChannel import StreamChannel
from activegraf_python.models.HandshakeResult import HandshakeResult


class ComponentCommunicator(object):
    activeGrafServerUrl: str
    source: str
    source_uri: str
    __hub_connection: BaseHubConnection
    __connection_estabilished_lock: threading.Lock
    __handshake_result: HandshakeResult
    __packet_id: int
    __message_subscribers: dict[str, Callable[[any], None]]

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ComponentCommunicator, cls).__new__(cls)
            cls.instance.prepare()
        return cls.instance

    def prepare(self) -> None:
        self.activeGrafServerUrl = "http://localhost:55580"
        self.source = __main__.__file__
        self.source_uri = os.path.realpath(self.source)
        self.__packet_id = 1
        self.__message_subscribers = {}
        self.__build_signalR()
        self.__start()

    def __build_signalR(self):
        self.__hub_connection = HubConnectionBuilder()\
            .with_url(self.activeGrafServerUrl + "/hub")\
            .with_automatic_reconnect({
                "type": "raw",
                "keep_alive_interval": 30,
                "reconnect_interval": 5,
                "max_attempts": 5})\
            .build()

        self.__hub_connection.on_open(self.__connection_opened)
        self.__hub_connection.on_close(lambda: print("connection closed"))
        self.__hub_connection.on(
            "ServerMessage", self.__server_message_received)

    def __handshake_finished(self, message):
        self.__handshake_result = HandshakeResult(message.result["resultCode"], message.result["localDocumentUri"])
        self.__connection_estabilished_lock.release()

    def __connection_opened(self):
        self.__hub_connection.send(
            "DataSourceHandshake", [self.source_uri], self.__handshake_finished)

    def __server_message_received(self, message: any):
        msg = message[0]
        handler = self.__message_subscribers.get(msg["header"]["modelType"])
        if handler != None:
            handler(msg)
            
    def __prepare_message(self, body) -> Message:
        message = Message(MessageHeader(self.__packet_id,
                          type(body).__name__, "0"), body)
        self.__packet_id += 2
        return message

    def __start(self):
        self.__connection_estabilished_lock = threading.Lock()
        self.__connection_estabilished_lock.acquire()
        self.__hub_connection.start()
        if not self.__connection_estabilished_lock.acquire(timeout=10):
            raise TimeoutError("Connection failed")
        if self.__handshake_result.result_code != 0:
            raise ConnectionAbortedError(
                "Handshake failed with error: '{code}'".format(code=self.__handshake_result))

    def send_and_forget(self, model: any):
        self.__hub_connection.send(
            "ClientMessage", [self.__prepare_message(model)])

    # TODO: better model & return types
    def send(self, model: any, timeout = 10) -> any:
        result_lock = threading.Lock()
        result_lock.acquire()
        result: any

        def message_received(message):
            nonlocal result
            result = message
            result_lock.release()

        self.__hub_connection.send(
            "ClientMessage", [self.__prepare_message(model)], message_received)
        if not result_lock.acquire(timeout = timeout):
            raise TimeoutError("No response received in time")

        return result

    def stream(self, model: any) -> StreamChannel:
        subject = Subject()
        self.__hub_connection.send("StreamedClientMessage", subject)
        subject.next(jsonpickle.encode(self.__prepare_message(model), unpicklable=False))
        return StreamChannel(subject)

    def subscribe(self, messageType: type[any], handler: Callable[[any], None]):
        self.__message_subscribers[messageType.__name__] = handler

    def terminate(self):
        self.__hub_connection.stop()
