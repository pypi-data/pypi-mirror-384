# Version - must match version in pyproject.toml
__version__ = "2.1.1"

# API resources
from .environments import (  # noqa: F401
    DEFAULT_ENV,
    ENVIRONMENT_PRODUCTION,
    ENVIRONMENT_SANDBOX,
    ENVIRONMENT_TEST,
    AVAILABLE_ENVS,
)

# Import API base URLs from constants (tenant-specific)
from .constants import PRODUCTION_API_BASE, SANDBOX_API_BASE  # noqa: F401

# Configuration variables

app_id = None
app_secret = None
private_key = None
env = DEFAULT_ENV

access_token = None

# API base URLs (imported from constants, can be overridden)
production_api_base = PRODUCTION_API_BASE
sandbox_api_base = SANDBOX_API_BASE

api_version = "v2"
verify_ssl_certs = True
proxy = None
default_http_client = None
app_info = None
enable_telemetry = True
max_network_retries = 0

# Set to either 'debug' or 'info', controls console logging
log = None

# API resources
from .api_resources import *  # noqa

# OAuth
from .oauth import OAuth  # noqa

# Webhooks
from .webhook import Webhook, WebhookSignature  # noqa


# Sets some basic information about the running application that's sent along
# with API requests. Useful for plugin authors to identify their plugin when
# communicating with the API.
#
# Takes a name and optional version and plugin URL.
def set_app_info(name, partner_id=None, url=None, version=None):
    global app_info
    app_info = {
        "name": name,
        "partner_id": partner_id,
        "url": url,
        "version": version,
    }
