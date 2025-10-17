"""Debug module for testing streaming gateway without external dependencies.

This module provides mock implementations for testing the streaming pipeline
without requiring Kafka, Redis, or API connectivity.

Example usage:
    from matrice_streaming.streaming_gateway.debug import DebugStreamingGateway
    
    # Create debug gateway with local video files
    gateway = DebugStreamingGateway(
        video_paths=["video1.mp4", "video2.mp4"],
        fps=10,
        video_codec="h265-frame",
        save_to_files=True,
        output_dir="./debug_output"
    )
    
    # Start streaming
    gateway.start_streaming()
    
    # Check stats
    import time
    time.sleep(30)
    print(gateway.get_statistics())
    
    # Stop
    gateway.stop_streaming()
"""

from .debug_streaming_gateway import DebugStreamingGateway, DebugStreamingAction
from .debug_stream_backend import DebugStreamBackend
from .debug_utils import MockSession, MockRPC, create_debug_input_streams

__all__ = [
    "DebugStreamingGateway",
    "DebugStreamingAction",
    "DebugStreamBackend",
    "MockSession",
    "MockRPC",
    "create_debug_input_streams",
]

