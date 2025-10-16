from .hl_agent_cli_runner import *
from .patch_capability import *
from .rtsp_server import RTSPServer


class FakeBinaryStdin:
    def __init__(self, buf):
        self.buffer = buf  # binary interface

    def read(self, *args, **kwargs):
        return self.buffer.read(*args, **kwargs)

    def isatty(self):
        return False
