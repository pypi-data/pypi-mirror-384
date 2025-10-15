import sys
from orionis.support.facades.console import Console
from orionis.test.contracts.dumper import ITestDumper

class TestDumper(ITestDumper):

    def __isTestCaseClass(self, value) -> bool:
        """
        Check if the provided value is an instance of a recognized test case class.

        Parameters
        ----------
        value : object
            The object to check for test case class membership.

        Returns
        -------
        bool
            True if `value` is an instance of AsyncTestCase, SyncTestCase, unittest.TestCase,
            or unittest.IsolatedAsyncioTestCase. False otherwise or if an import error occurs.
        """

        # If the value is None, it cannot be a test case instance.
        if value is None:
            return False

        try:

            # Attempt to import the test case base classes.
            from orionis.test.cases.asynchronous import AsyncTestCase
            from orionis.test.cases.synchronous import SyncTestCase
            import unittest

            # Check if the value is an instance of either Orionis or native unittest test case class.
            return isinstance(
                value,
                (
                    AsyncTestCase,
                    SyncTestCase,
                    unittest.TestCase,
                    unittest.IsolatedAsyncioTestCase
                )
            )

        except Exception:

            # If imports fail or any other exception occurs, return False.
            return False

    def __valuesToDump(self, args: tuple) -> tuple:
        """
        Filter out test case instances from the provided arguments.

        Parameters
        ----------
        args : tuple
            A tuple of objects to be filtered.

        Returns
        -------
        tuple
            A new tuple containing only the objects that are not instances of recognized
            test case classes.
        """

        values: tuple = ()
        for arg in args:
            if not self.__isTestCaseClass(arg):
                values += (arg,)

        return values

    def __tracebackInfo(self) -> tuple[str | None, int | None]:
        """
        Retrieve the module name and line number of the caller.

        This method inspects the call stack to obtain the module name and line number
        from which it was called. This information is useful for debugging and logging
        purposes, as it provides context about where a function was invoked.

        Returns
        -------
        tuple of (str or None, int or None)
            A tuple containing the module name as a string and the line number as an integer.
            If the information cannot be determined due to an error, returns (None, None).
        """

        try:

            # Get the caller's frame from the call stack (1 level up)
            caller_frame = sys._getframe(2)

            # Retrieve the module name from the caller's global variables
            module = caller_frame.f_globals.get("__name__", None)

            # Retrieve the line number from the caller's frame
            line_number = caller_frame.f_lineno

            # Return the module name and line number
            return (module, line_number)

        except Exception:

            # If any error occurs while retrieving the frame, return (None, None)
            return (None, None)

    def dd(self, *args) -> None:
        """
        Output debugging information and halt further execution.

        Captures the caller's file and line number for context. Temporarily redirects
        standard output and error streams to ensure correct display. If the first argument
        is a recognized test case instance, it is skipped in the output. Raises a custom
        runtime error if dumping fails.

        Parameters
        ----------
        *args : tuple
            Objects to be dumped.

        Returns
        -------
        None
        """

        # Retrieve the caller's module and line number for context
        module, line = self.__tracebackInfo()

        # Filter out test case instances from the arguments
        Console.dump(
            *self.__valuesToDump(args),
            module_path=module,
            line_number=line,
            force_exit=True,        # Halt execution after dumping
            redirect_output=True,   # Redirect stdout/stderr for proper display
            insert_line=True
        )

    def dump(self, *args) -> None:
        """
        Output debugging information without halting execution.

        This method captures the caller's module and line number to provide context for the output.
        It filters out any recognized test case instances from the provided arguments to avoid dumping
        unnecessary or sensitive test case objects. The method then delegates the actual output operation
        to the internal console, ensuring that standard output and error streams are redirected for
        correct display. Unlike `dd`, this method does not terminate the program after dumping.

        Parameters
        ----------
        *args : tuple
            Objects to be dumped. Test case instances are automatically filtered out.

        Returns
        -------
        None
            This method does not return any value. It performs output as a side effect.
        """

        # Retrieve the caller's module and line number for context
        module, line = self.__tracebackInfo()

        # Filter out test case instances from the arguments and output the rest
        Console.dump(
            *self.__valuesToDump(args),
            module_path=module,
            line_number=line,
            force_exit=False,      # Do not halt execution after dumping
            redirect_output=True,  # Redirect stdout/stderr for proper display
            insert_line=True
        )