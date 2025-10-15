
class ToggleGlobalLoadingRequest:
    enabled: bool

    def __init__(self, enabled: bool):
        self.enabled = enabled