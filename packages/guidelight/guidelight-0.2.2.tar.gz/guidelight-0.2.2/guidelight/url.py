"""
Simplifies URL parsing and manipulation tasks.
"""

import posixpath

from email.message import Message
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs


class URL(object):
    """
    A helper object to make it easier to work with URLs and create endpoints.
    """

    __slots__ = ("scheme", "netloc", "path", "params", "query", "fragment")

    @classmethod
    def parse(cls, url: str, scheme: str = "", allow_fragments: bool = True) -> "URL":
        parsed = urlparse(url, scheme, allow_fragments)
        return cls(*parsed)

    def __init__(self, scheme, netloc, path, params, query, fragment):
        self.scheme = scheme
        self.netloc = netloc
        self.path = path
        self.params = params
        self.query = query
        self.fragment = fragment

    def resolve(self, *endpoint: str, query: dict = None) -> "URL":
        """
        Resolve the specified endpoint against this URL, returning a new URL object.

        The endpoint is joined with the path of this URL. If any component is an
        absolute path then all previous path components will be discarded.

        If a query is specified, it updates the query parameters of this URL and is
        encoded as a query string on the new URL.
        """
        path = posixpath.join(self.path, *endpoint)
        qs = self.parse_query()
        qs.update(query or {})

        return URL(
            self.scheme,
            self.netloc,
            path,
            self.params,
            urlencode(qs, doseq=True) if qs else "",
            self.fragment,
        )

    def parse_query(self) -> dict[str, list[str]]:
        """
        Parse the query string of this URL into a dictionary.
        """
        if self.query:
            return parse_qs(self.query)
        return {}

    def __str__(self):
        return urlunparse(self)

    def __iter__(self):
        for name in self.__slots__:
            yield getattr(self, name)


def parse_host(url: str) -> str:
    """
    Helper function to extract the host from a URL string.
    """
    parsed = urlparse(url, scheme="https", allow_fragments=False)
    if parsed.netloc:
        return parsed.netloc

    # if a domain is specified then it will be in the path
    return parsed.path.split("/")[0]


def parse_content_type(mime: str) -> tuple[str, dict[str, str]]:
    """
    Helper function to extract the main content type and parameters from a MIME string.
    """
    msg = Message()
    msg["content-type"] = mime
    params = msg.get_params()
    return params[0][0], dict(params[1:])
