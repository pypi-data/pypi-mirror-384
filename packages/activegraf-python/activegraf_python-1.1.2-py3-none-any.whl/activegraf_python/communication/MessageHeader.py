class MessageHeader:
    packetId: int
    modelType: str
    traceId: str

    def __init__(self, id: str, modelType: str, traceId: str):
        self.packetId = id
        self.modelType = modelType
        self.traceId = traceId
