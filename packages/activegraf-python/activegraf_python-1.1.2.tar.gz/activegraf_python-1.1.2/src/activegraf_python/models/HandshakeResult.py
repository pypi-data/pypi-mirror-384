class HandshakeResult:
    result_code: int
    local_document_uri: str

    def __init__(self, result_code: int, local_document_uri: str):
        self.result_code = result_code
        self.local_document_uri = local_document_uri
