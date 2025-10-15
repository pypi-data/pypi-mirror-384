import time

from activegraf_python.authentication_manager.AuthenticationManager import AuthenticationManager
from activegraf_python.communication.GrafDataChange import GrafDataChange
from activegraf_python.models.GrafData import GrafData
from activegraf_python.models.ActiveGrafData import ActiveGrafData
from activegraf_python.utils.CellDataUtils import CellDataUtils
from activegraf_python.models.AuthorizationResult import AuthorizationResult

_auth = AuthenticationManager()


class authenticatingGrafData(ActiveGrafData):
    def _build_graf_data(self, graf_data: GrafData) -> GrafDataChange:
        graf_data.definition = self._init_graf_data_definition("auth1234", "Intuit oauth token test",
                                                               series=[
                                                                   "token"],
                                                               categories=["value"])
        graf_data.values.append(CellDataUtils.createFrom("no token yet", True))
        return graf_data


auth_gd = authenticatingGrafData()

auth_gd.start()

_authorizationResult: AuthorizationResult = _auth.requestAuthorization(
    baseUri="https://developer.intuit.com",
    scope="com.intuit.quickbooks.accounting",
    clientId="YOUR_CLIENT_ID",
    clientSecret="YOUR_CLIENT_SECRET",
)

print("token: " + _authorizationResult.token)
print("redirectUri: " + _authorizationResult.redirectUri)
print("realmId: " + _authorizationResult.extraData["realmId"])

auth_gd.get_grafData_mutator().set(
    0, 0, CellDataUtils.createFrom(_authorizationResult.token, True))

while True:
    time.sleep(1)
