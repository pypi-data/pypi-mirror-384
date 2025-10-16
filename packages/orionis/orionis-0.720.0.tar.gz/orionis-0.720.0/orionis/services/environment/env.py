from orionis.services.environment.contracts.env import IEnv
from orionis.services.environment.core.dot_env import DotEnv
from typing import Any, Dict

class Env(IEnv):

    # Shared singleton instance for DotEnv
    _dotenv_instance = None

    @classmethod
    def _getSingletonInstance(cls):
        """
        Retrieve the shared DotEnv singleton instance.

        This method ensures that only one instance of DotEnv is created and reused
        throughout the Env class. If the instance does not exist, it will be created.

        Returns
        -------
        DotEnv
            The shared DotEnv instance used for environment variable operations.
        """

        # Check if the singleton instance has already been created
        if cls._dotenv_instance is None:
            # Create a new DotEnv instance if it does not exist
            cls._dotenv_instance = DotEnv()
        # Return the existing or newly created DotEnv instance
        return cls._dotenv_instance

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Retrieve the value of an environment variable by its key.

        Parameters
        ----------
        key : str
            The name of the environment variable to retrieve.
        default : Any, optional
            The value to return if the environment variable is not found. Defaults to None.

        Returns
        -------
        Any
            The value of the environment variable if it exists, otherwise the provided default value.
        """

        # Get the shared DotEnv singleton instance to access environment variables
        dotenv = cls._getSingletonInstance()

        # Return the value for the specified key, or the default if the key is not present
        return dotenv.get(key, default)

    @classmethod
    def set(cls, key: str, value: str, type: str = None) -> bool:
        """
        Set or update an environment variable in the .env file.

        Parameters
        ----------
        key : str
            The name of the environment variable to set or update.
        value : str
            The value to assign to the environment variable.
        type : str, optional
            Type hint for the variable. Supported types include 'str', 'int', 'float',
            'bool', 'list', 'dict', 'tuple', 'set', 'base64', and 'path'. Defaults to None.

        Returns
        -------
        bool
            Returns True if the environment variable was set or updated successfully,
            otherwise returns False.
        """

        # Retrieve the shared DotEnv singleton instance to access environment variable operations
        dotenv = cls._getSingletonInstance()

        # Set the environment variable with the specified key, value, and optional type hint
        return dotenv.set(key, value, type)

    @classmethod
    def unset(cls, key: str) -> bool:
        """
        Remove an environment variable from the .env file.

        Parameters
        ----------
        key : str
            The name of the environment variable to remove.

        Returns
        -------
        bool
            True if the environment variable was removed successfully, False otherwise.
        """

        # Retrieve the shared DotEnv singleton instance to access environment variable operations
        dotenv = cls._getSingletonInstance()

        # Attempt to remove the environment variable with the specified key
        return dotenv.unset(key)

    @classmethod
    def all(cls) -> Dict[str, Any]:
        """
        Retrieve all environment variables as a dictionary.

        This method accesses the shared DotEnv singleton instance and returns all loaded
        environment variables in a dictionary format. It is useful for inspecting the
        current environment configuration.

        Returns
        -------
        dict of str to Any
            A dictionary containing all environment variables loaded by DotEnv.
        """

        # Retrieve the shared DotEnv singleton instance to access environment variables
        dotenv = cls._getSingletonInstance()

        # Return all environment variables as a dictionary
        return dotenv.all()

    @staticmethod
    def isVirtual() -> bool:
        """
        Check if the current Python interpreter is running inside a virtual environment.

        This method detects whether the Python process is executing within a virtual environment
        by inspecting environment variables, configuration files, and interpreter prefixes.

        Returns
        -------
        bool
            Returns True if the interpreter is running inside a virtual environment, otherwise False.
        """

        import sys
        import os
        from pathlib import Path

        # Check for the 'VIRTUAL_ENV' environment variable, which is set by virtualenv
        if 'VIRTUAL_ENV' in os.environ:
            return True

        # Search for 'pyvenv.cfg' in the parent directories of the Python executable (used by venv)
        executable = Path(sys.executable).resolve()
        for parent in executable.parents:

            # If 'pyvenv.cfg' exists in any parent directory, it's likely a venv
            if (parent / 'pyvenv.cfg').exists():
                return True

        # Compare sys.prefix and sys.base_prefix to detect venv or virtualenv usage
        if hasattr(sys, 'base_prefix') and sys.prefix != sys.base_prefix:
            return True

        # If none of the checks indicate a virtual environment, return False
        return False

    @classmethod
    def reload(cls) -> bool:
        """
        Reload environment variables from the .env file.

        This method resets the DotEnv singleton instance and reloads all environment variables
        from the .env file. It is useful when the .env file has been modified externally and
        the latest values need to be reflected in the application.

        Returns
        -------
        bool
            True if the environment variables were reloaded successfully, False otherwise.
        """

        # Reset the singleton instance to ensure a fresh reload of environment variables
        cls._dotenv_instance = None

        # Create a new DotEnv instance and load the .env file
        dotenv = cls._getSingletonInstance()

        # Attempt to reload environment variables from the .env file
        try:
            return dotenv.reload()
        except Exception:
            # Return False if an error occurs during reload
            return False
