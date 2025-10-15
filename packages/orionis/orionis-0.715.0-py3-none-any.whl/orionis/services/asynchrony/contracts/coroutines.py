import asyncio
from abc import ABC, abstractmethod
from typing import TypeVar, Union

T = TypeVar("T")

class ICoroutine(ABC):

    @abstractmethod
    def invoke(self, *args, **kwargs) -> Union[T, asyncio.Task, None]:
        """
        Invokes the wrapped coroutine or callable function with the provided arguments.

        This method determines whether the target is a coroutine or a regular callable,
        and executes it accordingly. It adapts to the current event loop context,
        handling both synchronous and asynchronous execution. Exceptions are wrapped
        with context information for easier debugging.

        Parameters
        ----------
        *args : tuple
            Positional arguments to pass to the callable function.
        **kwargs : dict
            Keyword arguments to pass to the callable function.

        Returns
        -------
        Union[T, asyncio.Task, None]
            The result of the coroutine if executed synchronously, an asyncio.Task if scheduled
            for asynchronous execution, or None if the callable is not a coroutine function.

        Raises
        ------
        OrionisCoroutineException
            If an error occurs during coroutine execution.
        RuntimeError
            If an error occurs during callable execution that is not coroutine-related.

        Notes
        -----
        - Only callable objects can be invoked with this method.
        - For coroutine functions, execution context is automatically detected.
        - Non-coroutine callables are executed directly and return None.
        - Exceptions are wrapped with appropriate context information.
        """
        # This method should be implemented by subclasses to handle invocation logic.
        pass

    @abstractmethod
    def run(self) -> Union[T, asyncio.Future]:
        """
        Executes the wrapped coroutine, adapting to the current event loop context.

        This method determines whether to execute the coroutine synchronously or schedule it
        asynchronously based on the presence of an active event loop. It ensures that the coroutine
        is executed in the most appropriate manner for the current context, handling event loop
        issues gracefully.

        Returns
        -------
        Union[T, asyncio.Future]
            The result of the coroutine if executed synchronously, or an asyncio.Future if scheduled
            for asynchronous execution.

        Raises
        ------
        RuntimeError
            If the coroutine cannot be executed due to event loop issues.

        Notes
        -----
        - Executes synchronously if called outside an active event loop and returns the result.
        - Schedules asynchronously if called within an active event loop and returns a Future.
        - Automatically detects the execution context and chooses the appropriate strategy.
        """
        # This method should be implemented by subclasses to handle coroutine execution logic.
        pass