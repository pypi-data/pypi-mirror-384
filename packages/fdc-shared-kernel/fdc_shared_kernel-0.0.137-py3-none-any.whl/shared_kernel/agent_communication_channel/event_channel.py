import queue
from typing import Any, Callable, Optional
import time


class EventChannel:
    def __init__(self, yield_callback: Optional[Callable] = None):
        self.user_to_agent_queue = queue.Queue()
        self.agent_to_user_queue = queue.Queue()
        self.yield_callback = yield_callback or self._default_yield

    def _default_yield(self):
        """Default yield that works in any environment"""
        time.sleep(0.01)

    def set_yield_callback(self, callback: Callable):
        """Set custom yield callback for different environments"""
        self.yield_callback = callback

    # --- user -> agent ---
    def send_user_query(self, user_input: Any):
        self.user_to_agent_queue.put(
            {"event": "UserSendsInput", "payload": {"message": user_input}}
        )

    def wait_for_user_input(self) -> str:
        while True:
            event: dict = self.user_to_agent_queue.get()
            if event.get("event") == "UserSendsInput":
                return event["payload"]["message"]

    # --- agent -> user ---
    def publish_event(self, event_name: str, payload: dict = None):
        self.agent_to_user_queue.put({"event": event_name, "payload": payload or {}})

    # --- user-side convenience ---
    def provide_user_query(self, user_input: Any):
        from shared_kernel.agent_communication_channel.contexts import TaskContext

        return TaskContext(self, user_input, self.yield_callback)
