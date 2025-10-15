class AuthorizationResult:
    token: str
    redirectUri: str
    extraData: dict[str]

    def __init__(self, token: str, redirectUri: str, extraData: dict[str]):
        self.token = token
        self.redirectUri = redirectUri
        self.extraData = extraData
