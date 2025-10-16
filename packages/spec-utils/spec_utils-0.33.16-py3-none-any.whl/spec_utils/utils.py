import re
from asyncio import sleep as aio_sleep
from random import choice as r_choice
from string import digits as str_digits, ascii_lowercase as str_letters
from typing import AsyncGenerator, Callable, Any, Optional, List
from pydantic import validate_arguments
from spec_utils.schemas import KwargRelation


class Decorators:

    @staticmethod
    def ensure_session(method: Callable) -> Callable:
        def wrapper(client, *args, **kwargs) -> Optional[Any]:
            if client.session is None:
                raise ConnectionError(
                    f"""
                    Start a session with self.start_session() before of make a
                    request or use "with" expression like with
                    {client.__class__.__name__}(url=...) as client: ...
                    """
                )
            return method(client, *args, **kwargs)

        return wrapper

        return wrapper

    @staticmethod
    @validate_arguments
    def merge_arguments(rels: List[KwargRelation]) -> Callable:
        def inner(method: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> Optional[Any]:
                for rel in rels:
                    if kwargs.get(rel.inner, None):
                        kwargs[rel.outer] = kwargs.get(rel.outer, {})
                        kwargs[rel.outer].update(kwargs.get(rel.inner))
                        if rel.pop_inner:
                            kwargs.pop(rel.inner, None)
                return method(*args, **kwargs)

            return wrapper

        return inner

    @staticmethod
    def ensure_async_session(method: Callable) -> Callable:
        async def wrapper(clt, *args, **kwargs) -> Optional[Any]:
            if clt.session is None or getattr(clt.session, "closed", None):
                msg = str(
                    "Start a session with self.start_session() before of make a "
                    "request or use 'with' expression like async with "
                    f"{clt.__class__.__name__}(url=...) as client: ..."
                )
                raise ConnectionError(msg)
            return await method(clt, *args, **kwargs)

        return wrapper

    @staticmethod
    @validate_arguments
    def async_merge_arguments(rels: List[KwargRelation]) -> Callable:
        def inner(method: Callable) -> Callable:
            async def wrapper(*args, **kwargs) -> Optional[Any]:
                for rel in rels:
                    if kwargs.get(rel.inner, None):
                        kwargs[rel.outer] = kwargs.get(rel.outer, {})
                        kwargs[rel.outer].update(kwargs.get(rel.inner))
                        if rel.pop_inner:
                            kwargs.pop(rel.inner, None)
                return await method(*args, **kwargs)

            return wrapper

        return inner


def random_str(
    size: Optional[int] = 5, chars: Optional[str] = str_digits + str_letters
) -> str:
    """Return a str of 'size' len with numbers and ascii lower letters."""

    return "".join(r_choice(chars) for _ in range(size))


def create_random_suffix(name: Optional[str] = "") -> str:
    """Create a random name adding suffix after of clean recived name."""

    clean = re.sub("[^a-zA-Z0-9]", "_", name)
    clean += "_" if name else ""
    clean += random_str(size=5)

    return clean


async def async_range(
    start: int, stop: int = None, step: int = 1
) -> AsyncGenerator[int, None]:
    if stop:
        range_ = range(start, stop, step)
    else:
        range_ = range(start)
    for i in range_:
        yield i
        await aio_sleep(0)
