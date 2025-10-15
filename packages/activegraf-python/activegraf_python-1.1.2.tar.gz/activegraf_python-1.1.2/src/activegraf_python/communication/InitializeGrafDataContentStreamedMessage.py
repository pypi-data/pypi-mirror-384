class InitializeGrafDataContentStreamedMessage:
    id: str
    name: str
    source: str
    sourceId: str
    originX: int
    originY: int
    categories: list[str]
    series: list[str]

    def __init__(self, id: str, source: str, name: str, categories: list[str] = [], series: list[str] = []):
        self.id = id
        self.name = name
        self.categories = categories
        self.series = series
        self.source = source
        self.sourceId = ""
        self.originX = 0
        self.originY = 0
