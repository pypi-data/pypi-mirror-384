from dataclasses import dataclass


@dataclass
class AuthorizationRequestMessage():
    baseUri: str
    scope: str
    clientId: str
    clientSecret: str
