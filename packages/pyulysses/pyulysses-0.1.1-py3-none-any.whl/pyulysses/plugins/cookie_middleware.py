from http.cookies import SimpleCookie

from pyarrow import flight


class CookieMiddlewareFactory(flight.ClientMiddlewareFactory):
    def __init__(self):
        self.cookies = {}

    def start_call(self, info):
        return CookieMiddleware(self)


class CookieMiddleware(flight.ClientMiddleware):
    def __init__(self, factory):
        self.factory = factory

    def received_headers(self, headers):
        for key in headers:
            if key.lower() == 'set-cookie':
                cookie = SimpleCookie()
                for item in headers.get(key):
                    cookie.load(item)
                self.factory.cookies.update(cookie.items())

    def sending_headers(self):
        if self.factory.cookies:
            cookie_string = '; '.join(
                f'{key}={val.value}'
                for key, val in self.factory.cookies.items()
            )
            return {b'cookie': cookie_string.encode('utf-8')}
        return {}
