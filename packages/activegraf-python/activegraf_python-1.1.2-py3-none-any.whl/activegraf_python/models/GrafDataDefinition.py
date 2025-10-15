class GrafDataDefinition:
    id: str
    name: str
    source: str
    sourceId: str
    sourceUri: str
    originX: int
    originY: int
    categories: list[str]
    series: list[str]

    def __init__(self, id: str, source: str, name: str, sourceUri: str, categories: list[str] = [], series: list[str] = []):
        self.id = id
        self.name = name
        self.categories = categories
        self.series = series
        self.source = "python"
        self.sourceId = ""
        self.sourceUri = sourceUri
        self.originX = 0
        self.originY = 0
