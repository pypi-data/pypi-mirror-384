"""Methods to interact with the SNIP Endpoints.

This module provides methods to interact with the SNIP API. The API is used to
fetch data from the SNIP server and to upload data to the SNIP server.
"""

import json
import os

# Any request to the API is made through this deployment URL if not specified otherwise.
DEFAULT_DEPLOYMENT_URL = os.getenv(
    "SNIP_DEPLOYMENT_URL", "https://snip.roentgen.physik.uni-goettingen.de/"
)

# The default request arguments for the API.
ADDITIONAL_REQUEST_ARGS = json.loads(os.getenv("SNIP_ADDITIONAL_REQUEST_ARGS", "{}"))
