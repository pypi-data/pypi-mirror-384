# Supports data URLs with the following format:
#     data:[<media-type>][;base64],<data>
# https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data
import base64
import io
import re
import urllib

import aiko_services as aiko

DATA_URL_PATTERN = re.compile(
    r"^data:"
    r"(?P<mediatype>[a-zA-Z0-9!#$&^_.+-]+/[a-zA-Z0-9!#$&^_.+-]+)?"  # optional media type
    r"(?P<base64>;base64)?"  # optional ;base64 flag
    r","
    r"(?P<data>.*)$"  # actual data
)


def parse_data_url(data_url):
    match = DATA_URL_PATTERN.match(data_url)
    parsed_url = None
    if match:
        encoded_data = match.group("data")
        if match.group("base64") == ";base64":
            data = base64.b64decode(encoded_data)
        else:
            data = urllib.parse.unquote(encoded_data)
        parsed_url = {"mediatype": match.group("mediatype"), "data": data}
    return parsed_url


class DataSchemeData(aiko.DataScheme):
    def create_sources(self, stream, data_sources, frame_generator=None, use_create_frame=True):
        pipeline_element = self.pipeline_element
        if use_create_frame and len(data_sources) == 1:
            parsed_data = parse_data_url(data_sources[0])
            if parsed_data is None:
                diagnostic = f"Invalid data URL: {data_sources[0]}"
                return aiko.StreamEvent.ERROR, {"diagnostic": diagnostic}
            data = parsed_data["data"]
            pipeline_element.create_frame(stream, {"data": data})
        else:
            source_buffers = []
            content_types = []
            for data_source in data_sources:
                parsed_data = parse_data_url(data_source)
                if parsed_data is None:
                    diagnostic = f"Invalid data URL: {data_source}"
                    return aiko.StreamEvent.ERROR, {"diagnostic": diagnostic}
                data = parsed_data["data"]
                if not isinstance(data, bytes):
                    data = data.encode()
                buffer = io.BufferedReader(io.BytesIO(data))
                source_buffers.append(buffer)
                content_types.append(parsed_data["mediatype"])

            stream.variables["source_buffers"] = source_buffers
            stream.variables["source_buffer_content_types"] = content_types
            rate, _ = pipeline_element.get_parameter("rate", default=None)
            rate = float(rate) if rate else None
            pipeline_element.create_frames(stream, frame_generator, rate=rate)
        return aiko.StreamEvent.OKAY, {}


DataSchemeData.add_data_scheme("data", DataSchemeData)
