from activegraf_python.communication.GrafDataChange import GrafDataChange


class HandleGrafDataChangesRequest:
    id: int
    sourceUri: str
    changes: list[list[GrafDataChange]]

    def __init__(self, id, sourceUri, changes):
        self.id = id
        self.sourceUri = sourceUri
        self.changes = changes
