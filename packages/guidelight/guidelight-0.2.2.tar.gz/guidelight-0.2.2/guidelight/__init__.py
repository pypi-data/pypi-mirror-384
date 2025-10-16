"""
A library for developing task-oriented AI systems that integrate with Endeavor.
"""

##########################################################################
## Module Info
##########################################################################

# Import the version number at the top level
from .version import get_version, __version_info__


##########################################################################
## Package Version
##########################################################################

__version__ = get_version(short=True)


##########################################################################
## Primary API Entry Point
##########################################################################

from dotenv import load_dotenv
from .client import Client


def connect(url=None, client_id=None, client_secret=None, auth_url=None, timeout=None):
    """
    Create an API client with the specified URL and api key material. If not specified,
    this function will first load any .env files in the local path, then attempt to
    configure the client from the environment.

    Parameters
    ----------
    url : str
        The URL of your Endeavor server (e.g. https://guidelight.dev). If not
        set, it is discovered from the $ENDEAVOR_URL environment variable.

    client_id : str
        The Client ID from your API Key to access your Endeavor server. If not set, it
        is discovered from the $ENDEAVOR_CLIENT_ID environment variable.

    client_secret : str
        The Client Secret from your API Key to access your Endeavor server. If not set,
        it is discovered from the $ENDEAVOR_CLIENT_SECRET environment variable.

    auth_url : str
        The URL of your authentication server (e.g. https://auth.guidelight.dev). If not
        set, it is discovered from the $ENDEAVOR_AUTH_URL environment variable and falls
        back to the url specified otherwise.

    timeout : float
        The number of seconds to wait for a response until error.
    """

    if url is None or client_id is None or client_secret is None or auth_url is None:
        # We need to load information from the environment
        load_dotenv()

    # create the client and perform the pre-flight now to authorize the client
    # now so the client's first actual data request isn't delayed by seconds
    client = Client(
        url=url,
        client_id=client_id,
        client_secret=client_secret,
        auth_url=auth_url,
        timeout=timeout
    )
    client._pre_flight(require_authentication=True)
    return client
