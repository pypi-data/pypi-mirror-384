import os
import sys

from pyarrow import flight

from plugins.auth_middleware import DremioClientAuthMiddlewareFactory
from plugins.cookie_middleware import CookieMiddlewareFactory

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'src')
    ),
)

from configs.env_loader import get_dremio_config


def make_connection(
    host: str,
    port: str,
    username: str,
    password: str = None,
    pat_or_auth_token: str = None,
    tls: bool = True,
    certs: str = None,
    disable_server_verification: bool = True,
    engine: str = None,
    session_properties: list[tuple[str, str]] = None,
):
    """
    Establish a Flight connection to a Dremio instance.
    """
    scheme = 'grpc+tls' if tls else 'grpc+tcp'
    connection_args = {}

    if tls:
        if certs:
            with open(certs, 'rb') as root_certs:
                connection_args['tls_root_certs'] = root_certs.read()
        elif disable_server_verification:
            connection_args[
                'disable_server_verification'
            ] = disable_server_verification
        else:
            raise Exception('Trusted certificates must be provided for TLS.')

    headers = session_properties or []
    if engine:
        headers.append((b'routing_engine', engine.encode('utf-8')))

    cookie_middleware = CookieMiddlewareFactory()

    if pat_or_auth_token:
        client = flight.FlightClient(
            f'{scheme}://{host}:{port}',
            middleware=[cookie_middleware],
            **connection_args,
        )
        headers.append(
            (b'authorization', f'Bearer {pat_or_auth_token}'.encode('utf-8'))
        )
    elif username and password:
        auth_middleware = DremioClientAuthMiddlewareFactory()
        client = flight.FlightClient(
            f'{scheme}://{host}:{port}',
            middleware=[auth_middleware, cookie_middleware],
            **connection_args,
        )
        bearer_token = client.authenticate_basic_token(
            username,
            password,
            flight.FlightCallOptions(headers=headers),
        )
        headers.append(bearer_token)
    else:
        raise Exception(
            'Username/password or PAT/Auth token must be supplied.'
        )

    return client, headers


class Client:
    """
    Wrapper class for managing a Dremio Flight client.
    """

    def __init__(self, **kwargs):
        self.client, self.headers = make_connection(**kwargs)

    def query(self, query: str):
        from .query_executor import execute

        return execute(self.client, self.headers, query)


def dremio_client():
    """Provides a Dremio client instance."""
    config = get_dremio_config()
    return Client(**config)
