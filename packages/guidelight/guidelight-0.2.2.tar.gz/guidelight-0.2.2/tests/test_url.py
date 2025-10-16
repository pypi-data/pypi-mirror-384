import pytest

from guidelight.url import URL, parse_host, parse_content_type


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://example.com/path/to/resource?query=param#fragment",
        "ftp://ftp.example.com/resource",
        "http://example.com:8080",
        "http://localhost",
        "http://localhost:9000/path",
        "http://example.local",
    ],
)
def test_url_parse(url):
    parsed = URL.parse(url)
    assert str(parsed) == url


@pytest.mark.parametrize(
    "url,endpoint,query,expected",
    [
        (
            "https://guidelight.dev",
            ("v1", "agents"),
            None,
            "https://guidelight.dev/v1/agents",
        ),
        (
            "https://guidelight.dev/v1",
            ("agents",),
            None,
            "https://guidelight.dev/v1/agents",
        ),
        (
            "https://guidelight.dev/v1",
            ("/", "v2", "agents"),
            None,
            "https://guidelight.dev/v2/agents",
        ),
        (
            "https://guidelight.dev?ordering=created",
            ("v1", "agents"),
            None,
            "https://guidelight.dev/v1/agents?ordering=created",
        ),
        (
            "https://guidelight.dev?ordering=created",
            ("v1", "agents"),
            {"ordering": "modified"},
            "https://guidelight.dev/v1/agents?ordering=modified",
        ),
        (
            "https://guidelight.dev?ordering=created",
            ("v1", "agents"),
            {"include": "archives"},
            "https://guidelight.dev/v1/agents?ordering=created&include=archives",
        ),
    ],
)
def test_resolve(url, endpoint, query, expected):
    base = URL.parse(url)
    resolved = base.resolve(*endpoint, query=query)
    assert str(resolved) == expected


@pytest.mark.parametrize("input,expected", [
    ("http://example.com", "example.com"),
    ("https://example.com/path", "example.com"),
    ("ftp://ftp.example.com/resource", "ftp.example.com"),
    ("http://example.com:8080", "example.com:8080"),
    ("http://localhost", "localhost"),
    ("http://localhost:9000/path", "localhost:9000"),
    ("http://example.local", "example.local"),
])
def test_parse_host(input, expected):
    actual = parse_host(input)
    assert actual == expected


@pytest.mark.parametrize("input,mime,params", [
    ("text/html; charset=UTF-8", "text/html", {"charset": "UTF-8"}),
    ("application/json", "application/json", {}),
])
def test_parse_content_type(input, mime, params):
    result_mime, result_params = parse_content_type(input)
    assert result_mime == mime
    assert result_params == params
