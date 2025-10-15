from dataclasses import dataclass
from activegraf_python.communication.GrafDataChange import GrafDataChange


@dataclass
class GrafDataChangedEvent():
    id: str
    sourceUri: str
    changes: list[list[GrafDataChange]]

    @classmethod
    def from_dict(cls, data: dict):
        changes = []
        for batch in data["changes"]:
            local_changes = []
            for change in batch:
                local_changes.append(GrafDataChange.from_dict(change))
            changes.append(local_changes)
        return cls(data["id"], data["sourceUri"], changes)
