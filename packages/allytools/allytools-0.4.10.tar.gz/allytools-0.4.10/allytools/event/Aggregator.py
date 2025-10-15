from typing import Callable, Dict, List

from .BasicEvents import E, Event, EventType

Subscriber = Callable[[E], None]


class EventAggregator:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Subscriber]] = {}

    def subscribe(self, event_type: EventType, subscriber: Subscriber) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if subscriber not in self._subscribers[event_type]:
            self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type: EventType, subscriber: Subscriber) -> None:
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(subscriber)
                # TODO check if this is necessary (clean entry if no subscribers left)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        if event.event_type in self._subscribers:
            for subscriber in self._subscribers[event.event_type]:
                subscriber(event)
