from activegraf_python.communication.MessageHeader import MessageHeader


class Message:
    header: MessageHeader
    body: any

    def __init__(self, header: MessageHeader, body: any) -> None:
        self.header = header
        self.body = body
