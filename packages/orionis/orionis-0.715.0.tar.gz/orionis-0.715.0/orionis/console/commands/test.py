from typing import List
from orionis.console.args.argument import CLIArgument
from orionis.console.base.command import BaseCommand
from orionis.console.exceptions import CLIOrionisRuntimeError
from orionis.foundation.contracts.application import IApplication
from orionis.test.contracts.kernel import ITestKernel

class TestCommand(BaseCommand):
    """
    Command class to execute all automated tests using the configured test kernel for the Orionis application.

    Attributes
    ----------
    timestamps : bool
        Indicates whether timestamps will be shown in the command output.
    signature : str
        The command signature.
    description : str
        A brief description of the command.
    """

    # Indicates whether timestamps will be shown in the command output
    timestamps: bool = False

    # Command signature and description
    signature: str = "test"

    # Command description
    description: str = "Executes all automated tests using the configured test kernel for the Orionis application."

    def options(self) -> List[CLIArgument]:
        """
        Returns the list of command-line options available for the test command.

        This method defines the supported CLI arguments for the test command,
        allowing users to specify additional options such as the modules to test.

        Returns
        -------
        List[CLIArgument]
            A list containing CLIArgument instances that describe the available
            command-line options for the test command.
        """

        # Define the available command-line options for the test command
        return [
            CLIArgument(
                flags=["--module", "-m"],
                type=str,
                default=[],
                help="Specify one or more test modules to execute (can be used multiple times).",
                action="append",
                dest="modules"
            )
        ]

    def handle(self, app: IApplication) -> dict:
        """
        Executes all automated tests using the configured test kernel.

        This method retrieves the test kernel instance from the application container
        and executes the test suite by invoking the kernel's handle method. If any
        exception occurs during execution, it raises a CLIOrionisRuntimeError with
        the error details.

        Parameters
        ----------
        app : IApplication
            The Orionis application instance providing access to the service container.

        Returns
        -------
        dict
            A dictionary containing the results of the test execution, such as test
            statuses, counts, or other relevant information.

        Raises
        ------
        CLIOrionisRuntimeError
            If an unexpected error occurs during the execution of the test command.
        """

        # Attempt to execute the test suite using the test kernel
        try:

            # Retrieve the test kernel instance from the application container
            kernel: ITestKernel = app.make(ITestKernel)

            # Run the test suite using the kernel's handle method
            return kernel.handle(
                modules=self.argument("modules")
            )

        except Exception as e:

            # Raise a CLI-specific runtime error if any exception occurs
            raise CLIOrionisRuntimeError(f"An unexpected error occurred: {e}") from e
