from abc import ABC
from dataclasses import dataclass
from typing import TypeVar


class IterableConstants(type):
    def __iter__(cls):
        for attr in dir(cls):
            if not attr.startswith("_") and not callable(getattr(cls, attr)):
                yield getattr(cls, attr)


class EventType:
    def __init__(self, name: str, label: str):
        self.name = name
        self.label = label

    def __str__(self):
        return self.label

    def __repr__(self):
        return f"EventType(name='{self.name}', label='{self.label}')"

    def __eq__(self, other):
        return isinstance(other, EventType) and self.name == other.name

    def __hash__(self):
        return hash(self.name)


class EventTypes(metaclass=IterableConstants):
    ERROR_OCCURRED = EventType("ERROR_OCCURRED", "General error occurred -")


@dataclass
class Event(ABC):
    event_type: EventTypes
    message: str


@dataclass
class LogEvent(Event):
    pass


@dataclass
class ErrorOccurredEvent(Event):
    pass


E = TypeVar("E", bound=Event)
