from pyarrow import flight


class DremioClientAuthMiddlewareFactory(flight.ClientMiddlewareFactory):
    def __init__(self):
        self.call_credential = []

    def start_call(self, info):
        return DremioClientAuthMiddleware(self)

    def set_call_credential(self, call_credential):
        self.call_credential = call_credential


class DremioClientAuthMiddleware(flight.ClientMiddleware):
    def __init__(self, factory):
        self.factory = factory

    def received_headers(self, headers):
        auth_header_key = 'authorization'
        authorization_header = headers.get(auth_header_key, [])
        if authorization_header:
            self.factory.set_call_credential(
                [b'authorization', authorization_header[0].encode('utf-8')]
            )
