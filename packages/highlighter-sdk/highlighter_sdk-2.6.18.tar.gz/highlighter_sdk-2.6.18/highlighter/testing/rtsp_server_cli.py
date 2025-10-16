#!/usr/bin/env python3
"""
CLI entrypoint for RTSP server.

Usage:
  rtsp-server [video_file] [--port 8554] [--host 0.0.0.0] [--advertise-host 100.x.y.z] [--tcp-only] [--no-loop]
"""

import argparse
import sys
from pathlib import Path

# Try relative import first (for installed package), fallback to direct import (for standalone use)
try:
    from .rtsp_server import RTSPServer
except ImportError:
    import importlib.util

    spec = importlib.util.spec_from_file_location("rtsp_server", Path(__file__).parent / "rtsp_server.py")
    rtsp_server = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rtsp_server)
    RTSPServer = rtsp_server.RTSPServer

# Default test video file - resolve to absolute path
DEFAULT_VIDEO_FILE = (
    Path(__file__).parent / "../../../../../web/spec/files/videos/sample_video_360x240x15FPS_5s.mp4"
).resolve()
TEST_VIDEOS_DIR = (Path(__file__).parent / "../../../../../web/spec/files/videos").resolve()


def main():
    parser = argparse.ArgumentParser(description="GStreamer RTSP Server for testing")
    parser.add_argument(
        "video_file", nargs="?", default=str(DEFAULT_VIDEO_FILE), help="Path to MP4 video file"
    )
    parser.add_argument("--port", "-p", type=int, default=8554, help="RTSP server port (default: 8554)")
    parser.add_argument(
        "--host",
        default="0.0.0.0",  # nosec B104
        help="Bind address (use 0.0.0.0 for all interfaces; default: 0.0.0.0)",
    )
    parser.add_argument(
        "--advertise-host",
        default=None,
        help="Host/IP to show in the printed RTSP URL (e.g., your Tailscale IP like 100.x.y.z)",
    )
    parser.add_argument(
        "--tcp-only",
        action="store_true",
        help="Force RTSP over TCP (interleaved) to keep everything on one TCP connection (recommended over Tailscale/NAT).",
    )
    parser.add_argument(
        "--no-loop",
        action="store_true",
        help="Disable looping - stream will end when video file finishes (default: looping enabled)",
    )

    args = parser.parse_args()

    video_path = Path(args.video_file)
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        print("\nAvailable test videos:")
        if TEST_VIDEOS_DIR.exists():
            for mp4_file in TEST_VIDEOS_DIR.glob("*.mp4"):
                print(f"  {mp4_file}")
        sys.exit(1)

    # Create and run RTSP server
    server = RTSPServer(
        video_file=video_path,
        port=args.port,
        bind_address=args.host,
        advertise_host=args.advertise_host,
        tcp_only=args.tcp_only,
        loop=not args.no_loop,
    )
    server.run()


if __name__ == "__main__":
    main()
