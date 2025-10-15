from activegraf_python.communication.AuthorizationRequestMessage import AuthorizationRequestMessage
from activegraf_python.communication.ComponentCommunicator import ComponentCommunicator
from activegraf_python.exceptions.AuthorizationFailedException import AuthorizationFailedException
from activegraf_python.models.AuthorizationResult import AuthorizationResult


class AuthenticationManager():
    __communicator: ComponentCommunicator

    def __init__(self) -> None:
        super().__init__()
        self.__communicator = ComponentCommunicator()

    def requestAuthorization(self, baseUri: str, scope: str, clientId: str, clientSecret: str) -> AuthorizationResult:
        response = self.__communicator.send(AuthorizationRequestMessage(
            baseUri, scope, clientId, clientSecret), timeout=-1)
        body = response.result['body']
        if ('errorCode' in body):
            raise AuthorizationFailedException("Authorization failed on server side")

        return AuthorizationResult(body['accessToken'], body['redirectUri'], body['extraData'])
