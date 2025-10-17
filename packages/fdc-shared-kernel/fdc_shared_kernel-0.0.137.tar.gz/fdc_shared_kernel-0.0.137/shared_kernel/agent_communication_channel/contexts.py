from typing import Any, Callable
from shared_kernel.agent_communication_channel.event_channel import EventChannel
import queue


class TaskContext:
    def __init__(
        self, channel: "EventChannel", user_input: Any, yield_callback: Callable
    ):
        self.channel = channel
        self.user_input = user_input
        self.yield_callback = yield_callback

    def __enter__(self):
        self.channel.send_user_query(self.user_input)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def wait_for_step_function(self):

        while True:
            try:
                event = self.channel.agent_to_user_queue.get(timeout=1)

                et = event.get("event")
                if et == "AgentStepExecutionStart":
                    yield StepContext(
                        self.channel,
                        event["payload"].get("message"),
                        event["payload"].get("is_streaming"),
                        self.yield_callback,
                    )
                elif et == "AgentProcessingEnd":
                    break

            except queue.Empty:
                self.yield_callback()  # yield control back to event loop using callback


class StepContext:
    def __init__(
        self,
        channel: "EventChannel",
        message: str,
        is_streaming: bool,
        yield_callback: Callable,
    ):
        self.channel = channel
        self.is_streaming = is_streaming
        self.message = message
        self.yield_callback = yield_callback

    def wait_for_data(self):
        return ResponseContext(self.channel, self.is_streaming, self.yield_callback)


class ResponseContext:
    def __init__(
        self, channel: "EventChannel", is_stream: bool, yield_callback: Callable
    ):
        self.channel = channel
        self._streaming_started = False
        self._streaming_ended = False
        self._step_ended = False
        self._final_data = None
        self.is_stream = is_stream
        self.yield_callback = yield_callback

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def is_streaming(self):
        return self.is_stream

    def stream(self):
        while True:
            try:
                event = self.channel.agent_to_user_queue.get(timeout=1)

                et = event.get("event")
                if et == "AgentDataStreamingStart":
                    self._streaming_started = True
                    continue
                if et == "AgentDataStreamChunk":
                    yield event["payload"]["chunk"]
                    continue
                if et == "AgentDataStreamingEnd":
                    self._streaming_ended = True
                    break
                if et == "AgentDataResponse":
                    self._final_data = event["payload"].get("response")
                    break
                if et == "AgentStepExecutionEnd":
                    self._step_ended = True
                    break
                continue
            except queue.Empty:
                self.yield_callback()  # yield control back to event loop using callback

    def data(self):
        if self._final_data is not None:
            return self._final_data

        while True:
            try:
                event = self.channel.agent_to_user_queue.get(timeout=1)

                et = event.get("event")
                if et == "AgentDataResponse":
                    self._final_data = event["payload"].get("response")
                    return self._final_data
                if et == "AgentDataStreamingEnd":
                    self._streaming_ended = True
                    return None
                if et == "AgentStepExecutionEnd":
                    self._step_ended = True
                    return None
                if et == "AgentDataStreamingStart":
                    self._streaming_started = True
                    continue
                if et == "AgentDataStreamChunk":
                    continue
                continue
            except queue.Empty:
                self.yield_callback()  # yield control back to event loop using callback
