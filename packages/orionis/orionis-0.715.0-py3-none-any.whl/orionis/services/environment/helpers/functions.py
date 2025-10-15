from typing import Any
from orionis.services.environment.env import Env

def env(key: str, default: Any = None) -> Any:
    """
    Retrieve the value of an environment variable using the Env facade.

    Parameters
    ----------
    key : str
        The name of the environment variable to retrieve.
    default : Any, optional
        The value to return if the environment variable is not found. Defaults to None.

    Returns
    -------
    Any
        The value of the environment variable if it exists, otherwise the specified default value.
    """

    # Retrieve the environment variable using the Env singleton instance.
    return Env.get(key, default)
