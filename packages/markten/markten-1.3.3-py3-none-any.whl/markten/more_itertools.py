import asyncio
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Callable,
    Iterable,
    Iterator,
)
from time import time
from typing import Generic, NoReturn, TypeVar

T = TypeVar("T")


class AsyncReuseIterable(Generic[T]):
    """
    Iterable that runs the given iterable the first time it is iterated,
    and then uses the past results after that.
    """

    def __init__(self, iterable: AsyncIterable[T]) -> None:
        self.__iterable = iterable
        self.__past_values: list[T] = []
        self.__generated = False

    async def __aiter__(self) -> AsyncIterator[T]:
        async def first_iteration():
            self.__generated = True
            async for item in self.__iterable:
                self.__past_values.append(item)
                yield item

        async def later_iterations():
            for val in self.__past_values:
                yield val

        if self.__generated:
            return later_iterations()
        else:
            return first_iteration()


class ReuseIterable(Generic[T]):
    """
    Iterable that runs the given iterable the first time it is iterated,
    and then uses the past results after that.
    """

    def __init__(self, iterable: Iterable[T]) -> None:
        self.__iterable = iterable
        self.__past_values: list[T] = []
        self.__generated = False

    def __iter__(self) -> Iterator[T]:
        def first_iteration():
            self.__generated = True
            for item in self.__iterable:
                self.__past_values.append(item)
                yield item

        def later_iterations():
            yield from self.__past_values

        if self.__generated:
            return later_iterations()
        else:
            return first_iteration()


class AsyncRegenerateIterable(Generic[T]):
    """
    Iterable that reruns the given generator function each time it is iterated.
    """

    def __init__(self, generator: Callable[[], AsyncIterator[T]]) -> None:
        self.__generator = generator

    async def __aiter__(self) -> AsyncIterator[T]:
        return self.__generator()


class RegenerateIterable(Generic[T]):
    """
    Iterable that reruns the given generator function each time it is iterated.
    """

    def __init__(self, generator: Callable[[], Iterator[T]]) -> None:
        self.__generator = generator

    def __iter__(self) -> Iterator[T]:
        return self.__generator()


async def hourglass(interval: float) -> AsyncGenerator[None, NoReturn]:
    """Async iterable that yields a `None` at the given interval.

    Parameters
    ----------
    interval : float
        Time interval in seconds
    """
    while True:
        t_before_yield = time()
        yield None
        await asyncio.sleep(interval - (time() - t_before_yield))
