"""A module for state tracking in state machines."""

from ._common import MAGIC_FLAG, Auto, get_original, is_auto
from ._decorator import auto_value_decorator
from .state import State
from .state_machine import StateMachine

__all__ = [
    "MAGIC_FLAG",
    "Auto",
    "State",
    "StateMachine",
    "auto_value_decorator",
    "get_original",
    "is_auto",
]
