from collections.abc import Awaitable, Callable
from typing import Any
from weakref import WeakMethod, ref

Handler = Callable[..., Any]
AsyncHandler = Callable[..., Awaitable[Any]]
ReferenceType = WeakMethod | ref
SyncReference = WeakMethod[Handler] | ref[Handler]
AsyncReference = WeakMethod[AsyncHandler] | ref[AsyncHandler]
