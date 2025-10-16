"""
Simple RTSP server using GStreamer for testing VideoReader retry functionality.
Serves an MP4 file as an RTSP stream that can be accessed via rtsp://<host>:<port>/test

The server loops the video by default, automatically seeking back to the start when
the end of the stream is reached. This is useful for testing continuous streaming
and reconnection scenarios.

Usage:
  from highlighter.testing.rtsp_server import RTSPServer
  server = RTSPServer(video_file, port=8554)
  server.run()

  # Or disable looping:
  server = RTSPServer(video_file, port=8554, loop=False)
"""

import signal
import socket
import sys

try:
    import gi

    gi.require_version("Gst", "1.0")
    gi.require_version("GstRtspServer", "1.0")
    from gi.repository import GLib, Gst, GstRtspServer
except ImportError:
    print("Error: GStreamer Python bindings not available.")
    print("Install with: pip install pygobject")
    sys.exit(1)


class _LoopingMediaFactory(GstRtspServer.RTSPMediaFactory):
    """RTSP media factory that notifies the server when media is configured."""

    def __init__(self, server):
        super().__init__()
        self._server = server

    def do_configure(self, media):
        GstRtspServer.RTSPMediaFactory.do_configure(self, media)
        self._server._on_media_configure(self, media)


class RTSPServer:
    """RTSP server for testing video streaming."""

    def __init__(
        self,
        video_file,
        port=8554,
        bind_address="0.0.0.0",
        advertise_host=None,
        tcp_only=False,
        loop=True,  # nosec B104
    ):
        # Note: Binding to 0.0.0.0 is intentional for testing - allows connection from any interface
        self.video_file = str(video_file)
        self.port = port
        self.bind_address = bind_address
        self.advertise_host = advertise_host
        self.tcp_only = tcp_only
        self.loop = loop

        # Initialize GStreamer
        Gst.init(None)

        # Create RTSP server
        self.server = GstRtspServer.RTSPServer()
        # Bind to all interfaces (or a specific one if provided)
        # This makes it reachable over Tailscale as long as tailscale0 is up.
        self.server.set_address(self.bind_address)
        self.server.set_service(str(port))

        # Create media factory
        self.factory = _LoopingMediaFactory(self)

        # Create pipeline string for the video file (video only to avoid audio codec issues)
        pipeline = (
            f'( filesrc location="{self.video_file}" ! '
            "qtdemux name=d "
            "d.video_0 ! queue ! decodebin ! videoconvert ! "
            "x264enc tune=zerolatency speed-preset=veryfast bitrate=1000 ! "
            "rtph264pay name=pay0 pt=96 )"
        )

        self.factory.set_launch(pipeline)
        self.factory.set_shared(True)

        # Enable looping by preventing EOS shutdown
        if self.loop:
            self.factory.set_eos_shutdown(False)

        # Force RTSP TCP interleaved if requested (handy over Tailscale / NAT)
        if self.tcp_only:
            try:
                # GstRtspServer.RTSPLowerTrans is the correct enum for protocols
                self.factory.set_protocols(GstRtspServer.RTSPLowerTrans.TCP)
            except Exception as e:
                print(f"Warning: couldn't force TCP-only transport ({e}). Proceeding with default UDP/TCP.")

        # Attach factory to server
        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/test", self.factory)

        # Server will be attached to main context when start() is called
        self._server_id = None

    def _guess_advertise_host(self):
        # Decide which host to print in the RTSP URL
        if self.advertise_host:
            return self.advertise_host
        # If bound to a specific address, use that; otherwise show the system hostname IP
        if self.bind_address and self.bind_address != "0.0.0.0":  # nosec B104
            return self.bind_address
        # Best-effort: resolve hostname (may show LAN IP). You can also pass --advertise-host 100.x.y.z (Tailscale IP)
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"

    def _on_media_configure(self, factory, media):
        """Configure media so it loops by seeking to the beginning on EOS."""
        if not self.loop:
            return

        pipeline = media.get_element()
        if not pipeline:
            return

        # Find the demuxer element for looping
        demuxer = pipeline.get_by_name("d")  # Named "d" in pipeline string

        # Use a timeout to wait for pads to become available
        if demuxer:
            probe_added = [False]  # Use list to allow modification in closure

            def check_and_add_probe():
                """Check if demuxer pads are ready and add probe."""
                if probe_added[0]:
                    return False  # Stop timeout

                # Check if pipeline is in PAUSED or PLAYING state
                state = pipeline.get_state(0)  # Non-blocking check
                if state[1] >= Gst.State.PAUSED:
                    # Try to add the probe
                    if self._setup_demuxer_probe(demuxer, pipeline):
                        # Send initial SEGMENT seek
                        seek_flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT
                        pipeline.seek_simple(Gst.Format.TIME, seek_flags, 0)
                        probe_added[0] = True
                        return False  # Stop timeout

                return True  # Continue checking

            # Check every 100ms for up to 5 seconds
            GLib.timeout_add(100, check_and_add_probe)
            media._loop_timeout_active = True  # noqa: SLF001

        # Store reference for cleanup (will be garbage collected when media is destroyed)
        media._loop_demuxer = demuxer  # noqa: SLF001

    def _setup_demuxer_probe(self, demuxer, pipeline):
        """Add probe to demuxer pad once it's available. Returns True if successful."""
        # Try to get the video_0 pad
        pad = demuxer.get_static_pad("video_0")
        if pad:
            pad.add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM, self._demuxer_probe_callback, pipeline)
            return True

        # Iterate through source pads to find video pad
        iterator = demuxer.iterate_src_pads()
        while True:
            result, pad = iterator.next()
            if result != Gst.IteratorResult.OK:
                break
            if "video" in pad.get_name():
                pad.add_probe(Gst.PadProbeType.EVENT_DOWNSTREAM, self._demuxer_probe_callback, pipeline)
                return True

        return False  # Pads not ready yet

    def _demuxer_probe_callback(self, pad, info, pipeline):
        """Handle EOS and SEGMENT_DONE events on demuxer pad."""
        event = info.get_event()
        if not event:
            return Gst.PadProbeReturn.OK

        event_type = event.type

        # Intercept EOS and SEGMENT_DONE events
        if event_type == Gst.EventType.EOS or event_type == Gst.EventType.SEGMENT_DONE:
            # Send a new SEGMENT seek to loop back to the beginning
            seek_flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT
            pipeline.seek_simple(Gst.Format.TIME, seek_flags, 0)

            # Mark event as handled (don't propagate downstream)
            return Gst.PadProbeReturn.HANDLED

        return Gst.PadProbeReturn.OK

    def run(self):
        """Start the RTSP server and run the main loop."""
        host_for_url = self._guess_advertise_host()
        print(f"RTSP Server starting...")
        print(f"  Video file     : {self.video_file}")
        print(f"  Bind address   : {self.bind_address}")
        print(f"  Port           : {self.port}")
        print(f"  RTSP URL       : rtsp://{host_for_url}:{self.port}/test")
        if self.tcp_only:
            print(f"  Transport      : TCP (interleaved)")
        else:
            print(f"  Transport      : UDP (default; client may request TCP)")
        print(f"  Looping        : {'enabled' if self.loop else 'disabled'}")

        print("Press Ctrl+C to stop")

        # Create main loop
        self.main_loop = GLib.MainLoop()

        # Attach server to main context
        self._server_id = self.server.attach(None)

        # Handle Ctrl+C
        def signal_handler(sig, frame):
            print("\nShutting down RTSP server...")
            self.main_loop.quit()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            print("\nShutting down RTSP server...")

    def start(self):
        """Start the RTSP server without blocking (for use in tests)."""
        import threading
        import time

        # Create main loop
        self.main_loop = GLib.MainLoop()

        # We need to attach the server in the same thread as the MainLoop
        # Use a flag to track when attachment is complete
        attach_done = threading.Event()

        def run_loop():
            """Run the MainLoop and handle server attachment in the same thread."""
            # Attach server to main context (must happen in the loop thread)
            self._server_id = self.server.attach(None)
            attach_done.set()
            # Run the main loop
            self.main_loop.run()

        # Start the main loop in a background thread
        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

        # Wait for server attachment to complete
        attach_done.wait(timeout=2.0)

        # Give the server a bit more time to fully start
        # time.sleep(0.3)

    def stop(self):
        """Stop the RTSP server and cleanup resources, disconnecting all clients."""
        import warnings

        def cleanup_and_quit():
            """Cleanup active sessions and quit the MainLoop."""
            try:
                # Get the session pool from the server
                session_pool = self.server.get_session_pool()
                if session_pool:
                    # Collect all sessions first
                    sessions_to_close = []

                    def collect_sessions(pool, session, user_data):
                        sessions_to_close.append(session)
                        return False  # Don't remove yet, just collect

                    session_pool.filter(collect_sessions, None)

                    # Now close each session
                    for session in sessions_to_close:
                        try:
                            # Send TEARDOWN to close the session properly
                            session.send_teardown()
                        except Exception as e:
                            # Log but continue - we're shutting down anyway
                            print(f"Warning: failed to teardown session: {e}")
            except Exception as e:
                # If session cleanup fails, continue anyway to quit the loop
                print(f"Warning: session cleanup failed: {e}")

            # Quit the main loop
            self.main_loop.quit()
            return False  # Don't repeat this idle callback

        # Schedule cleanup and quit to run in the MainLoop's thread context
        # This is the thread-safe way to quit a MainLoop from another thread
        if hasattr(self, "main_loop") and self.main_loop:
            if self.main_loop.is_running():
                # Use GLib.idle_add to schedule cleanup in the MainLoop thread
                GLib.idle_add(cleanup_and_quit)

        # Wait for the thread to finish
        if hasattr(self, "thread") and self.thread.is_alive():
            self.thread.join(timeout=5)
            if self.thread.is_alive():
                warnings.warn("RTSP server thread did not stop within timeout")

        # Now we can safely clean up the server ID
        # (the thread has stopped, so no more GLib operations)
        if self._server_id is not None:
            try:
                GLib.source_remove(self._server_id)
            except Exception as e:
                # This might fail if the source was already removed, which is fine
                print(f"Warning: failed to remove GLib source: {e}")
            finally:
                self._server_id = None

    def get_url(self):
        """Get the RTSP URL for this server."""
        host_for_url = self._guess_advertise_host()
        return f"rtsp://{host_for_url}:{self.port}/test"

    @property
    def rtsp_url(self):
        """Get the RTSP URL for this server (property for backwards compatibility)."""
        return self.get_url()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
