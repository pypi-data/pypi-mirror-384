"""Interface with schema related endpoints.

Provides functions to retrieve available schemas and specific schema details from a given snip deployment.
"""

from typing import Dict, Optional

from . import DEFAULT_DEPLOYMENT_URL
from .request import request


def get_available_schemas(deployment: Optional[str] = None, **kwargs) -> list[str]:
    """Get all available schemas from the deployment.

    Parameters
    ----------
    deployment : str, optional
        The deployment to get the available schemas from.
        If None, the default deployment is used.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.get function.

    Returns
    -------
    list[str]
        The list of available schemas.

    Raises
    ------
    requests.HTTPError
        If the request to the deployment fails. Should only happen if the deployment is not reachable.

    """
    if deployment is None:
        deployment = DEFAULT_DEPLOYMENT_URL

    data = request("GET", f"{deployment}/schemas/json", **kwargs)

    if data is None:
        raise ValueError("No data returned from the API.")

    if not isinstance(data, list):
        raise ValueError("Invalid data returned from the API.")

    return data


def get_schema(name: str, deployment: Optional[str] = None, **kwargs) -> Dict:
    """Get a schema from the deployment.

    Parameters
    ----------
    name : str
        The name of the schema to retrieve i.e. its identifier e.g. "text" or "uprp/timestamp"
    deployment : str, optional
        The deployment to get the schema from.
        If None, the default deployment is used.
    **kwargs: Any
        Additional keyword arguments to pass to the requests.get function.

    Returns
    -------
    Dict
        The schema object.

    Raises
    ------
    requests.HTTPError
        If the request to the deployment fails. Can happen if the deployment is not reachable or if the schema is not found.
        Check the response for more information.

    """
    if deployment is None:
        deployment = DEFAULT_DEPLOYMENT_URL

    data = request("GET", f"{deployment}/schemas/json/{name}", **kwargs)

    if data is None:
        raise ValueError("No data returned from the API.")

    if not isinstance(data, dict):
        raise ValueError("Invalid data returned from the API.")

    return data
