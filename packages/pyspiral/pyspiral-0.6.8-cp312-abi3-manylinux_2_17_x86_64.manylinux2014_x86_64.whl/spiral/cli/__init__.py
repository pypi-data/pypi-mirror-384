import asyncio
import functools
import inspect
from collections.abc import Callable
from typing import IO, Generic, ParamSpec, TypeVar, override

import typer
from click import ClickException
from grpclib import GRPCError
from httpx import HTTPStatusError
from rich.console import Console

P = ParamSpec("P")
T = TypeVar("T")

CONSOLE = Console()
ERR_CONSOLE = Console(stderr=True, style="red")


class AsyncTyper(typer.Typer, Generic[P]):
    """Wrapper to allow async functions to be used as commands.

    We also pre-bake some configuration.

    Per https://github.com/tiangolo/typer/issues/88#issuecomment-1732469681
    """

    def __init__(self, **kwargs):
        super().__init__(
            no_args_is_help=True,
            pretty_exceptions_enable=False,
            **kwargs,
        )

    @override
    def callback(self, *args, **kwargs) -> Callable[[Callable[P, T]], Callable[P, T]]:
        decorator = super().callback(*args, **kwargs)
        for wrapper in (_wrap_exceptions, _maybe_run_async):
            decorator = functools.partial(wrapper, decorator)
        return decorator

    @override
    def command(self, *args, **kwargs) -> Callable[[Callable[P, T]], Callable[P, T]]:
        decorator = super().command(*args, **kwargs)
        for wrapper in (_wrap_exceptions, _maybe_run_async):
            decorator = functools.partial(wrapper, decorator)
        return decorator


class _ClickGRPCException(ClickException):
    def __init__(self, err: GRPCError):
        super().__init__(err.message or "GRPCError message was None.")
        self.err = err
        self.exit_code = 1

    def format_message(self) -> str:
        if self.err.details:
            return f"{self.message}: {self.err.details}"
        return self.message

    def show(self, file: IO[str] | None = None) -> None:
        ERR_CONSOLE.print(f"Error: {self.format_message()}")


def _maybe_run_async(decorator, f):
    if inspect.iscoroutinefunction(f):

        @functools.wraps(f)
        def runner(*args, **kwargs):
            return asyncio.run(f(*args, **kwargs))

        decorator(runner)
    else:
        decorator(f)
    return f


def _wrap_exceptions(decorator, f):
    @functools.wraps(f)
    def runner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except HTTPStatusError as e:
            raise ClickException(str(e))
        except GRPCError as e:
            raise _ClickGRPCException(e)

    return decorator(runner)
