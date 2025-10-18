"""Event system models using Pydantic for type safety and validation."""

from enum import IntEnum
from types import ModuleType
from typing import Any, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from bear_dereth.lazy_imports import lazy
from bear_epoch_time import EpochTimestamp

json: ModuleType = lazy("json")


ISO_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


class EventPriority(IntEnum):
    """Event priority levels for handler execution order."""

    LOWEST = 0
    LOW = 25
    NORMAL = 50
    HIGH = 75
    HIGHEST = 100


class BaseEvent(BaseModel):
    """Base class for all events in the system."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    event_id: UUID = Field(default_factory=uuid4)
    msg: str | None = None
    timestamp: EpochTimestamp = Field(default_factory=EpochTimestamp.now)
    success: bool = True
    exception: Exception | None = None
    returncode: int | None = None

    @field_serializer("timestamp")
    def serialize_timestamp(self, ts: EpochTimestamp) -> str:
        """Serialize the timestamp to an ISO 8601 string."""
        return ts.to_string(fmt=ISO_FORMAT)

    @field_serializer("event_id")
    def serialize_event_id(self, eid: UUID) -> str:
        """Serialize the event_id to a string."""
        return str(eid)

    @field_serializer("exception")
    def serialize_exception(self, exc: Exception | None) -> str | None:
        """Serialize the exception to its string representation."""
        return str(exc) if exc is not None else None

    def ts_to_string(self, fmt: str) -> str:
        """Return the timestamp as a human-readable string."""
        return self.timestamp.to_string(fmt=fmt)

    def _base_done(self, msg: str = "") -> Self:
        """Update the event's timestamp to the current time."""
        self.msg = msg
        self.timestamp = EpochTimestamp.now()
        return self

    def fail(self, exception: Exception) -> None:
        """Mark the event as failed with an exception message."""
        self.success = False
        self.exception = exception

    def done(self, result: Any, msg: str = "") -> Self:
        """Tasks to complete when event processing is done.

        Args:
            msg (str): Message indicating the status of event processing.
        """
        raise NotImplementedError("Subclasses must implement done method")


class Event[T_Input, T_Results](BaseEvent):
    """Generic event with typed data payload."""

    input_data: T_Input | None = Field(default=None)
    results: T_Results | None = Field(default=None)

    def _insert_results(self, result: T_Results) -> None:
        """Insert results into the event."""
        self.results = result

    def done(self, result: T_Results, msg: str = "") -> Self:
        """Tasks to complete when event processing is done.

        Args:
            msg (str): Message indicating the status of event processing.
            **kwargs: Additional keyword arguments to be passed to insert_results.
                result (T_Results): The results to insert into the event.
        """
        super()._base_done(msg=msg)
        self._insert_results(result)
        return self


if __name__ == "__main__":  # pragma: no cover
    # Example usage and test cases
    event: Event[int, str] = Event[int, str](name="TestEvent", input_data=42)
    print("Initial Event:", event.model_dump_json(indent=2))

    event.done(result="The answer is 42", msg="Processing complete")
    print("Completed Event:", event.model_dump_json(indent=2))

    event.fail(exception=ValueError("An error occurred"))
    print("Failed Event:", event.model_dump_json(indent=2))
