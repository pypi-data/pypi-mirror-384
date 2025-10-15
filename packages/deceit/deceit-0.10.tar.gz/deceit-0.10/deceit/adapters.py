import ssl

from requests import Session, Request
from requests.adapters import HTTPAdapter, DEFAULT_POOLSIZE, DEFAULT_POOLBLOCK
from urllib3 import Retry



class RetryAdapter(HTTPAdapter):
    ssl_options = ssl.PROTOCOL_TLSv1_2

    def __init__(self, timeout=None, pool_connections=DEFAULT_POOLSIZE,
                 pool_maxsize=DEFAULT_POOLSIZE,
                 max_retries=None,
                 pool_block=DEFAULT_POOLBLOCK,
                 methods=None,
                 statuses=None):
        if max_retries is None:
            max_retries = Retry(
                connect=5, read=5, redirect=4,
                status_forcelist=statuses or [429, 502, 503, 504],
                allowed_methods=methods or [
                    'HEAD', 'GET', 'POST', 'PUT', 'PATCH', 'DELETE',
                ], backoff_factor=10)
        super().__init__(
            pool_connections=pool_connections, pool_maxsize=pool_maxsize,
            max_retries=max_retries, pool_block=pool_block)
        self.timeout = timeout

    def send(self, request, stream=False, timeout=None,
             verify=True, cert=None, proxies=None):
        if timeout == -1:
            timeout = None
        elif timeout is None and self.timeout is not None:
            timeout = self.timeout
        return super().send(request, stream, timeout, verify, cert, proxies)
