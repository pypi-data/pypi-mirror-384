from typing import Any, Dict
from abc import ABC, abstractmethod

class IEnv(ABC):

    @classmethod
    @abstractmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Retrieves the value of the specified environment variable.

        Parameters
        ----------
        key : str
            The name of the environment variable to retrieve. Must be a valid
            environment variable name (uppercase, numbers, underscores).
        default : Any, optional
            The value to return if the environment variable is not found. 
            Can be any type (str, int, bool, list, etc.). Defaults to None.

        Returns
        -------
        Any
            The value of the environment variable if it exists, automatically
            parsed to its appropriate Python type (str, int, float, bool, list, dict, etc.),
            otherwise the default value.
        """
        pass

    @classmethod
    @abstractmethod
    def set(cls, key: str, value: str, type: str = None) -> bool:
        """
        Sets the value of an environment variable in the .env file.

        Parameters
        ----------
        key : str
            The name of the environment variable to set. Must follow the pattern:
            uppercase letters, numbers, and underscores only, starting with a letter.
            Example: 'DATABASE_URL', 'MAX_CONNECTIONS', 'FEATURE_FLAGS'
        value : str
            The value to assign to the environment variable.
        type : str, optional
            Optional type hint for explicit type casting. Supported types:
            - 'str': String values
            - 'int': Integer values
            - 'float': Floating-point values
            - 'bool': Boolean values (true/false)
            - 'list': List/array values
            - 'dict': Dictionary/object values
            - 'tuple': Tuple values
            - 'set': Set values
            - 'base64': Base64 encoded values
            - 'path': File system path values
            Defaults to None (automatic type detection).

        Returns
        -------
        bool
            True if the environment variable was set successfully, False otherwise.
        """
        pass

    @classmethod
    @abstractmethod
    def unset(cls, key: str) -> bool:
        """
        Removes the specified environment variable from the .env file.

        Parameters
        ----------
        key : str
            The name of the environment variable to remove.

        Returns
        -------
        bool
            True if the environment variable was removed successfully, False otherwise.
        """
        pass

    @classmethod
    @abstractmethod
    def all(cls) -> Dict[str, Any]:
        """
        Retrieves all environment variables as a dictionary.

        Returns
        -------
        dict of str to Any
            A dictionary containing all environment variables loaded by DotEnv.
        """
        pass

    @classmethod
    @abstractmethod
    def reload(cls) -> bool:
        """
        Reload environment variables from the .env file.

        This method forces a refresh of all environment variables from the .env file,
        useful when the file has been modified externally.

        Returns
        -------
        bool
            True if the reload was successful, False otherwise.
        """
        pass