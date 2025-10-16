import json
import logging
import re
import time
from collections import deque
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, Optional, Tuple
from urllib.parse import urlparse

import av
import numpy as np
from av.error import FFmpegError
from sqlmodel import Session
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from highlighter.agent.capabilities.base_capability import IMAGE, TEXT, VIDEO
from highlighter.agent.capabilities.data_sample_processor import (
    DataSampleProcessor,
    RecordMode,
)
from highlighter.client import download_bytes
from highlighter.client.io import (
    _pil_open_image_bytes,
    _pil_open_image_path,
    _pil_open_image_url,
)
from highlighter.core.data_models.data_sample import DataSample
from highlighter.core.enums import ContentTypeEnum
from highlighter.io.url import is_url_scheme

from .base_capability import DataSourceCapability

__all__ = [
    "ImageDataSource",
    "TextDataSource",
    "JsonArrayDataSource",
    "VideoDataSource",
]

DEFAULT_CONTENT_SEPARATOR = "===END==="
DEFAULT_SAMPLES_PER_FILE = 25 * 10  # frames * seconds

# Stream URL schemes that support reconnection (based on PyAV/FFmpeg protocol support)
STREAMING_URL_SCHEMES = (
    # Real-Time Streaming Protocol
    "rtsp://",
    "rtsps://",
    # Real-Time Messaging Protocol variants
    "rtmp://",
    "rtmpe://",
    "rtmps://",
    "rtmpt://",
    "rtmpte://",
    "rtmpts://",
    # HTTP streams (HLS, DASH, progressive download)
    "http://",
    "https://",
    # UDP and RTP streams
    "udp://",
    "rtp://",
    # TCP streams
    "tcp://",
    # Secure Reliable Transport and RIST
    "srt://",
    "rist://",
    # FTP streams
    "ftp://",
)


def _iter_buffer(
    buffer,
    sep: bytes,
) -> Generator[bytes, None, None]:
    """
    Streams data from stdin until the Nth occurrence of a separator byte sequence.

    sep: The separator byte sequence (e.g., b'\n' or b'\x00\x01')
    """
    if sep is None or len(sep) == 0:
        raise ValueError("Separator must be a non-empty bytes object")

    byte_result = bytearray()
    buffer_remainder = bytearray()

    while True:
        chunk = buffer.read(4096)  # Adjusted for testing, increase for performance
        if not chunk:
            if byte_result:
                byte_result = bytes(byte_result)
                yield byte_result
            break

        buffer_remainder.extend(chunk)

        while True:
            sep_index = buffer_remainder.find(sep)
            if sep_index == -1:
                break

            byte_result.extend(buffer_remainder[:sep_index])
            yield bytes(byte_result)

            byte_result.clear()
            buffer_remainder = buffer_remainder[sep_index + len(sep) :]

        byte_result.extend(buffer_remainder)
        buffer_remainder.clear()


class TextFrameIterator:

    def __init__(
        self,
        source_buffers=None,
        source_urls=None,
        logger=None,
    ):

        self.logger = logger if logger is not None else getLogger("TextFrameIterator")
        self.source_buffers = source_buffers
        self.source_urls = source_urls

        if self.source_urls is not None:
            self.logger.info("TextFrameIterator using source_url")
            self._source = iter([str(u) for u, _ in self.source_urls])
        elif self.source_buffers is not None:

            def iter_buffers(bufs):
                for b in bufs:
                    for item in _iter_buffer(b, "===END===".encode("utf-8")):
                        yield item.decode()

            self._source = iter_buffers(self.source_buffers)
            self.logger.info(f"TextFrameIterator using source_buffer")
        else:
            raise ValueError("Must provide source_buffer &| source_url")

    def _is_local_path(self, p):
        return Path(p).exists()

    def _read_text(self, text_src):
        if self._is_local_path(text_src):
            with open(text_src, "r") as f:
                text = f.read()
            original_source_url = text_src
        elif is_url_scheme(text_src, ["http", "https"]):
            text = download_bytes(text_src).decode("utf-8")
            original_source_url = text_src
        else:
            text = text_src
            original_source_url = None
        return text, original_source_url

    def __iter__(self):
        return self

    def __next__(self):
        text_src = next(self._source)
        text_content, _ = self._read_text(text_src)

        data_sample = DataSample(
            # data_file_id=self.ds.id,
            content=text_content,
            content_type="text",
            stream_frame_index=0,
            media_frame_index=0,
        )
        return data_sample


class TextDataSource(DataSourceCapability):
    """

    TODO: Check/update this

    Example:
        # process a single string
        hl agent start --data-source TextDataSource PIPELINE.json "tell me a joke."

        # process many text files
        ToDo

        # Read from stdin
        cat file | hl agent start --data-source TextDataSource -sp read_stdin=true PIPELINE.json
    """

    stream_media_type = TEXT

    def get_text_frame_generator(self, stream):

        if "source_paths_generator" in stream.variables:
            for frame_data in TextFrameIterator(
                source_buffers=None,
                source_urls=stream.variables["source_paths_generator"],
                logger=self.logger,
            ):
                yield frame_data
        elif "source_buffers" in stream.variables:
            for frame_data in TextFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                logger=self.logger,
            ):
                yield frame_data
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_data_sample(self, stream):

        frame_generator = stream.variables.get("text_frame_generator", None)
        if frame_generator is None:
            frame_generator = self.get_text_frame_generator(stream)
            stream.variables["text_frame_generator"] = frame_generator

        data_sample = next(frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_sample, entities


class JsonArrayFrameIterator:

    def __init__(self, source_buffers=None, source_urls=None, key="", logger=None):

        self.logger = logger if logger is not None else getLogger("JsonArrayFrameIterator")
        self.source_urls = source_urls
        self.source_buffers = source_buffers
        self.key = key

        if self.source_urls is not None:
            self.logger.info("Using source_urls")
            self._source = self._iter_source_urls(self.source_urls)

        elif self.source_buffers is not None:
            self.logger.info("Using source_buffers")
            self._source = self._iter_source_buffers(self.source_buffers)
        else:
            raise ValueError("Must provide source_buffer &| source_url")

    def _is_url(self, p):
        return all([urlparse(p), urlparse(p).netloc])

    def _is_local_path(self, p):
        return Path(p).exists()

    def _iter_source_urls(self, source_urls):
        frame_counter = 0
        for url in source_urls:
            url = str(url)
            if self._is_url(url):
                arr = json.loads(download_bytes(url).decode("utf-8"))
            elif self._is_local_path(url):
                with open(url, "r") as f:
                    arr = json.load(f)
            else:
                raise ValueError(f"Unable to load {url} as json")

            for k in self.key.split("."):
                arr = arr[k]

            for item in arr:
                yield item, url, frame_counter
                frame_counter += 1

    def _iter_source_buffers(self, source_buffers):
        frame_counter = 0
        for buf in source_buffers:
            for item in _iter_buffer(buf, "===END===".encode("utf-8")):
                arr = json.loads(item)

                for k in self.key.split("."):
                    arr = arr[k]

                for item in arr:
                    yield item, None, frame_counter
                    frame_counter += 1

    def __iter__(self):
        return self

    def __next__(self):

        content, _, frame_index = next(self._source)
        data_sample = DataSample(
            # data_file_id=self.ds.id,
            content=content,
            content_type="text",
            stream_frame_index=frame_index,
            media_frame_index=frame_index,
        )
        return data_sample


class JsonArrayDataSource(DataSourceCapability):

    stream_media_type = TEXT

    class StreamParameters(DataSourceCapability.StreamParameters):
        key: str = ""

    def get_json_array_frame_generator(self, stream):
        parameters = self.stream_parameters(stream.stream_id)

        if "source_paths_generator" in stream.variables:
            source_urls = [path for path, _ in stream.variables["source_paths_generator"]]
            for frame_data in JsonArrayFrameIterator(
                source_buffers=None,
                source_urls=source_urls,
                key=parameters.key,
                logger=self.logger,
            ):
                yield frame_data
        elif "source_buffers" in stream.variables:
            for frame_data in JsonArrayFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                key=parameters.key,
                logger=self.logger,
            ):
                yield frame_data
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_data_sample(self, stream):

        json_array_frame_generator = stream.variables.get("json_array_frame_generator", None)
        if json_array_frame_generator is None:
            json_array_frame_generator = self.get_json_array_frame_generator(stream)
            stream.variables["json_array_frame_generator"] = json_array_frame_generator

        data_sample = next(json_array_frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_sample, entities


class OutputType(str, Enum):
    numpy = "numpy"
    pillow = "pillow"


class ImageFrameIterator:
    def __init__(
        self,
        source_buffers=None,
        source_urls=None,
        output_type: OutputType = OutputType.numpy,
        logger=None,
    ):

        self.logger = logger if logger is not None else getLogger("ImageFrameIterator")
        self.source_buffers = source_buffers
        self.source_urls = source_urls
        self.output_type = output_type

        if self.source_urls is not None:
            self.logger.info("ImageFrameIterator using source_url")
            self._source = iter([str(u) for u, _ in self.source_urls])
        elif self.source_buffers is not None:

            def iter_buffers(bufs):
                for b in bufs:
                    for item in _iter_buffer(b, DEFAULT_CONTENT_SEPARATOR.encode("utf-8")):
                        yield item

            self._source = iter_buffers(self.source_buffers)
            self.logger.info(f"ImageFrameIterator using source_buffer")
        else:
            raise ValueError("Must provide source_buffer &| source_url")

        self.frame_index = 0

    def _is_url(self, p):
        return all([urlparse(p), urlparse(p).netloc])

    def _is_local_path(self, p):
        return Path(p).exists()

    def __iter__(self):
        return self

    def _read_image(self, img_src):
        if isinstance(img_src, str) and self._is_local_path(img_src):
            img = _pil_open_image_path(img_src)
            original_source_url = img_src
        elif isinstance(img_src, str) and self._is_url(img_src):
            img = _pil_open_image_url(img_src)
            original_source_url = img_src
        else:
            img = _pil_open_image_bytes(img_src)
            original_source_url = None
        return img, original_source_url

    def __next__(self):
        img_src = next(self._source)
        img, _ = self._read_image(img_src)

        if self.output_type == OutputType.numpy:
            img = np.array(img, dtype=np.uint8)

        data_sample = DataSample(
            content=img,
            content_type=ContentTypeEnum.IMAGE,
            stream_frame_index=0,
            media_frame_index=0,
        )
        return data_sample


class ImageDataSource(DataSourceCapability):
    """

    Example:
        # process a single image
        hl agent start PIPELINE.json image.jpg

        # process many images
        find image/dir/ -n "*.jpg" | hl agent start PIPELINE.json
    """

    stream_media_type = IMAGE

    class StreamParameters(DataSourceCapability.StreamParameters):
        output_type: OutputType = OutputType.numpy

    def get_image_frame_generator(self, stream):
        parameters = self.stream_parameters(stream.stream_id)
        if parameters.record != RecordMode.OFF and parameters.database is None:
            raise ValueError("Missing 'database', required when recording")

        if "source_paths_generator" in stream.variables:
            ifi = ImageFrameIterator(
                source_buffers=None,
                source_urls=stream.variables["source_paths_generator"],
                output_type=parameters.output_type,
                logger=self.logger,
            )
            processor = DataSampleProcessor(
                account_uuid=parameters.account_uuid,
                content_type=ContentTypeEnum.IMAGE,
                data_source_uuid=parameters.data_source_uuid,
                iterator=ifi,
                output_filename_template=parameters.output_filename_template,
                output_folder=parameters.output_folder,
                record=parameters.record,  # <-- enable persistence
                samples_per_file=parameters.samples_per_file,  # batch size
                session_factory=lambda: parameters.database.get_session(),
                writer_opts=parameters.writer_opts,  # forwarded to DataFile.save_local() writer
            )
            for data_sample in processor:
                yield data_sample
        elif "source_buffers" in stream.variables:
            ifi = ImageFrameIterator(
                source_buffers=stream.variables["source_buffers"],
                source_urls=None,
                output_type=parameters.output_type,
                logger=self.logger,
            )
            processor = DataSampleProcessor(
                account_uuid=parameters.account_uuid,
                content_type=ContentTypeEnum.IMAGE,
                data_source_uuid=parameters.data_source_uuid,
                iterator=ifi,
                output_filename_template=parameters.output_filename_template,
                output_folder=parameters.output_folder,
                record=parameters.record,  # <-- enable persistence
                samples_per_file=parameters.samples_per_file,  # batch size
                session_factory=lambda: self.init_parameters.database.get_session(),
                writer_opts=parameters.writer_opts,  # forwarded to DataFile.save_local() writer
            )
            for data_sample in processor:
                yield data_sample
        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_data_sample(self, stream):

        frame_generator = stream.variables.get("image_frame_generator", None)
        if frame_generator is None:
            frame_generator = self.get_image_frame_generator(stream)
            stream.variables["image_frame_generator"] = frame_generator

        data_sample = next(frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_sample, entities


class VideoReader:
    """An iterator for extracting frames from video sources using PyAV.

    This class provides an interface to iterate over video frames from either
    file URLs or in-memory buffers, returning frames as either NumPy arrays or
    PIL Images. It supports frame sampling at a specified FPS and provides
    metadata about the video such as frame count, dimensions, and bitrate.

    Args:
        source_buffer (Optional[bytes]): Iterable of in-memory video buffer. Use io.BytesIO not io.BufferedReader as we pass directly into av.open  eg., av.open(source_buffer)
        source_url (Optional[str]): video file URL or path.
        output_type (OutputType): Format of output frames ('numpy' or 'pillow'). Defaults to OutputType.numpy.
        sample_fps (Optional[float]): Target frames per second for sampling. If None, uses original video FPS.
        sample_frame_idxs (Optional[Iterable[int]]): Target frames by index. If None, uses original video FPS.
        resize_to (Optional[Tuple[int, int]]): If set, each frame is resized via ffmpeg to (width, height) before conversion to RGB/array.
        original_fps (Optional[float]): Override for the original FPS when automatic detection fails. If None, uses stream metadata.
        open_opts (Optional[Dict[str, Any]]): Additional options to pass to av.open(). Useful for RTSP transport settings, error handling, etc.
        logger (Optional[logging.Logger]): Custom logger instance. If None, a default logger is created.

    Raises:
        ValueError: If neither source_buffer nor source_url is provided, or if
        the video source cannot be opened.

    Attributes:
        bit_rate (float): Estimated bitrate of the video in kbps.
        crop_zone (Optional[Tuple[int, int, int, int]]): zone to crop in the video
        current_frame_idx (int): Current frame index of video being iterated over.
        duration_ms (float): Duration of the video in milliseconds.
        frame_interval (int): Number of frames to skip between sampled frames.
        height (int): Height of the video frames in pixels.
        original_fps (float): Original frames per second of the video.
        reconnection_count (int): Number of times the video source has been reconnected.
        sample_fps (float): Frames per second to sample.
        sample_frame_idxs (Iterable[int]): List of frame indexes to sample.
        time_interval_ms (float): Time between sampled frames in milliseconds.
        total_frames (int): Total number of frames in the video.
        width (int): Width of the video frames in pixels.

    Example:
        >>> iterator = VideoReader(source_url="video.mp4", output_type=OutputType.pillow, sample_fps=10.0)
        >>> for frame_data in iterator:
        ...     print(frame_data.media_frame_index, frame_data.recorded_at)
        ...     frame_data.content.save(f"frame_{frame_data.media_frame_index}.png")
    """

    def __init__(
        self,
        source_buffer=None,
        source_url=None,
        output_type: OutputType = OutputType.numpy,
        sample_fps: Optional[float] = None,
        crop_zone: Optional[Tuple[int, int, int, int] | Tuple[float, float, float, float]] = None,
        sample_frame_idxs: Optional[Iterable[int]] = None,
        resize_to: Optional[Tuple[int, int]] = None,
        original_fps: Optional[float] = None,
        open_opts: Optional[Dict[str, Any]] = None,
        logger=None,
        idle_timeout: float = 10.0,
        open_timeout: float = 8.0,
        max_retries: int = 5,
        retry_enabled: Optional[bool] = None,
    ):
        # Public configuration
        self.logger = logger if logger is not None else getLogger("VideoReader")
        self.output_type = output_type
        self.source_url = source_url
        self.source_buffer = source_buffer
        self.idle_timeout = idle_timeout
        self.open_timeout = open_timeout
        self.max_retries = max_retries

        # Smart retry detection: auto-detect if retries make sense based on source type
        if retry_enabled is None:
            self.retry_enabled = self._should_enable_retries()
        else:
            self.retry_enabled = retry_enabled

        # Private configuration
        self._crop_zone = crop_zone
        self._resize_to = resize_to
        self._sample_frame_idxs = sample_frame_idxs
        self._sample_fps = sample_fps

        # Private state
        self._container = None
        self._stream = None
        self._source = None
        self._original_source_url = None
        self._last_frame_time = None
        self._connection_healthy = False
        self._current_frame_idx = -1
        self._fps = None
        self._frame_indexes = None
        self.start_time = None
        self._prev_t = None
        self.intervals_ms = None
        self._reconnection_count = 0

        if (sample_frame_idxs is not None) and (sample_fps is not None):
            raise ValueError("Cannot set both sample_fps and sample_frame_idxs")

        self._sample_frame_idxs = sample_frame_idxs
        self._sample_fps = sample_fps
        self._original_fps_override = original_fps
        self._open_opts = open_opts or {}

        if self.source_url is not None:
            self.logger.info(
                f"Using source URL with PyAV. output_type: {self.output_type}, sample_fps: {self._sample_fps}, resize_to: {self._resize_to}"
            )
            self._source = self.source_url
        elif self.source_buffer is not None:
            self.logger.info(
                f"Using source buffers with PyAV. output_type: {self.output_type}, sample_fps: {self._sample_fps}, resize_to: {self._resize_to}"
            )
            self._source = self.source_buffer
        else:
            raise ValueError("Must provide source_buffer or source_url")

        # Initialize the connection
        self.open()

    def _should_enable_retries(self) -> bool:
        """Determine if retries should be enabled based on source type.

        Enables retries for streaming sources (RTSP, RTMP, HTTP) where temporary
        network issues can be resolved by reconnection. Disables retries for
        local files and BytesIO objects where retries are counterproductive.

        Returns:
            bool: True if retries should be enabled, False otherwise.
        """
        # BytesIO and other buffer objects don't benefit from retries
        if self.source_buffer is not None:
            return False

        # Check if source_url looks like a streaming protocol
        if self.source_url is not None:
            if isinstance(self.source_url, str):
                url_lower = self.source_url.lower()
                # Enable retries for streaming protocols
                if url_lower.startswith(STREAMING_URL_SCHEMES):
                    return True
                # Disable retries for local files
                return False

        # Default to False for safety
        return False

    @property
    def original_fps(self) -> float:
        """Original frame rate of the video."""
        if self._original_fps_override is not None:
            return self._original_fps_override

        stream_fps = self._stream.average_rate or self._stream.rate
        if stream_fps is not None:
            return float(stream_fps)

        raise ValueError(
            "Cannot determine original FPS: stream metadata unavailable and no original_fps override provided. "
            "For RTSP cameras without rate metadata, please specify original_fps parameter."
        )

    @property
    def total_frames(self):
        """Total number of frames in the video."""
        return self._stream.frames

    @property
    def sample_frame_idxs(self):
        return self._sample_frame_idxs

    @property
    def sample_fps(self):
        return self._sample_fps

    @property
    def width(self):
        """Width of the video frames in pixels."""
        return self._stream.width

    @property
    def height(self):
        """Height of the video frames in pixels."""
        return self._stream.height

    @property
    def duration_ms(self):
        """Duration of the video in milliseconds."""
        return (self.total_frames / self.original_fps) * 1000 if self.total_frames else 0

    @property
    def bit_rate(self):
        """Estimated bitrate of the video in kbps."""
        return (self.width * self.height * self.original_fps * 24) / 1000  # 24 bits per pixel (RGB)

    @property
    def time_interval_ms(self):
        """Time between sampled frames in milliseconds."""
        return 1000 / self._fps

    @property
    def frame_interval(self):
        """Number of frames to skip between sampled frames."""
        return max(1, int(round(self.original_fps / self._fps)))

    @property
    def current_frame_idx(self):
        """Current frame index of video being iterated over."""
        return self._current_frame_idx

    @property
    def reconnection_count(self):
        """Number of times the video source has been reconnected."""
        return self._reconnection_count

    # Public API Methods
    def open(self):
        """Open the video source with retry logic if enabled.

        Establishes a connection to the video source (file or stream) and initializes
        the video container for frame reading. If retry_enabled is True, will automatically
        retry on connection failures with exponential backoff.

        Raises:
            ValueError: If the video source cannot be opened after all retry attempts.
            av.error.ExitError: For immediate exit errors (e.g., RTSP connection issues).
            av.error.EOFError: For end-of-stream errors.
            av.error.FFmpegError: For other FFmpeg-related errors.
            OSError: For I/O and network errors.

        Example:
            ```python
            reader = VideoReader(source_url="rtsp://camera/stream", retry_enabled=False)
            reader.open()  # Manually open connection
            ```
        """
        retry_status = (
            f"with retry (max_retries={self.max_retries})" if self.retry_enabled else "without retry"
        )
        self.logger.info(f"Opening video source {retry_status}: {self._source}")

        if self.retry_enabled:
            self._with_retry("Container open", self._open)
        else:
            self._open()

    def close(self):
        """Close the video source and cleanup resources.

        Properly closes the video container and releases any associated resources.
        This method is safe to call multiple times and will not raise errors if
        the container is already closed.

        Note:
            This method is automatically called when the VideoReader object is
            destroyed (via __del__), but it's good practice to call it explicitly
            when you're done with the video source.

        Example:
            ```python
            reader = VideoReader(source_url="video.mp4")
            # ... process frames ...
            reader.close()  # Cleanup resources
            ```
        """
        self._close()

    def reopen(self):
        """Close and reopen the video source.

        Convenience method that closes the current connection and establishes a new one.
        This is useful for recovering from connection issues or resetting the stream
        position. If retry_enabled is True, the reopen will use retry logic.

        This method is automatically called during retry operations when stream
        errors are detected (e.g., RTSP connection drops, idle timeouts).

        Raises:
            ValueError: If the video source cannot be reopened after all retry attempts.
            av.error.ExitError: For immediate exit errors during reopening.
            av.error.EOFError: For end-of-stream errors during reopening.
            av.error.FFmpegError: For other FFmpeg-related errors during reopening.
            OSError: For I/O and network errors during reopening.

        Example:
            ```python
            reader = VideoReader(source_url="rtsp://camera/stream", retry_enabled=True)
            try:
                frame = next(reader)
            except av.error.ExitError:
                reader.reopen()  # Manually recover from connection error
                frame = next(reader)
            ```
        """
        self._reconnection_count += 1
        self.logger.info(f"Reopening video source (reconnection #{self._reconnection_count}): {self._source}")
        self.close()
        self.open()

    def _with_retry(self, operation_name, func, *args, **kwargs):
        """Generic retry wrapper for any operation."""
        if not self.retry_enabled:
            return func(*args, **kwargs)

        @retry(
            retry=retry_if_exception_type((av.error.ExitError, av.error.FFmpegError, OSError)),
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
        )
        def _retry_operation():
            try:
                self.logger.debug(f"Attempting {operation_name} for {self._source}")
                result = func(*args, **kwargs)
                self.logger.debug(f"Successfully completed {operation_name}")
                return result
            except av.error.ExitError as e:
                self.logger.warning(
                    f"RETRY: {operation_name} failed with Exit error: {e}. Source: {self._source}"
                )
                raise
            except av.error.EOFError as e:
                self.logger.warning(
                    f"RETRY: {operation_name} failed with EOF error: {e}. Source: {self._source}. Raising StopIteration"
                )
                raise StopIteration
            except av.error.FFmpegError as e:
                self.logger.warning(
                    f"RETRY: {operation_name} failed with FFmpeg error: {e}. Source: {self._source}"
                )
                raise
            except OSError as e:
                self.logger.warning(
                    f"RETRY: {operation_name} failed with IO error: {e}. Source: {self._source}"
                )
                raise
            except StopIteration as e:
                raise
            except Exception as e:
                self.logger.warning(
                    f"RETRY: {operation_name} failed with unexpected error: {e}. Source: {self._source}"
                )
                raise

        try:
            return _retry_operation()
        except StopIteration as e:
            self.logger.debug("RETRY handled StopInteration")
            raise
        except Exception as final_error:
            self.logger.error(
                f"RETRY EXHAUSTED: {operation_name} failed after {self.max_retries} attempts. Final error: {final_error}. Source: {self._source}"
            )
            raise

    # Private Methods
    def _open(self):
        """Internal method to open video container."""
        self.logger.info(f"Opening video source: {self._source}")
        start_open = time.monotonic()

        try:
            if self._open_opts:
                self._container = av.open(
                    self._source, mode="r", timeout=self.open_timeout, options=self._open_opts
                )
            else:
                self._container = av.open(self._source, mode="r", timeout=self.open_timeout)
            self._stream = self._container.streams.video[0]

            # Try to read start_time from metadata (written by VideoWriter)
            # Check stream metadata first (more specific), then container metadata
            self.start_time = None
            for key in ["recorded_at", "creation_time", "©day"]:
                # Try stream metadata first
                if hasattr(self._stream, "metadata") and key in self._stream.metadata:
                    try:
                        self.start_time = datetime.fromisoformat(self._stream.metadata[key])
                        self.logger.info(f"Using {key} from stream metadata: {self.start_time}")
                        break
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Failed to parse stream {key} metadata: {e}")

                # Fall back to container metadata
                if key in self._container.metadata:
                    try:
                        self.start_time = datetime.fromisoformat(self._container.metadata[key])
                        self.logger.info(f"Using {key} from container metadata: {self.start_time}")
                        break
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Failed to parse container {key} metadata: {e}")

            # Fallback to current time if metadata not available
            if self.start_time is None:
                self.start_time = datetime.now(tz=timezone.utc)
                self.logger.info(f"No metadata timestamp found, using current time: {self.start_time}")

            open_duration = time.monotonic() - start_open
            self.logger.info(f"Successfully opened container in {open_duration:.2f}s")

            self._connection_healthy = True
            self._last_frame_time = time.monotonic()

            if isinstance(self._source, str):
                self._original_source_url = self._source
            else:
                self._original_source_url = None

            self._stream = self._container.streams.video[0]
            self._initialize_frame_sampling()
            self._initialize_performance_tracking()
            self._print_container_info()

        except (av.error.ExitError, av.error.EOFError) as e:
            self.logger.warning(f"Stream exit/EOF error: {e}")
            raise
        except av.error.FFmpegError as e:
            self.logger.error(f"FFmpeg error: {e}")
            raise
        except OSError as e:
            self.logger.error(f"IO error: {e}")
            raise
        except Exception as e:
            self.logger.exception(f"Unexpected error opening container: {e}")
            raise

    def _close(self):
        """Internal method to close video container."""
        self.logger.info(f"closing {self.source_url}")

        try:
            if hasattr(self, "_container") and self._container:
                self._container.close()
                self.logger.debug("Container closed")
        except Exception as e:
            self.logger.debug(f"Error closing container: {e}")
        finally:
            self._container = None
            self._stream = None
            self._connection_healthy = False
            self._current_frame_idx = -1

    def _initialize_frame_sampling(self):
        """Initialize frame sampling parameters."""
        if self._sample_frame_idxs is None:
            if self._sample_fps is None:
                self._fps = self.original_fps
            else:
                self._fps = self._sample_fps
            self._frame_indexes = None  # Will be computed on the fly
        else:
            self._fps = self.original_fps
            self._frame_indexes = iter(self._sample_frame_idxs)

        self._current_frame_idx = -1

    def _initialize_performance_tracking(self):
        """Initialize performance tracking."""
        self._prev_t = time.perf_counter()
        self.intervals_ms = deque(maxlen=150)  # holds up to 150 time-delta values

    def _print_container_info(self):
        fmt = self._container.format.name
        dur_s = (self._container.duration / av.time_base) if self._container.duration else 0.0
        br_kbps = (self._container.bit_rate or 0) / 1_000
        self.logger.info(f"Container: fmt={fmt}, duration={dur_s:.2f}s, br={br_kbps:.0f}kbps")

        # Per‐stream
        for idx, stream in enumerate(self._container.streams):
            cc = stream.codec_context
            stype = stream.type
            codec = cc.name
            if stype == "video":
                w, h = cc.width, cc.height
                fps = float(stream.average_rate or 0.0)
                sbr_kbps = (stream.bit_rate or cc.bit_rate or 0) / 1_000
                self.logger.info(
                    f"Stream #{idx} [video]: codec={codec}, " f"{w}×{h}@{fps:.2f}fps, br={sbr_kbps:.0f}kbps"
                )
            elif stype == "audio":
                sr = cc.sample_rate
                ch = cc.channels
                abr_kbps = (cc.bit_rate or stream.bit_rate or 0) / 1_000
                self.logger.info(
                    f"Stream #{idx} [audio]: codec={codec}, " f"{sr}Hz/{ch}ch, br={abr_kbps:.0f}kbps"
                )
            else:
                self.logger.info(f"Stream #{idx} [{stype}]: codec={codec}")

    def __iter__(self):
        return self

    def __next__(self):
        """Get the next frame from the video source."""
        # Check for idle timeout if retry is enabled
        if (
            self.retry_enabled
            and self._last_frame_time
            and (time.monotonic() - self._last_frame_time) > self.idle_timeout
        ):
            self.logger.warning(f"Idle timeout ({self.idle_timeout}s) - reconnecting...")
            self.reopen()

        if self.retry_enabled:
            frame = self._with_retry("Get next frame", self._get_next_frame)
        else:
            try:
                frame = self._get_next_frame()
            except av.error.EOFError as e:
                self.close()
                self.logger.warning(f"Stream EOF error, stopping iteration.")
                raise StopIteration

        return self._process_frame(frame)

    def _get_next_frame(self):
        """Internal method to get the next frame."""
        if self._sample_frame_idxs is not None:
            return self._seek_to_frame()

        # Sequential decoding with stream reconnection support
        while True:
            for frame in self._container.decode(video=0):
                self._current_frame_idx += 1
                if self.retry_enabled:
                    self._last_frame_time = time.monotonic()

                # Sequential decoding, skip frames not matching the interval
                if self._current_frame_idx % self.frame_interval != 0:
                    continue

                return frame
            else:
                # End of stream - for files this is normal, for RTSP streams we should reconnect
                if (
                    self.retry_enabled
                    and isinstance(self._source, str)
                    and self._source.startswith(STREAMING_URL_SCHEMES)
                ):
                    self.logger.warning("Stream ended unexpectedly - reconnecting...")
                    self.reopen()
                    continue  # Try again after reconnect
                else:
                    self.close()
                    raise StopIteration

    def _process_frame(self, frame):

        crop_zone = self._crop_zone

        resize = self._resize_to
        if resize is not None and (frame.width, frame.height) != resize:
            rw, rh = resize
            frame = frame.reformat(width=rw, height=rh, format="rgb24")
        else:
            frame = frame.to_rgb()  # Ensure frame is RGB

        if self.output_type == OutputType.pillow:
            frame_img = frame.to_image()
        elif self.output_type == OutputType.numpy:
            frame_img = frame.to_ndarray()
        else:
            raise ValueError(f"Invalid Output Type: {self.output_type}")

        if frame.pts is not None and frame.time_base is not None:
            # precise PTS from the stream  → timedelta(seconds=…)
            timestamp = frame.pts * frame.time_base
        else:
            timestamp = self._current_frame_idx / self._fps

        data_sample = DataSample(
            content=frame_img,
            content_type=ContentTypeEnum.IMAGE,
            recorded_at=self.start_time + timedelta(seconds=float(timestamp)),
            stream_frame_index=self._current_frame_idx,
            media_frame_index=self._current_frame_idx,
        )

        # TODO: should we crop and then resize?
        if crop_zone:
            data_samples = data_sample.crop_content([crop_zone], as_data_sample=True)
            data_sample = data_samples[0]

        return data_sample

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.close()

    def _seek_to_frame(self):
        try:
            target_frame_idx = next(self._frame_indexes)
            timestamp = target_frame_idx * (1 / self.original_fps)  # Convert to seconds
            offset = int(timestamp / self._stream.time_base)
            self.logger.debug(f"SEEK: {target_frame_idx} - {offset}")
            self._container.seek(offset, stream=self._stream, backward=True, any_frame=False)
            self._current_frame_idx = target_frame_idx
            frame_iter = self._container.decode(video=0)
            if target_frame_idx == 0:
                frame = next(frame_iter)
            else:
                key_frame = next(frame_iter)
                sec_frame = int(
                    key_frame.pts * self._stream.time_base * self.original_fps
                )  # get the proper key frame number of that timestamp
                if sec_frame == target_frame_idx:
                    self.logger.debug(
                        f"target: {target_frame_idx}, KEY FRAME: {sec_frame}, offset: {0}, keyframe.pts:{key_frame.pts}"
                    )
                    frame = key_frame
                else:
                    for i in range(sec_frame, target_frame_idx):
                        self.logger.debug(
                            f"target: {target_frame_idx}, KEY FRAME: {sec_frame}, offset: {i}, keyframe.pts:{key_frame.pts}"
                        )
                        frame = next(frame_iter)

        except StopIteration:
            self.logger.info("Stopping iteration")
            self.close()
            raise StopIteration

        return frame

    def _log_next_sample_perf(self):
        now = time.perf_counter()
        delta_ms = (now - self._prev_t) * 1_000
        self.intervals_ms.append(delta_ms)
        self._prev_t = now

        # compute + log every 150 frames
        if len(self.intervals_ms) == self.intervals_ms.maxlen:
            avg_ms = sum(self.intervals_ms) / len(self.intervals_ms)
            fps = 1_000 / avg_ms if avg_ms else float("inf")
            self.logger.debug(f"VideoReader: avg {avg_ms:.1f} ms between frames ↔ {fps:.2f} fps (sample=150)")
            self.intervals_ms.clear()


def parse_resize_to(raw: Any) -> Tuple[int, int]:
    """
    Parse a `resize_to` parameter into a (width, height) tuple.

    Accepts either:
      • A string in the form "800x600" or "800X600" (case-insensitive)
      • A sequence (list/tuple) of two ints

    Raises
    ------
    ValueError
        If the string isn’t in WIDTHxHEIGHT format, or the sequence isn’t
        length 2 of ints.
    TypeError
        If `raw` is neither str nor sequence.
    """
    if isinstance(raw, str):
        m = re.match(r"^\s*(\d+)\s*[xX]\s*(\d+)\s*$", raw)
        if not m:
            raise ValueError(
                f"Invalid resize_to string: {raw!r}. " "Expected format WIDTHxHEIGHT, e.g. '640x480'"
            )
        w, h = map(int, m.groups())
        return w, h

    if isinstance(raw, (list, tuple)):
        if len(raw) != 2:
            raise ValueError(f"resize_to sequence must have length 2, got {len(raw)}")
        w, h = raw
        if not (isinstance(w, int) and isinstance(h, int)):
            raise ValueError(f"resize_to elements must be ints, got types {type(w)} and {type(h)}")
        return w, h

    raise TypeError(f"resize_to must be a string or 2-tuple of ints, got {type(raw)}")


class VideoDataSource(DataSourceCapability):

    stream_media_type = VIDEO

    class InitParameters(DataSourceCapability.InitParameters):
        crop_zone: Optional[Tuple[int, int, int, int] | Tuple[float, float, float, float]] = None
        open_opts: Optional[Dict[str, Any]] = None
        original_fps: Optional[float] = None
        output_type: OutputType = OutputType.numpy
        recording_content_type: ContentTypeEnum = ContentTypeEnum.VIDEO
        resize_to: Optional[str] = None
        sample_fps: Optional[float] = None
        samples_per_file: int = DEFAULT_SAMPLES_PER_FILE
        writer_opts: Dict = {}
        idle_timeout: float = 10.0
        open_timeout: float = 8.0
        max_retries: int = 5
        retry_enabled: Optional[bool] = None

    class StreamParameters(InitParameters):
        pass

    def get_video_frame_generator(self, stream):
        parameters = self.stream_parameters(stream.stream_id)
        if parameters.record != RecordMode.OFF and parameters.database is None:
            raise ValueError("Missing 'database' parameter, required when recording")
        resize_to_string = parameters.resize_to
        if resize_to_string is not None:
            resize_to = parse_resize_to(resize_to_string)
        else:
            resize_to = None

        data_file_id = None
        video_data_file_ids = None
        if "video_data_file_ids" in stream.variables:
            video_data_file_ids = stream.variables["video_data_file_ids"]
        if video_data_file_ids is not None:
            assert len(video_data_file_ids) == 1
            data_file_id = video_data_file_ids[0]

        if "source_paths_generator" in stream.variables:
            source_urls = [path for path, task_id in stream.variables["source_paths_generator"]]
            for source_url in source_urls:
                self.logger.info(f"Processing {source_url}")
                vfi = VideoReader(
                    source_buffer=None,
                    source_url=str(source_url),
                    sample_fps=parameters.sample_fps,
                    crop_zone=parameters.crop_zone,
                    resize_to=resize_to,
                    original_fps=parameters.original_fps,
                    open_opts=parameters.open_opts,
                    output_type=parameters.output_type,
                    logger=self.logger,
                    idle_timeout=parameters.idle_timeout,
                    open_timeout=parameters.open_timeout,
                    max_retries=parameters.max_retries,
                    retry_enabled=parameters.retry_enabled,
                )
                writer_opts = {"frame_rate": vfi._fps, **parameters.writer_opts}
                processor = DataSampleProcessor(
                    account_uuid=parameters.account_uuid,
                    content_type=parameters.recording_content_type,
                    data_file_id=data_file_id,
                    data_source_uuid=parameters.data_source_uuid,
                    iterator=vfi,
                    output_filename_template=parameters.output_filename_template,
                    output_folder=parameters.output_folder,
                    record=parameters.record,  # <-- enable persistence
                    samples_per_file=parameters.samples_per_file,  # batch size
                    session_factory=lambda: parameters.database.get_session(),
                    writer_opts=writer_opts,  # forwarded to DataFile.save_local() writer
                )
                for data_sample in processor:
                    yield data_sample

        elif "source_buffers" in stream.variables:
            for source_buffer in stream.variables["source_buffers"]:
                vfi = VideoReader(
                    source_buffer=source_buffer,
                    source_url=None,
                    sample_fps=parameters.sample_fps,
                    crop_zone=parameters.crop_zone,
                    resize_to=resize_to,
                    original_fps=parameters.original_fps,
                    open_opts=parameters.open_opts,
                    output_type=parameters.output_type,
                    logger=self.logger,
                    idle_timeout=parameters.idle_timeout,
                    open_timeout=parameters.open_timeout,
                    max_retries=parameters.max_retries,
                    retry_enabled=parameters.retry_enabled,
                )
                writer_opts = {"frame_rate": vfi._fps, **parameters.writer_opts}
                processor = DataSampleProcessor(
                    account_uuid=parameters.account_uuid,
                    content_type=parameters.recording_content_type,
                    data_file_id=data_file_id,
                    data_source_uuid=parameters.data_source_uuid,
                    iterator=vfi,
                    output_filename_template=parameters.output_filename_template,
                    output_folder=parameters.output_folder,
                    record=parameters.record,  # <-- enable persistence
                    samples_per_file=parameters.samples_per_file,  # batch size
                    session_factory=lambda: parameters.database.get_session(),
                    writer_opts=parameters.writer_opts,  # forwarded to DataFile.save_local()  writer
                )
                for data_sample in processor:
                    yield data_sample

        elif "records" in stream.variables:
            raise NotImplementedError("#### ToDo records ####")
        else:
            raise NotImplementedError("#### ToDo ####")

    def get_next_data_sample(self, stream):
        video_frame_generator = stream.variables.get("video_frame_generator", None)
        if video_frame_generator is None:
            video_frame_generator = self.get_video_frame_generator(stream)
            stream.variables["video_frame_generator"] = video_frame_generator

        data_sample = next(video_frame_generator)
        entities = {}  # ToDo, how/where to load existing entities from
        return data_sample, entities
