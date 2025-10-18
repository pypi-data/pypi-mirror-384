"""Synchronous event bus implementation."""

from collections.abc import Callable
from contextlib import suppress
from functools import wraps
from typing import Any, ParamSpec, TypeVar, overload

from bear_dereth.exceptions import HandlerNotFoundError
from bear_utils.events._base_event_bus import BaseEventBus
from bear_utils.events._common import Handler
from bear_utils.events.event_models import BaseEvent, Event

T = TypeVar("T")
P = ParamSpec("P")


class EventBus(BaseEventBus[Handler]):
    """Synchronous event bus for registering and emitting sync handlers only."""

    def register(self, event_name: str, handler: Handler) -> None:
        """Register a sync handler for a given event name.

        Args:
            event_name(str): The name of the event that will be used to call it in emit or fire.
            handler(Handler): The method or function itself to be called later.
        """
        self._handlers[event_name] = self._create_weak_ref(event_name, handler)

    @overload
    def emit(self, event_name: str, event_model: None, **kwargs) -> Event: ...

    @overload
    def emit[T: BaseEvent](self, event_name: str, event_model: T, **kwargs) -> T: ...

    def emit[T: BaseEvent](self, event_name: str, event_model: T | None = None, **kwargs) -> T | Event:
        """Emit an event to registered sync handler and return modified event.

        This is for times when you would expect results from your handlers. If no handler is found,
        the event will have its `msg` attribute set to "No handler registered for event."

        Args:
            event_name(str): The name of the event to emit
            event_model(T) (Optional): The event instance to use. If None, creates its own Event.
            **kwargs: Keyword arguments to pass to Event object if event is None
        Returns:
            T | Event: The processed event, with type matching event_model if provided.
        """
        handler: Handler | None = self._get_handler(event_name)
        # callback: Any = kwargs.pop("callback") # TODO: Do we want to support callbacks here?
        event: T | Event = event_model if event_model is not None else Event(name=event_name, **kwargs)
        if handler is None:
            event.fail(HandlerNotFoundError(event_name))
            return event

        with suppress(Exception):
            event = handler(event)  # Handler will be responsible for calling done() or fail() and error handling
        return event

    def fire(self, event_name: str, **kwargs) -> None:
        """Fire and forget - call handler without expecting return value.

        If handler isn't found, then nothing happens.

        Args:
            event_name(str): The name of the event to fire.
            **kwargs: Arbitrary keyword arguments to pass to the handler.
        """
        handler: Handler | None = self._get_handler(event_name)
        if handler is None:
            return
        with suppress(Exception):
            callback: Any = kwargs.pop("callback", None)
            result: Any = handler(**kwargs)
            if callback is not None and callable(callback):
                callback(result)

    def subscribe(self, event_name: str) -> Callable[..., Callable[P, T]]:  # type: ignore[return-type]
        """Wrapper to register method/function as handler for event name.

        Args:
            event_name(str): The name of the event that will be used to call it in emit or fire.
            handler(Handler): The method or function itself to be called later.

        Returns:
            Handler: The original handler function/method.
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                value: T = func(*args, **kwargs)
                return value

            self.register(event_name, wrapper)
            return wrapper

        return decorator
