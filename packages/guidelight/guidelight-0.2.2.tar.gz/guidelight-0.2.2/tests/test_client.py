from guidelight.client import Client
from pytest_httpserver import HTTPServer


def test_preflight():
    """
    Test preflight authentication happens implicitly.
    """

    # Create a test server
    server = HTTPServer()
    server.start()

    # Expect authentication request
    server.expect_request("/v1/authenticate").respond_with_json(
        {
            "access_token": "access",
            "refresh_token": "refresh",
        }
    )

    # Start a guidelight client
    client = Client(
        "http://localhost:%d" % server.port, client_id="id", client_secret="secret"
    )

    # Perform auth required request to trigger the preflight code
    server.expect_request(
        "/v1/authrequired",
        headers={"Authorization": "Bearer access"},
    ).respond_with_json([])
    client.post({}, "/v1/authrequired")
