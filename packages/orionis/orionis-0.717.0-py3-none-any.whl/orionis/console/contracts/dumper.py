from abc import ABC, abstractmethod
from typing import Any

class IDumper(ABC):

    @abstractmethod
    def dd(
        self,
        *args: Any,
        show_types: bool = False,
        show_index: bool = False,
        expand_all: bool = True,
        max_depth: int | None = None,
        module_path: str = None,
        line_number: int = None,
        redirect_output: int = False,
        insert_line: bool = False
    ) -> None:
        """
        Dump the provided variables to the console and terminate execution.

        This method outputs the given variables to the console using the configured
        console instance, then immediately stops program execution. It provides several
        options to customize the output, such as displaying types, indices, expanding
        all nested structures, and limiting the depth of expansion. The output can also
        include information about the module path and line number where the method was called.

        Parameters
        ----------
        *args : Any
            The variables to be dumped to the console.
        show_types : bool, optional
            Whether to display the type of each variable (default is False).
        show_index : bool, optional
            Whether to display the index for each variable in the output (default is False).
        expand_all : bool, optional
            Whether to expand all nested structures in the output (default is True).
        max_depth : int or None, optional
            The maximum depth to which nested structures should be expanded (default is None, meaning no limit).
        module_path : str or None, optional
            The path of the module from which the method is called (default is None).
        line_number : int or None, optional
            The line number in the source code where the method is called (default is None).
        redirect_output : int, optional
            Whether to redirect the output (default is False).
        insert_line : bool, optional
            Whether to insert a separating line before the dump output (default is False).

        Returns
        -------
        None
            This method does not return any value. It outputs the dump information to the console and terminates execution.
        """
        pass

    @abstractmethod
    def dump(
        self,
        *args: Any,
        show_types: bool = False,
        show_index: bool = False,
        expand_all: bool = True,
        max_depth: int | None = None,
        module_path: str = None,
        line_number: int = None,
        redirect_output: int = False,
        insert_line: bool = False
    ) -> None:
        """
        Dump the provided variables to the console for debugging purposes.

        This method outputs the given variables to the console using the configured
        console instance. It provides several options to customize the output, such as
        displaying types, indices, expanding all nested structures, and limiting the
        depth of expansion. The output can also include information about the module
        path and line number where the dump was called.

        Parameters
        ----------
        *args : Any
            The variables to be dumped to the console.
        show_types : bool, optional
            Whether to display the type of each variable (default is False).
        show_index : bool, optional
            Whether to display the index for each variable in the output (default is False).
        expand_all : bool, optional
            Whether to expand all nested structures in the output (default is True).
        max_depth : int or None, optional
            The maximum depth to which nested structures should be expanded (default is None, meaning no limit).
        module_path : str or None, optional
            The path of the module from which the dump is called (default is None).
        line_number : int or None, optional
            The line number in the source code where the dump is called (default is None).
        redirect_output : int, optional
            Whether to redirect the output (default is False).
        insert_line : bool, optional
            Whether to insert a separating line before the dump output (default is False).

        Returns
        -------
        None
            This method does not return any value. It outputs the dump information to the console.
        """
        pass