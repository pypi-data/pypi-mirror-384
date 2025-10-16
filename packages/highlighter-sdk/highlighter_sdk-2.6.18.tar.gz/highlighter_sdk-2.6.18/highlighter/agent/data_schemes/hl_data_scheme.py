import aiko_services as aiko

__all__ = ["HLDataScheme"]


class HLDataScheme(aiko.DataScheme):

    def create_sources(self, stream, data_sources, frame_generator=None, use_create_frame=True):
        task_id = None
        stream.variables["source_paths_generator"] = iter([(url, task_id) for url in data_sources])
        rate, _ = self.pipeline_element.get_parameter("rate", default=None)
        rate = float(rate) if rate else None
        self.pipeline_element.create_frames(stream, frame_generator, rate=rate)
        return aiko.StreamEvent.OKAY, {}


HLDataScheme.add_data_scheme("http", HLDataScheme)
HLDataScheme.add_data_scheme("https", HLDataScheme)
HLDataScheme.add_data_scheme("rtsp", HLDataScheme)
HLDataScheme.add_data_scheme("rtsps", HLDataScheme)
