import asyncio
from typing import Any, Callable, Coroutine as TypingCoroutine, TypeVar, Union
from orionis.services.asynchrony.contracts.coroutines import ICoroutine
from orionis.services.asynchrony.exceptions import OrionisCoroutineException
from orionis.services.introspection.objects.types import Type

T = TypeVar("T")

class Coroutine(ICoroutine):

    def __init__(self, func: Union[TypingCoroutine[Any, Any, T], Callable[..., TypingCoroutine[Any, Any, T]]]) -> None:
        """
        Initializes a Coroutine wrapper to manage and execute coroutine objects or functions.

        This constructor accepts either a coroutine object or a callable that returns a coroutine.
        The wrapped coroutine or function can be executed later using the run() or invoke() methods.

        Parameters
        ----------
        func : Union[TypingCoroutine[Any, Any, T], Callable[..., TypingCoroutine[Any, Any, T]]]
            The coroutine object or a callable that returns a coroutine to be managed.

        Returns
        -------
        None
            This method does not return any value.

        Notes
        -----
        - Type validation is deferred until execution.
        - Accepts both coroutine objects and coroutine functions.
        """

        # Store the coroutine object or callable for later execution
        self.__func = func

    def invoke(self, *args, **kwargs) -> Union[T, asyncio.Task, None]:
        """
        Invokes the callable coroutine function or regular function with the provided arguments.

        This method executes a callable coroutine function or a regular function using the given
        positional and keyword arguments. It automatically detects whether the function is asynchronous
        and adapts execution to the current event loop context. Exceptions are handled and wrapped
        appropriately.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to the callable function.
        **kwargs : dict
            Keyword arguments to pass to the callable function.

        Returns
        -------
        Union[T, asyncio.Task, None]
            The result of the coroutine if executed synchronously,
            an asyncio.Task if scheduled for asynchronous execution,
            or the result of a regular callable.

        Raises
        ------
        OrionisCoroutineException
            If an error occurs during coroutine execution.
        RuntimeError
            If an unexpected error occurs during callable execution.

        Notes
        -----
        - Only callable objects can be invoked with this method.
        - For coroutine functions, execution context is automatically detected.
        - Non-coroutine callables are executed directly.
        - Exceptions are wrapped with appropriate context information.
        """

        # Ensure the stored object is callable before invocation
        if not callable(self.__func):
            raise OrionisCoroutineException(
                f"Cannot invoke non-callable object of type {type(self.__func).__name__}"
            )

        try:
            # Check if the callable is a coroutine function
            if asyncio.iscoroutinefunction(self.__func):

                # Create the coroutine object using provided arguments
                coroutine_obj = self.__func(*args, **kwargs)

                try:
                    # Attempt to get the currently running event loop
                    loop = asyncio.get_running_loop()

                    # Schedule the coroutine for asynchronous execution and return the Task
                    return loop.create_task(coroutine_obj)

                except RuntimeError:
                    # No running event loop; execute the coroutine synchronously

                    try:
                        # Use asyncio.run to execute the coroutine and return its result
                        return asyncio.run(coroutine_obj)

                    except Exception as e:
                        # Wrap and raise any exceptions that occur during synchronous execution
                        raise OrionisCoroutineException(
                            f"Failed to execute coroutine synchronously: {str(e)}"
                        ) from e

            else:
                # Execute regular callable directly and return its result
                return self.__func(*args, **kwargs)

        except OrionisCoroutineException:
            # Re-raise custom exceptions as-is
            raise

        except Exception as e:
            # Wrap and raise any other exceptions that occur during invocation
            raise RuntimeError(
                f"Unexpected error during callable invocation: {str(e)}"
            ) from e

    def run(self) -> Union[T, asyncio.Future]:
        """
        Executes the wrapped coroutine, adapting execution to the current event loop context.

        This method determines whether to execute the coroutine synchronously or schedule it
        for asynchronous execution based on the presence of an active event loop. It validates
        that the stored object is a coroutine before execution.

        Returns
        -------
        Union[T, asyncio.Future]
            The result of the coroutine if executed synchronously, or an asyncio.Future if scheduled
            for asynchronous execution.

        Raises
        ------
        OrionisCoroutineException
            If the stored object is not a coroutine.
        RuntimeError
            If the coroutine cannot be executed due to event loop issues.

        Notes
        -----
        - If called outside an active event loop, the coroutine is executed synchronously and its result is returned.
        - If called within an active event loop, the coroutine is scheduled for asynchronous execution and a Future is returned.
        - The method automatically detects the execution context and chooses the appropriate execution strategy.
        """

        # Validate that the provided object is a coroutine
        if not Type(self.__func).isCoroutine():
            raise OrionisCoroutineException(
                f"Expected a coroutine object, but got {type(self.__func).__name__}."
            )

        # Attempt to get the currently running event loop
        try:
            loop = asyncio.get_running_loop()

        # No running event loop; execute the coroutine synchronously and return its result
        except RuntimeError:
            return asyncio.run(self.__func)

        # If inside an active event loop, schedule the coroutine and return a Future
        if loop.is_running():
            return asyncio.ensure_future(self.__func)

        # If no event loop is running, execute the coroutine synchronously using the loop
        else:
            return loop.run_until_complete(self.__func)
