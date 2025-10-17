"""Debug streaming gateway for testing without Redis/Kafka/API."""
import logging
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from .debug_stream_backend import DebugStreamBackend
from .debug_utils import MockSession, create_debug_input_streams
from ..camera_streamer.camera_streamer import CameraStreamer

class DebugStreamingGateway:
    """Debug version of StreamingGateway that works without external dependencies.
    
    This class allows you to test the complete streaming pipeline using local video files
    without requiring:
    - Kafka or Redis servers
    - API authentication
    - Network connectivity
    - Real streaming gateway configuration
    
    Perfect for:
    - Local development and testing
    - CI/CD pipelines
    - Debugging encoding/processing issues
    - Performance testing
    
    Example usage:
        # Simple usage with video files
        gateway = DebugStreamingGateway(
            video_paths=["video1.mp4", "video2.mp4"],
            fps=10,
            loop_videos=True
        )
        gateway.start_streaming()
        
        # Wait and check stats
        time.sleep(30)
        print(gateway.get_statistics())
        
        # Stop
        gateway.stop_streaming()
    """
    
    def __init__(
        self,
        video_paths: List[str],
        fps: int = 10,
        video_codec: str = "h264",
        h265_quality: int = 23,
        use_hardware: bool = False,
        loop_videos: bool = True,
        output_dir: Optional[str] = None,
        save_to_files: bool = False,
        log_messages: bool = True,
        save_frame_data: bool = False,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        """Initialize debug streaming gateway.
        
        Args:
            video_paths: List of video file paths to stream
            fps: Frames per second to stream
            video_codec: Video codec (h264, h265-frame, h265-chunk)
            h265_quality: H.265 quality (0-51, lower=better)
            use_hardware: Use hardware encoding
            loop_videos: Loop videos continuously
            output_dir: Directory to save debug output
            save_to_files: Save streamed messages to files
            log_messages: Log message metadata
            save_frame_data: Include frame data in saved files
            width: Override video width
            height: Override video height
        """
        # Validate video paths
        for video_path in video_paths:
            if not Path(video_path).exists():
                raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.video_paths = video_paths
        self.fps = fps
        self.video_codec = video_codec
        self.loop_videos = loop_videos
        
        # Create mock session
        self.session = MockSession()
        
        # Create debug stream backend (replaces Kafka/Redis)
        self.stream_backend = DebugStreamBackend(
            output_dir=output_dir,
            save_to_files=save_to_files,
            log_messages=log_messages,
            save_frame_data=save_frame_data
        )
        
        # Create input streams from video paths
        self.input_streams = create_debug_input_streams(
            video_paths=video_paths,
            fps=fps,
            loop=loop_videos
        )
        
        # Override dimensions if provided
        if width or height:
            for stream in self.input_streams:
                if width:
                    stream.width = width
                if height:
                    stream.height = height
        
        # Create camera streamer with debug backend
        self.camera_streamer = CameraStreamer(
            session=self.session,
            service_id="debug_streaming_gateway",
            server_type="debug",
            stream_config={},
            video_codec=video_codec,
            h265_quality=h265_quality,
            use_hardware=use_hardware,
        )
        
        # Replace MatriceStream with debug backend
        self.camera_streamer.matrice_stream = self.stream_backend
        
        # State
        self.is_streaming = False
        self.start_time = None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"DebugStreamingGateway initialized: "
            f"{len(video_paths)} videos, "
            f"{fps} fps, "
            f"codec={video_codec}"
        )
    
    def start_streaming(self, block: bool = False) -> bool:
        """Start streaming all video files.
        
        Args:
            block: If True, block until manually stopped
            
        Returns:
            True if started successfully
        """
        if self.is_streaming:
            self.logger.warning("Already streaming")
            return False
        
        self.logger.info(f"Starting debug streaming with {len(self.input_streams)} videos")
        
        try:
            # Register topics and start streams
            for i, input_stream in enumerate(self.input_streams):
                stream_key = input_stream.camera_key
                topic = input_stream.camera_input_topic
                
                # Register topic
                self.camera_streamer.register_stream_topic(stream_key, topic)
                self.stream_backend.setup(topic)
                
                # Start streaming
                success = self.camera_streamer.start_background_stream(
                    input=input_stream.source,
                    fps=input_stream.fps,
                    stream_key=stream_key,
                    stream_group_key=input_stream.camera_group_key,
                    quality=input_stream.quality,
                    width=input_stream.width,
                    height=input_stream.height,
                    simulate_video_file_stream=input_stream.simulate_video_file_stream,
                    camera_location=input_stream.camera_location,
                )
                
                if not success:
                    self.logger.error(f"Failed to start stream {i}: {input_stream.source}")
                    self.stop_streaming()
                    return False
                
                self.logger.info(f"Started stream {i}: {input_stream.source}")
            
            self.is_streaming = True
            self.start_time = time.time()
            self.logger.info("Debug streaming started successfully")
            
            if block:
                self.logger.info("Blocking mode - press Ctrl+C to stop")
                try:
                    while self.is_streaming:
                        time.sleep(1)
                except KeyboardInterrupt:
                    self.logger.info("Interrupted by user")
                    self.stop_streaming()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start debug streaming: {e}", exc_info=True)
            self.stop_streaming()
            return False
    
    def stop_streaming(self):
        """Stop all streaming."""
        if not self.is_streaming:
            self.logger.warning("Not streaming")
            return
        
        self.logger.info("Stopping debug streaming")
        
        try:
            self.camera_streamer.stop_streaming()
            self.stream_backend.close()
            self.is_streaming = False
            
            runtime = time.time() - self.start_time if self.start_time else 0
            self.logger.info(f"Debug streaming stopped (runtime: {runtime:.1f}s)")
            
        except Exception as e:
            self.logger.error(f"Error stopping debug streaming: {e}", exc_info=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics.
        
        Returns:
            Dictionary with streaming statistics
        """
        stats = {
            "is_streaming": self.is_streaming,
            "video_count": len(self.video_paths),
            "fps": self.fps,
            "video_codec": self.video_codec,
        }
        
        if self.start_time:
            stats["runtime_seconds"] = time.time() - self.start_time
        
        # Get camera streamer stats
        try:
            stats["transmission_stats"] = self.camera_streamer.get_transmission_stats()
        except Exception as e:
            self.logger.warning(f"Failed to get transmission stats: {e}")
        
        # Get backend stats
        try:
            stats["backend_stats"] = self.stream_backend.get_statistics()
        except Exception as e:
            self.logger.warning(f"Failed to get backend stats: {e}")
        
        return stats
    
    def get_timing_stats(self, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Get timing statistics.
        
        Args:
            stream_key: Specific stream or None for all
            
        Returns:
            Timing statistics
        """
        return self.camera_streamer.get_stream_timing_stats(stream_key)
    
    def reset_stats(self):
        """Reset all statistics."""
        self.camera_streamer.reset_transmission_stats()
        self.logger.info("Statistics reset")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.logger.error(f"Exception in context: {exc_val}", exc_info=True)
        self.stop_streaming()
    
    def __repr__(self):
        """String representation."""
        return (
            f"DebugStreamingGateway("
            f"videos={len(self.video_paths)}, "
            f"fps={self.fps}, "
            f"streaming={self.is_streaming})"
        )


class DebugStreamingAction:
    """Debug version of StreamingAction for testing without API.
    
    This is a simplified version that doesn't require action IDs, API calls,
    or health monitoring. Perfect for local testing.
    
    Example usage:
        action = DebugStreamingAction(
            video_paths=["video1.mp4", "video2.mp4"],
            fps=10
        )
        action.start()
        time.sleep(30)
        action.stop()
    """
    
    def __init__(
        self,
        video_paths: List[str],
        fps: int = 10,
        video_codec: str = "h265-frame",
        output_dir: Optional[str] = None,
        save_to_files: bool = False,
        **kwargs
    ):
        """Initialize debug streaming action.
        
        Args:
            video_paths: List of video file paths
            fps: Frames per second
            video_codec: Video codec
            output_dir: Output directory for debug files
            save_to_files: Save messages to files
            **kwargs: Additional arguments for DebugStreamingGateway
        """
        self.gateway = DebugStreamingGateway(
            video_paths=video_paths,
            fps=fps,
            video_codec=video_codec,
            output_dir=output_dir,
            save_to_files=save_to_files,
            **kwargs
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DebugStreamingAction initialized with {len(video_paths)} videos")
    
    def start(self, block: bool = False) -> bool:
        """Start streaming action.
        
        Args:
            block: Block until manually stopped
            
        Returns:
            True if started successfully
        """
        self.logger.info("Starting debug streaming action")
        return self.gateway.start_streaming(block=block)
    
    def stop(self):
        """Stop streaming action."""
        self.logger.info("Stopping debug streaming action")
        self.gateway.stop_streaming()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status.
        
        Returns:
            Status dictionary
        """
        return self.gateway.get_statistics()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.logger.error(f"Exception in context: {exc_val}", exc_info=True)
        self.stop()

