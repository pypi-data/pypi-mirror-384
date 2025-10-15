import json
import logging
import posixpath
from datetime import datetime, timedelta
from time import time
from typing import Optional, Dict, Any
from pytz import utc
import requests
from requests import PreparedRequest
from requests.models import Request, Response
from oauthlib.oauth2 import BackendApplicationClient
from oauthlib.oauth2.rfc6749.tokens import prepare_bearer_headers
from requests_oauthlib.oauth2_session import OAuth2Session
from .adapters import RetryAdapter
from .encoders import JsonEncoder
from .exceptions import ApiException


class ApiClient:
    def __init__(self, *args, base_url=None, default_timeout=None,
                 exception_class=None, statuses=None, **kwargs):
        self.base_url = base_url
        self.default_timeout = default_timeout
        self.adapter = RetryAdapter(timeout=self.default_timeout, statuses=statuses)
        self.session = requests.Session()
        self.session.mount('https://', self.adapter)
        self.session.mount('http://', self.adapter)
        self.log = logging.getLogger(__name__)
        self.exception_class = exception_class or ApiException

    def presend(self, request: PreparedRequest):
        """override this function to do things like logging requests
        """
        pass

    def postsend(self, request: PreparedRequest, response: Response):
        """override this function to do things like logging responses
        """
        pass

    def headers(self, *args, **kwargs):
        return {}

    def get_url(self, route):
        if route.startswith('https:') or route.startswith('http:'):
            return route
        base_url = self.base_url
        url = posixpath.join(base_url, route) if base_url else route
        return url

    def send(
            self,
            method: str,
            route: str,
            params: Optional[Dict[str, str]] = None,
            form_data: Optional[Dict[str, str]] = None,
            json_data: Optional[Dict[Any, Any]] = None,
            raw: bool = False,
            **kwargs):
        """base send function that initiates a http/1.1 request
        :param method: the type of request such as `get`, `post`, etc.
        :param route: the anchored route to use, remember that routes are
            prefixed to the `base_url`.
        :param params: a dictionary of query parameters to be included in the url
        :param form_data: a dictionary of values that will be sent in the request
            body as form encoded values
        :param json_data: a dictionary of values that will be sent in the
            request json-encoded
        :param raw: a flag that, if specified, will not cause the raising
            of an `ApiException`.  Use this flag when you need additional
            values out of the response or want to handle errors differently
            than the default.
        """
        headers = self.headers()
        headers.update(kwargs.pop('headers', None) or {})
        timeout = kwargs.pop('timeout', None) or self.default_timeout
        send_kwargs = {}
        if timeout is not None:
            send_kwargs['timeout'] = timeout
        url = self.get_url(route)
        body = None
        if json_data:
            body = json.dumps(json_data, cls=JsonEncoder)
            headers.setdefault('content-type', 'application/json')
        elif form_data:
            body = form_data
            headers.setdefault('content-type', 'application/x-www-form-urlencoded')
        request = Request(
            method, url, headers=headers, data=body,
            params=params, **kwargs)
        request = self.session.prepare_request(request)
        self.presend(request)
        response = self.session.send(request, **send_kwargs)
        self.postsend(request, response)
        if not raw:
            result = self.handle_response(response)
            if result:
                return result
        return response

    def handle_response(self, response: Response) -> Optional[Dict[Any, Any]]:
        """handles responses by returning the json dict or raising an
        `ApiException` for non 200-series responses

        :param response: the response received from the api
        :return: the json dict if we received a successful response or None
        """
        if response.status_code // 100 != 2:
            raise self.exception_class.from_response(response)
        try:
            return response.json()
        except json.JSONDecodeError:  # pragma: nocover
            pass
        return None

    def get(self, route, params=None, **kwargs):
        return self.send('get', route, params=params, **kwargs)

    def post(self, route, form_data=None, json_data=None, **kwargs):
        return self.send(
            'post', route, form_data=form_data, json_data=json_data, **kwargs)

    def put(self, route, form_data=None, json_data=None, **kwargs):
        return self.send(
            'put', route, form_data=form_data, json_data=json_data, **kwargs)

    def delete(self, route, params=None, form_data=None,
               json_data=None, **kwargs):
        return self.send(
            'delete', route, params=params, form_data=form_data,
            json_data=json_data, **kwargs)

    def patch(self, route, params=None, form_data=None,
              json_data=None, **kwargs):
        return self.send(
            'patch', route, params=params, form_data=form_data,
            json_data=json_data, **kwargs)


class BackendOauth2Client(ApiClient):
    def __init__(self, conf, *args, base_url=None, default_timeout=None,
                 exception_class=None, token_url=None,
                 client_id=None, password=None, scopes=None,
                 include_client_id=None, **kwargs):
        super().__init__(
            base_url=base_url or conf.base_url or None,
            default_timeout=default_timeout or conf.default_timeout or None,
            exception_class=exception_class, **kwargs)
        self.token_url = token_url or conf.token_url
        self.client_id = client_id or conf.client_id
        self.token_expires_at = time()
        self.client_secret = password or conf.client_secret or conf.password
        self.scopes = scopes or conf.scopes or []
        self.session = OAuth2Session(client=BackendApplicationClient(
            client_id=self.client_id,
            scope=self.scope))
        self.include_client_id = include_client_id or conf.get('include_client_id')
        self.session.mount('https://', self.adapter)

    @property
    def scope(self):
        if self.scopes:
            scopes = ' '.join(self.scopes)
            return scopes
        return None

    def fetch_token(self, **kwargs):
        tm_now = time()
        self.session.fetch_token(
            self.token_url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            include_client_id=self.include_client_id,
            scope=self.scope,
            **kwargs)
        expires_at = self.session.token.get('expires_at')
        if not expires_at:
            # microsoft apis can use `expires_on`
            expires_at = self.session.token.get('expires_on')
        if not expires_at:
            # some other apis use `expires_in`
            expires_at = self.session.token.get('expires_in') + tm_now
        self.token_expires_at = expires_at - 300

    @classmethod
    def now(cls):
        return datetime.now(utc)

    @property
    def expired(self):
        return time() >= self.token_expires_at

    def presend(self, request: PreparedRequest):
        if self.expired:
            self.fetch_token()
        prepare_bearer_headers(self.session.access_token, request.headers)
