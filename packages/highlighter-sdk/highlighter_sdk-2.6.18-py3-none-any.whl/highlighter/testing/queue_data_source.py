import time
from queue import Empty, Queue

from highlighter.agent.capabilities import DataSourceCapability, StreamEvent


class QueueDataSource(DataSourceCapability):
    class StreamParameters(DataSourceCapability.StreamParameters):
        queue: Queue

    def process_frame(self, stream, **kwargs):
        return StreamEvent.OKAY, kwargs

    def frame_generator(self, stream, frame_id):
        queue = self.stream_parameters(stream.stream_id).queue
        try:
            frame_data = queue.get(timeout=0.001)  # Somehow this is faster than queue.get(False)?
            if frame_data == "STOP":
                return StreamEvent.STOP, {}
            return StreamEvent.OKAY, frame_data
        except Empty:
            # We need to keep producing empty frames so that the frame generator
            # gives up the stream lock so frame processing can continue
            return StreamEvent.OKAY, {}

    def start_stream(self, stream, stream_id):
        super().start_stream(stream, stream_id)
        self.create_frames(stream, frame_generator=self.frame_generator)
        return StreamEvent.OKAY, {}

    def stop_stream(self, stream, stream_id):
        queue = self.stream_parameters(stream.stream_id).queue
        queue.put("STOP")
        return super().stop_stream(stream, stream_id)
