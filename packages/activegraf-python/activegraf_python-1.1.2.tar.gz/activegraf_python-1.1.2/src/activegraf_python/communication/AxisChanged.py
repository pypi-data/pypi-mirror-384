class AxisChanged:
    kind: int
    axis: int  # 0=series, 1=categories
    change: int  # 0=insert, 1=delete
    at: int
    size: int

    def __init__(self, axis: int, change: int, at: int, size: int):
        self.kind = 1
        self.axis = axis
        self.change = change
        self.at = at
        self.size = size

    @classmethod
    def from_dict(cls, data: dict):
        if data == None:
            return None
        return cls(data['axis'], data['change'], data['at'], data['size'])
