"""
Implements the API client that manages authentication and cookie state of requests to
and from an Endeavor server. These requests integrate guidelight with Endeavor for AI
projects and training.
"""

import os
import logging

from requests import Response
from platform import python_version
from requests.sessions import Session
from requests.adapters import HTTPAdapter

from .version import get_version
from .credentials import Credentials
from .url import URL, parse_content_type
from .exceptions import ClientError, ServerError
from .exceptions import AuthenticationError, NotFound

try:
    from json import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError


# Setup debug logging for guidelight
logger = logging.getLogger("endeavor")


# Environment variables for local configuration
ENV_URL = "ENDEAVOR_URL"
ENV_CLIENT_ID = "ENDEAVOR_CLIENT_ID"
ENV_CLIENT_SECRET = "ENDEAVOR_CLIENT_SECRET"
ENV_AUTH_URL = "ENDEAVOR_AUTH_URL"

# Default header values
ACCEPT = "application/json"
ACCEPT_LANG = "en-US,en"
ACCEPT_ENCODE = "gzip, deflate, br"
CONTENT_TYPE = "application/json; charset=utf-8"


class Client(object):
    """
    Client manages the connection/session to an Endeavor server and makes API requests.

    Parameters
    ----------
    url : str, optional
        The base URL of the Endeavor server. If not provided, defaults to the value of
        the `ENDEAVOR_URL` environment variable. If neither is set, an error is raised.

    client_id : str, optional
        The client ID of your API key for authentication. If not provided, defaults to
        the value of the `ENDEAVOR_CLIENT_ID` environment variable. If neither is set,
        an error is raised.

    client_secret : str, optional
        The client secret of your API key for authentication. If not provided, defaults
        to the value of the `ENDEAVOR_CLIENT_SECRET` environment variable. If neither is
        set, an error is raised.

    auth_url : str, optional
        The URL of your authentication server (e.g. https://auth.guidelight.dev). If not
        provided, defaults to the value of the `ENDEAVOR_AUTH_URL` environment variable
        and falls back to the url specified otherwise.

    timeout : float, optional
        The number of seconds to wait for a response until error.

    pool_connections : int, default=8
        The number of urllib3 connections to cache in a pool.

    pool_maxsize : int, default=16
        The maximum number of connections to save in the pool.

    max_retries : int, default=3
        The maximum number of retries for a request. Note, this only applies to failed
        DNS lookups, socket connections and connection timeouts, never to requests where
        data has made it to the server.
    """

    def __init__(
        self,
        url=None,
        client_id=None,
        client_secret=None,
        auth_url=None,
        timeout=None,
        pool_connections=8,
        pool_maxsize=16,
        max_retries=3,
    ):
        self._host = None
        self._creds = None
        self._prefix = None

        self.url = url or os.environ.get(ENV_URL, "")
        self.client_id = client_id or os.environ.get(ENV_CLIENT_ID, None)
        self.client_secret = client_secret or os.environ.get(ENV_CLIENT_SECRET, None)
        self.auth_url = auth_url or os.environ.get(ENV_AUTH_URL, None)

        user_agent = f"guidelight/{get_version(short=True)} python/{python_version()}"
        self._headers = {
            "Accept": ACCEPT,
            "Accept-Language": ACCEPT_LANG,
            "Accept-Encoding": ACCEPT_ENCODE,
            "Content-Type": CONTENT_TYPE,
            "User-Agent": user_agent,
        }

        # Configure HTTP requests with the requests library
        self.timeout = timeout
        self.session = Session()
        self.adapter = HTTPAdapter(
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
            max_retries=max_retries,
        )
        self.session.mount(self.prefix + "://", self.adapter)

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        if value is None:
            self._timeout = (10.0, 30.0)
        else:
            self._timeout = value

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._host = None
        self._prefix = None
        self._url = URL.parse(value) if value else None

    @property
    def auth_url(self):
        if self._auth_url is None:
            return self.url
        return self._auth_url

    @auth_url.setter
    def auth_url(self, value):
        self._auth_url = URL.parse(value) if value else None

    @property
    def host(self):
        if self._host is None and self.url:
            parsed = self.url
            if parsed.netloc:
                self._host = parsed.netloc
            else:
                # if a domain is specified then it will be in the path
                self._host = parsed.path.split("/")[0]

        return self._host

    @property
    def prefix(self):
        if self._prefix is None:
            if not self.host:
                raise ValueError("cannot compute prefix without host")

            if self.is_localhost():
                self._prefix = "http"
            else:
                self._prefix = "https"

        return self._prefix

    def status(self):
        """
        Executes a status request to the Endeavor server to verify connectivity and to
        retrieve server version and uptime information.
        """
        return self.get("status", require_authentication=False)

    def get(
        self,
        *endpoint: tuple[str],
        query: dict = None,
        require_authentication: bool = True,
    ) -> dict:
        headers = self._pre_flight(require_authentication=require_authentication)
        url = self._make_endpoint(*endpoint, query=query)

        logger.debug(f"GET {repr(url)}")

        rep = self.session.get(str(url), headers=headers, timeout=self.timeout)

        return self.handle(rep)

    def post(
        self,
        data,
        *endpoint: tuple[str],
        query: dict = None,
        require_authentication: bool = True,
    ) -> dict:
        headers = self._pre_flight(require_authentication=require_authentication)
        url = self._make_endpoint(*endpoint, query=query)

        logger.debug(f"POST {repr(url)}")

        rep = self.session.post(
            str(url), json=data, headers=headers, timeout=self.timeout
        )

        return self.handle(rep)

    def put(
        self,
        data,
        *endpoint: tuple[str],
        query: dict = None,
        require_authentication: bool = True,
    ) -> dict:
        headers = self._pre_flight(require_authentication=require_authentication)
        url = self._make_endpoint(*endpoint, query=query)

        logger.debug(f"PUT {repr(url)}")

        rep = self.session.put(
            str(url), json=data, headers=headers, timeout=self.timeout
        )

        return self.handle(rep)

    def delete(
        self,
        *endpoint: tuple[str],
        query: dict = None,
        require_authentication: bool = True,
    ) -> dict:
        headers = self._pre_flight(require_authentication=require_authentication)
        url = self._make_endpoint(*endpoint, query=query)

        logger.debug(f"DELETE {repr(url)}")

        rep = self.session.delete(str(url), headers=headers, timeout=self.timeout)

        return self.handle(rep)

    def handle(self, rep: Response) -> dict:
        """
        Handle the response from an API request, raising an error if the request failed.
        """
        if rep.status_code == 401 or rep.status_code == 403:
            raise AuthenticationError("authentication failed")

        elif rep.status_code == 204:
            return None

        elif 200 <= rep.status_code < 300:
            mimetype, _ = parse_content_type(rep.headers.get("Content-Type"))
            if mimetype == "application/json":
                return rep.json()
            else:
                return rep.content

        elif 400 <= rep.status_code < 500:
            logger.warning(f"client error: {rep.status_code} {repr(rep.content)}")
            message = f"{rep.status_code} response from {self.host}"

            try:
                err = rep.json()
                if "error" in err:
                    message = err["error"]
                if "errors" in err:
                    message += ":\n  " + "\n  ".join(
                        [f"{e['field']}: {e['error']}" for e in err["errors"]]
                    )
            except JSONDecodeError:
                pass

            if rep.status_code == 404:
                raise NotFound(message)
            else:
                raise ClientError(message)

        elif 500 <= rep.status_code < 600:
            logger.warning(f"server error: {rep.status_code} {repr(rep.content)}")
            message = f"{rep.status_code} response from {self._host}]"

            try:
                err = rep.json()
                if "error" in err:
                    message = err["error"]
            except JSONDecodeError:
                pass

            raise ServerError(message)

        else:
            raise ValueError(f"unhandled status code {rep.status_code}")

    def is_authenticated(self) -> bool:
        """
        Returns True if there are JWT claims with a valid access token
        """
        return self._creds is not None and self._creds.is_authenticated()

    def is_refreshable(self) -> bool:
        """
        Returns True if there are JWT claims with a valid refresh token
        """
        return self._creds is not None and self._creds.is_refreshable()

    def is_localhost(self) -> bool:
        """
        Returns true if the host is a local domain (e.g. localhost)
        """
        host = self.host
        if ":" in host:
            host = host.split(":")[0]
        return host == "localhost" or host.endswith(".local")

    def _make_endpoint(self, *endpoint: tuple[str], query: dict = None) -> URL:
        return self.url.resolve("/", "v1", *endpoint, query=query)

    def _make_auth_endpoint(self, *endpoint: tuple[str], query: dict = None) -> URL:
        return self.auth_url.resolve("/", "v1", *endpoint, query=query)

    def _pre_flight(self, require_authentication: bool = True) -> dict[str, str]:
        if not self.url:
            raise ClientError("no Endeavor URL has been configured")

        request_headers = {}
        request_headers.update(self._headers)

        if require_authentication:
            request_headers.update(self._authentication_headers())
        return request_headers

    def _authentication_headers(self) -> dict[str, str]:
        if not self.is_authenticated():
            # We need to reauthenticate, determin if we can refresh our credentials
            if self.is_refreshable():
                self._creds = self._reauthenticate()
            else:
                self._creds = self._authenticate()

        return {"Authorization": "Bearer " + str(self._creds.access_token)}

    def _authenticate(self) -> Credentials:
        if not self.client_id or not self.client_secret:
            raise AuthenticationError("no client id or secret specified")

        apikey = {"client_id": self.client_id, "client_secret": self.client_secret}
        endpoint = self._make_auth_endpoint("authenticate")
        headers = self._pre_flight(require_authentication=False)

        logger.debug(f"POST {repr(endpoint)}")
        rep = self.session.post(
            str(endpoint), json=apikey, headers=headers, timeout=self.timeout
        )

        rep = self.handle(rep)
        return Credentials(rep["access_token"], rep["refresh_token"])

    def _reauthenticate(self) -> Credentials:
        if not self._creds.refresh_token:
            raise AuthenticationError("no refresh token available")

        refresh = {"refresh_token": str(self._creds.refresh_token)}
        endpoint = self._make_auth_endpoint("reauthenticate")
        headers = self._pre_flight(require_authentication=False)

        logger.debug(f"POST {repr(endpoint)}")
        rep = self.session.post(
            str(endpoint), json=refresh, headers=headers, timeout=self.timeout
        )

        rep = self.handle(rep)
        return Credentials(rep["access_token"], rep["refresh_token"])
