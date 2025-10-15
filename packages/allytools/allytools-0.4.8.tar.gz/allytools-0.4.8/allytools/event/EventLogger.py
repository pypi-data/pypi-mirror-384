from datetime import datetime

from .BasicEvents import Event, EventType


def get_current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class EventLogger:
    def __init__(self, log_vm):
        super().__init__()
        self.log_vm = log_vm

    def update(self, event: Event):
        if not isinstance(event.event_type, EventType):
            raise TypeError(f"Expected EventType, got {type(event.event_type)}")
        message_template = str(event.event_type) + event.message
        self.log_update(message_template)

    def log_update(self, message: str):
        timestamped_message = f"[{get_current_timestamp()}] {message}"
        self.log_vm.add_log_message(timestamped_message)
