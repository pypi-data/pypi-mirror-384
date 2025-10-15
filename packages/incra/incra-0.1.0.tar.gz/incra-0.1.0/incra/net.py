"""
Módulo necessário para requisição em TLS 1.2
"""

import requests
import urllib3
from urllib3.util import create_urllib3_context


class CustomSSLContextHTTPAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs) -> None:
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(
        self, connections, maxsize, block=False, **kwargs
    ) -> None:
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


def create_session() -> requests.Session:
    ctx = create_urllib3_context()
    ctx.load_default_certs()
    ctx.set_ciphers('AES256-GCM-SHA384')

    session = requests.session()
    session.adapters.pop('https://', None)
    session.mount('https://', CustomSSLContextHTTPAdapter(ctx))
    return session
