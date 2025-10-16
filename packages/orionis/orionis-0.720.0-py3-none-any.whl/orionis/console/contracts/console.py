from abc import ABC, abstractmethod
from typing import List, Optional

class IConsole(ABC):
    """
    Interface contract for Console output functionality.

    Defines the contract for printing formatted messages to the console with ANSI colors,
    providing methods to print success, info, warning, and error messages with
    optional timestamps, as well as general text formatting methods.
    """

    @abstractmethod
    def success(self, message: str, timestamp: bool = True) -> None:
        """
        Prints a success message with a green background.

        Parameters
        ----------
        message : str
            The success message to print.
        timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        pass

    @abstractmethod
    def textSuccess(self, message: str) -> None:
        """
        Prints a success message in green.

        Parameters
        ----------
        message : str
            The success message to print.
        """
        pass

    @abstractmethod
    def textSuccessBold(self, message: str) -> None:
        """
        Prints a bold success message in green.

        Parameters
        ----------
        message : str
            The success message to print.
        """
        pass

    @abstractmethod
    def info(self, message: str, timestamp: bool = True) -> None:
        """
        Prints an informational message with a blue background.

        Parameters
        ----------
        message : str
            The informational message to print.
        timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        pass

    @abstractmethod
    def textInfo(self, message: str) -> None:
        """
        Prints an informational message in blue.

        Parameters
        ----------
        message : str
            The informational message to print.
        """
        pass

    @abstractmethod
    def textInfoBold(self, message: str) -> None:
        """
        Prints a bold informational message in blue.

        Parameters
        ----------
        message : str
            The informational message to print.
        """
        pass

    @abstractmethod
    def warning(self, message: str, timestamp: bool = True) -> None:
        """
        Prints a warning message with a yellow background.

        Parameters
        ----------
        message : str
            The warning message to print.
        timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        pass

    @abstractmethod
    def textWarning(self, message: str) -> None:
        """
        Prints a warning message in yellow.

        Parameters
        ----------
        message : str
            The warning message to print.
        """
        pass

    @abstractmethod
    def textWarningBold(self, message: str) -> None:
        """
        Prints a bold warning message in yellow.

        Parameters
        ----------
        message : str
            The warning message to print.
        """
        pass

    @abstractmethod
    def fail(self, message: str, timestamp: bool = True) -> None:
        """
        Prints a failure message with a red background.

        Parameters
        ----------
        message : str
            The failure message to print.
        timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        pass

    @abstractmethod
    def error(self, message: str, timestamp: bool = True) -> None:
        """
        Prints an error message with a red background.

        Parameters
        ----------
        message : str
            The error message to print.
        timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        pass

    @abstractmethod
    def textError(self, message: str) -> None:
        """
        Prints an error message in red.

        Parameters
        ----------
        message : str
            The error message to print.
        """
        pass

    @abstractmethod
    def textErrorBold(self, message: str) -> None:
        """
        Prints a bold error message in red.

        Parameters
        ----------
        message : str
            The error message to print.
        """
        pass

    @abstractmethod
    def textMuted(self, message: str) -> None:
        """
        Prints a muted (gray) message.

        Parameters
        ----------
        message : str
            The message to print.
        """
        pass

    @abstractmethod
    def textMutedBold(self, message: str) -> None:
        """
        Prints a bold muted (gray) message.

        Parameters
        ----------
        message : str
            The message to print.
        """
        pass

    @abstractmethod
    def textUnderline(self, message: str) -> None:
        """
        Prints an underlined message.

        Parameters
        ----------
        message : str
            The message to print.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clears the console screen.
        """
        pass

    @abstractmethod
    def clearLine(self) -> None:
        """
        Clears the current line in the console.
        """
        pass

    @abstractmethod
    def line(self) -> None:
        """
        Prints a horizontal line in the console.
        """
        pass

    @abstractmethod
    def newLine(self, count: int = 1) -> None:
        """
        Prints multiple new lines.

        Parameters
        ----------
        count : int, optional
            The number of new lines to print (default is 1).

        Raises
        ------
        ValueError
            If count is less than or equal to 0.
        """
        pass

    @abstractmethod
    def write(self, message: str) -> None:
        """
        Prints a message without moving to the next line.

        Parameters
        ----------
        message : str
            The message to print.
        """
        pass

    @abstractmethod
    def writeLine(self, message: str) -> None:
        """
        Prints a message and moves to the next line.

        Parameters
        ----------
        message : str
            The message to print.
        """
        pass

    @abstractmethod
    def ask(self, question: str) -> str:
        """
        Prompts the user for input with a message and returns the user's response.

        Parameters
        ----------
        question : str
            The question to ask the user.

        Returns
        -------
        str
            The user's input, as a string.
        """
        pass

    @abstractmethod
    def confirm(self, question: str, default: bool = False) -> bool:
        """
        Asks a confirmation question and returns True or False based on the user's response.

        Parameters
        ----------
        question : str
            The confirmation question to ask.
        default : bool, optional
            The default response if the user presses Enter without typing a response.
            Default is False, which corresponds to a 'No' response.

        Returns
        -------
        bool
            The user's response, which will be True if 'Y' is entered,
            or False if 'N' is entered or the default is used.
        """
        pass

    @abstractmethod
    def secret(self, question: str) -> str:
        """
        Prompts the user for hidden input, typically used for password input.

        Parameters
        ----------
        question : str
            The prompt to ask the user.

        Returns
        -------
        str
            The user's hidden input, returned as a string.
        """
        pass

    @abstractmethod
    def table(self, headers: List[str], rows: List[List[str]]) -> None:
        """
        Prints a table in the console with the given headers and rows, with bold headers.

        Parameters
        ----------
        headers : List[str]
            The column headers for the table.
        rows : List[List[str]]
            The rows of the table, where each row is a list of strings representing the columns.

        Raises
        ------
        ValueError
            If headers or rows are empty.

        Notes
        -----
        The table adjusts column widths dynamically, includes bold headers, and uses box-drawing characters for formatting.
        """
        pass

    @abstractmethod
    def anticipate(self, question: str, options: List[str], default: Optional[str] = None) -> str:
        """
        Provides autocomplete suggestions based on user input.

        Parameters
        ----------
        question : str
            The prompt for the user.
        options : List[str]
            The list of possible options for autocomplete.
        default : Optional[str], optional
            The default value if no matching option is found. Defaults to None.

        Returns
        -------
        str
            The chosen option or the default value.

        Notes
        -----
        This method allows the user to input a string, and then attempts to provide
        an autocomplete suggestion by matching the beginning of the input with the
        available options. If no match is found, the method returns the default value
        or the user input if no default is provided.
        """
        pass

    @abstractmethod
    def choice(self, question: str, choices: List[str], default_index: int = 0) -> str:
        """
        Allows the user to select an option from a list.

        Parameters
        ----------
        question : str
            The prompt for the user.
        choices : List[str]
            The list of available choices.
        default_index : int, optional
            The index of the default choice (zero-based). Defaults to 0.

        Returns
        -------
        str
            The selected choice.

        Raises
        ------
        ValueError
            If `default_index` is out of the range of choices.

        Notes
        -----
        The user is presented with a numbered list of choices and prompted to select
        one by entering the corresponding number. If an invalid input is provided,
        the user will be repeatedly prompted until a valid choice is made.
        """
        pass

    @abstractmethod
    def exception(self, e: Exception) -> None:
        """
        Prints an exception message with detailed information.

        Parameters
        ----------
        e : Exception
            The exception to print.

        Notes
        -----
        This method prints the exception type, message, and a detailed stack trace.
        """
        pass

    @abstractmethod
    def exitSuccess(self, message: Optional[str] = None) -> None:
        """
        Exits the program with a success message.

        Parameters
        ----------
        message : Optional[str], optional
            The success message to print before exiting.
        """
        pass

    @abstractmethod
    def exitError(self, message: Optional[str] = None) -> None:
        """
        Exits the program with an error message.

        Parameters
        ----------
        message : Optional[str], optional
            The error message to print before exiting.
        """
        pass

    @abstractmethod
    def dump(
        self,
        *args,
        show_types: bool = True,
        show_index: bool = False,
        expand_all: bool = True,
        max_depth: int | None = None,
        module_path: str | None = None,
        line_number: int | None = None,
        force_exit: bool = False,
        redirect_output: bool = False,
        insert_line: bool = False
    ) -> Optional[str]:
        """
        Displays formatted debug information for one or more variables using Rich, and optionally exports the output as HTML.

        Parameters
        ----------
        *args : Any
            One or more objects to be displayed for debugging.
        show_types : bool, optional
            If True, displays the type of each argument in the panel title. Default is True.
        show_index : bool, optional
            If True, shows an index number for each argument. Default is False.
        expand_all : bool, optional
            If True, expands all nested data structures. Default is True.
        max_depth : int or None, optional
            Maximum depth for nested structures. If None, no limit is applied. Default is None.
        module_path : str or None, optional
            Overrides the module path shown in the header. If None, uses the caller's module path.
        line_number : int or None, optional
            Overrides the line number shown in the header. If None, uses the caller's line number.
        force_exit : bool, optional
            If True, terminates the program after dumping. Default is False.
        redirect_output : bool, optional
            If True, temporarily restores stdout/stderr to their original streams during output. Default is False.
        insert_line : bool, optional
            If True, inserts a blank line before and after the dump output for better readability. Default

        Returns
        -------
        Optional[str]
            An HTML string containing the formatted output if successful, or None if caller information is unavailable.

        Notes
        -----
        This method uses the Rich library to display variables in a visually enhanced format, including type and index information if specified. It can also export the output as HTML for further use.
        """
        pass