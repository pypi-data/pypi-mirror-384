class Place:
    x: int
    y: int
    width: int
    height: int

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @classmethod
    def from_dict(cls, data: dict):
        obj = cls(data['x'], data['y'], data['width'], data['height'])
        return obj
