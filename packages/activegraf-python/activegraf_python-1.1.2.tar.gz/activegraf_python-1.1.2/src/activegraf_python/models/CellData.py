class CellData:
    readonly: bool
    type: int
    value: any

    def __init__(self, value: any, type: int = 1, readonly: bool = False):
        self.value = value
        self.type = type
        self.readonly = readonly

    @classmethod
    def from_dict(cls, data: dict):
        return cls(data['value'], data['type'], data['readonly'])
