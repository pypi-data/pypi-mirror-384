"""Simplified CameraStreamer using modular components."""
import logging
import cv2
import threading
import time
from typing import Dict, Optional, Union, Any
from matrice_common.stream.matrice_stream import MatriceStream, StreamType

# Import our modular components
from .video_capture_manager import VideoCaptureManager
from .encoder_manager import EncoderManager
from .stream_statistics import StreamStatistics
from .message_builder import StreamMessageBuilder
from .retry_manager import RetryManager
from .frame_processor import FrameProcessor
from ..streaming_gateway_utils import StreamingGatewayUtil


class CameraStreamer:
    """Simplified camera streamer using modular components.
    
    This class orchestrates video streaming with:
    - Robust retry logic (never gives up)
    - Multiple video codecs (H.264, H.265 frame/stream)
    - Automatic reconnection on failures
    - Statistics tracking
    - Support for cameras, video files, RTSP, HTTP streams
    """
    
    def __init__(
        self,
        session,
        service_id: str,
        server_type: str,
        strip_input_content: bool = False,
        video_codec: Optional[str] = None,
        h265_quality: int = 23,
        use_hardware: bool = False,
        h265_mode: str = "frame",
        gateway_util: StreamingGatewayUtil = None,
        connection_refresh_threshold: int = 10,
        connection_refresh_interval: float = 60.0,
    ):
        """Initialize CameraStreamer.
        
        Args:
            session: Session object for making RPC calls
            service_id: ID of the deployment
            server_type: Type of server (kafka or redis)
            strip_input_content: Strip content for out-of-band retrieval
            video_codec: Video codec to use
            h265_quality: H.265 quality (CRF value 0-51, lower=better)
            use_hardware: Use hardware encoding if available
            h265_mode: H.265 mode - "frame" or "stream"
            gateway_util: StreamingGatewayUtil instance for fetching connection info
            connection_refresh_threshold: Number of consecutive failures before refreshing connection
            connection_refresh_interval: Minimum seconds between connection refresh attempts
        """
        self.session = session
        self.service_id = service_id
        self.server_type = server_type.lower()
        self.gateway_util = gateway_util
        
        # Initialize modular components
        self.capture_manager = VideoCaptureManager()
        self.encoder_manager = EncoderManager(h265_mode, h265_quality, use_hardware)
        self.statistics = StreamStatistics()
        self.message_builder = StreamMessageBuilder(service_id, strip_input_content)
        
        # Video codec configuration
        self.video_codec = self._normalize_video_codec(video_codec, h265_mode)
        self.h265_mode = h265_mode
        
        # Streaming state
        self.streaming_threads = []
        self._stop_streaming = False
        self.stream_topics: Dict[str, str] = {}
        self.setup_topics = set()
        
        # Connection refresh state
        self.connection_refresh_threshold = connection_refresh_threshold
        self.connection_refresh_interval = connection_refresh_interval
        self._send_failure_count = 0
        self._last_connection_refresh_time = 0.0
        self._connection_lock = threading.RLock()
        
        # Initialize MatriceStream
        if self.gateway_util:
            self.stream_config = self.gateway_util.get_and_wait_for_connection_info(
                server_type=self.server_type
            )
        else:
            self.logger = logging.getLogger(__name__)
            self.logger.error("No gateway_util provided, connection refresh will be disabled")
            self.stream_config = {}
        
        self.matrice_stream = MatriceStream(
            StreamType.REDIS if self.server_type == "redis" else StreamType.KAFKA,
            **self.stream_config
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"CameraStreamer initialized with codec: {self.video_codec}")
    
    # ========================================================================
    # Public API - Topic Management
    # ========================================================================
    
    def register_stream_topic(self, stream_key: str, topic: str):
        """Register a topic for a specific stream key."""
        self.stream_topics[stream_key] = topic
        self.logger.info(f"Registered topic '{topic}' for stream '{stream_key}'")
    
    def get_topic_for_stream(self, stream_key: str) -> Optional[str]:
        """Get the topic for a specific stream key."""
        return self.stream_topics.get(stream_key)
    
    def setup_stream_for_topic(self, topic: str) -> bool:
        """Setup MatriceStream for a topic."""
        try:
            if topic not in self.setup_topics:
                self.matrice_stream.setup(topic)
                self.setup_topics.add(topic)
                self.logger.info(f"MatriceStream setup complete for topic: {topic}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to setup MatriceStream for topic {topic}: {e}")
            return False
    
    # ========================================================================
    # Public API - Streaming Control
    # ========================================================================
    
    def start_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        simulate_video_file_stream: bool = False,
        is_video_chunk: bool = False,
        chunk_duration_seconds: Optional[float] = None,
        chunk_frames: Optional[int] = None,
        camera_location: Optional[str] = None,
    ) -> bool:
        """Start streaming in current thread (blocking).
        
        Args:
            input: Video source (camera index, file path, or URL)
            fps: Target frames per second
            stream_key: Unique identifier for this stream
            stream_group_key: Group identifier for related streams
            quality: Video quality
            width: Target width (None to keep original)
            height: Target height (None to keep original)
            simulate_video_file_stream: Loop video file continuously
            is_video_chunk: Whether this is a chunked video stream
            chunk_duration_seconds: Duration of each chunk
            chunk_frames: Number of frames per chunk
            camera_location: Physical location description
            
        Returns:
            True if stream started successfully, False otherwise
        """
        try:
            topic = self.get_topic_for_stream(stream_key)
            if not topic:
                self.logger.error(f"No topic registered for stream {stream_key}")
                return False
            
            self._stream_loop(
                input, stream_key or "default", stream_group_key or "default",
                topic, fps, quality, width, height, simulate_video_file_stream,
                is_video_chunk, chunk_duration_seconds, chunk_frames,
                camera_location or "Unknown"
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to start stream: {e}", exc_info=True)
            return False
    
    def start_background_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        simulate_video_file_stream: bool = False,
        is_video_chunk: bool = False,
        chunk_duration_seconds: Optional[float] = None,
        chunk_frames: Optional[int] = None,
        camera_location: Optional[str] = None,
    ) -> bool:
        """Start streaming in background thread (non-blocking)."""
        try:
            topic = self.get_topic_for_stream(stream_key)
            if not topic:
                self.logger.error(f"No topic registered for stream {stream_key}")
                return False
            
            thread = threading.Thread(
                target=self._stream_loop,
                args=(
                    input, stream_key or "default", stream_group_key or "default",
                    topic, fps, quality, width, height, simulate_video_file_stream,
                    is_video_chunk, chunk_duration_seconds, chunk_frames,
                    camera_location or "Unknown"
                ),
                daemon=True
            )
            
            self.streaming_threads.append(thread)
            thread.start()
            self.logger.info(f"Started background stream for {stream_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start background stream: {e}")
            return False
    
    def stop_streaming(self):
        """Stop all streaming threads."""
        self._stop_streaming = True
        for thread in self.streaming_threads:
            if thread.is_alive():
                thread.join(timeout=5.0)
        self.streaming_threads.clear()
        self._stop_streaming = False
        self.logger.info("All streams stopped")
    
    # ========================================================================
    # Public API - Direct Message Production
    # ========================================================================
    
    def produce_request(
        self,
        input_data: bytes,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        metadata: Optional[Dict] = None,
        topic: Optional[str] = None,
        timeout: float = 60.0,
    ) -> bool:
        """Produce a stream request to MatriceStream (synchronous)."""
        try:
            actual_topic = topic or self.get_topic_for_stream(stream_key) or "default_topic"
            metadata = metadata or {}
            
            last_read, last_write, last_process = self.statistics.get_timing(stream_key or "default")
            input_order = self.statistics.get_next_input_order(stream_key or "default")
            
            message = self.message_builder.build_message(
                input_data, stream_key or "default", stream_group_key or "default",
                metadata.get("video_codec", "h264"), metadata, actual_topic,
                self.matrice_stream.config.get('bootstrap_servers', 'localhost:9092'),
                input_order, last_read, last_write, last_process
            )
            
            self.matrice_stream.add_message(
                topic_or_channel=actual_topic,
                message=message,
                key=str(stream_key)
            )
            
            # Record success
            self._record_send_success()
            return True
        except Exception as e:
            self.logger.error(f"Failed to produce request: {e}")
            
            # Record failure
            self._record_send_failure()
            return False
    
    async def async_produce_request(
        self,
        input_data: bytes,
        stream_key: Optional[str] = None,
        stream_group_key: Optional[str] = None,
        metadata: Optional[Dict] = None,
        topic: Optional[str] = None,
        timeout: float = 60.0,
    ) -> bool:
        """Produce a stream request to MatriceStream (asynchronous)."""
        try:
            actual_topic = topic or self.get_topic_for_stream(stream_key) or "default_topic"
            metadata = metadata or {}
            
            last_read, last_write, last_process = self.statistics.get_timing(stream_key or "default")
            input_order = self.statistics.get_next_input_order(stream_key or "default")
            
            message = self.message_builder.build_message(
                input_data, stream_key or "default", stream_group_key or "default",
                metadata.get("video_codec", "h264"), metadata, actual_topic,
                self.matrice_stream.config.get('bootstrap_servers', 'localhost:9092'),
                input_order, last_read, last_write, last_process
            )
            
            if not self.matrice_stream.is_async_setup():
                await self.matrice_stream.async_setup(actual_topic)
            
            await self.matrice_stream.async_add_message(
                topic_or_channel=actual_topic,
                message=message,
                key=str(stream_key)
            )
            
            # Record success
            self._record_send_success()
            return True
        except Exception as e:
            self.logger.error(f"Failed to async produce request: {e}")
            
            # Record failure
            self._record_send_failure()
            return False
    
    # ========================================================================
    # Public API - Statistics
    # ========================================================================
    
    def get_transmission_stats(self) -> Dict[str, Any]:
        """Get transmission statistics."""
        return self.statistics.get_transmission_stats(
            self.video_codec,
            len(self.streaming_threads)
        )
    
    def reset_transmission_stats(self):
        """Reset transmission statistics."""
        self.statistics.reset()
    
    def get_stream_timing_stats(self, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Get timing statistics for a stream."""
        return self.statistics.get_timing_stats(stream_key)
    
    # ========================================================================
    # Public API - Connection Management
    # ========================================================================
    
    def refresh_connection_info(self) -> bool:
        """Refresh connection info from API and reinitialize MatriceStream.
        
        This method checks the server connection info from the API and if it has changed,
        it reinitializes the MatriceStream with the new connection details.
        
        Returns:
            bool: True if connection was refreshed successfully
        """
        if not self.gateway_util:
            self.logger.warning("Cannot refresh connection: no gateway_util provided")
            return False
        
        with self._connection_lock:
            current_time = time.time()
            
            # Check if enough time has passed since last refresh
            if current_time - self._last_connection_refresh_time < self.connection_refresh_interval:
                self.logger.debug(
                    f"Skipping connection refresh, last refresh was {current_time - self._last_connection_refresh_time:.1f}s ago"
                )
                return False
            
            try:
                self.logger.info("Attempting to refresh connection info from API...")
                
                # Fetch new connection info with a short timeout (don't wait too long)
                new_connection_info = self.gateway_util.get_and_wait_for_connection_info(
                    server_type=self.server_type,
                    connection_timeout=300  # Short timeout for refresh
                )
                
                if not new_connection_info:
                    self.logger.error("Failed to fetch new connection info")
                    return False
                
                # Check if connection info has changed
                if new_connection_info == self.stream_config:
                    self.logger.info("Connection info unchanged, no refresh needed")
                    self._last_connection_refresh_time = current_time
                    return True
                
                self.logger.warning("Connection info has changed! Reinitializing MatriceStream...")
                self.logger.info(f"Old config: {self._mask_sensitive_config(self.stream_config)}")
                self.logger.info(f"New config: {self._mask_sensitive_config(new_connection_info)}")
                
                # Close existing stream
                try:
                    self.matrice_stream.close()
                    self.logger.debug("Closed old MatriceStream connection")
                except Exception as e:
                    self.logger.warning(f"Error closing old stream: {e}")
                
                # Update config and reinitialize
                self.stream_config = new_connection_info
                self.matrice_stream = MatriceStream(
                    StreamType.REDIS if self.server_type == "redis" else StreamType.KAFKA,
                    **self.stream_config
                )
                self.logger.info("MatriceStream reinitialized with new connection config")
                
                # Re-setup all topics
                topics_to_setup = list(self.setup_topics)
                self.setup_topics.clear()  # Clear and re-add as we setup
                
                for topic in topics_to_setup:
                    try:
                        self.matrice_stream.setup(topic)
                        self.setup_topics.add(topic)
                        self.logger.info(f"Re-setup topic: {topic}")
                    except Exception as e:
                        self.logger.error(f"Failed to re-setup topic {topic}: {e}")
                
                # Reset failure count and update refresh time
                self._send_failure_count = 0
                self._last_connection_refresh_time = current_time
                
                self.logger.info("Connection info refreshed and MatriceStream reinitialized successfully!")
                return True
                
            except Exception as e:
                self.logger.error(f"Error refreshing connection info: {e}", exc_info=True)
                return False
    
    def _record_send_success(self):
        """Record a successful send operation."""
        with self._connection_lock:
            if self._send_failure_count > 0:
                self.logger.debug(f"Send succeeded after {self._send_failure_count} failures, resetting counter")
            self._send_failure_count = 0
    
    def _record_send_failure(self):
        """Record a failed send operation and check if connection refresh is needed."""
        with self._connection_lock:
            self._send_failure_count += 1
            
            self.logger.warning(
                f"Send failure recorded ({self._send_failure_count}/{self.connection_refresh_threshold})"
            )
            
            # Check if we've reached the threshold
            if self._send_failure_count >= self.connection_refresh_threshold:
                self.logger.warning(
                    f"Send failure threshold reached ({self.connection_refresh_threshold}), "
                    f"attempting connection refresh..."
                )
                self.refresh_connection_info()
    
    # ========================================================================
    # Public API - Cleanup
    # ========================================================================
    
    async def close(self):
        """Clean up resources."""
        try:
            self.stop_streaming()
            self.encoder_manager.cleanup()
            self.capture_manager.cleanup()
            
            # Close stream
            await self.matrice_stream.async_close()
            self.matrice_stream.close()
            
            self.logger.info("CameraStreamer closed")
        except Exception as e:
            self.logger.error(f"Error closing CameraStreamer: {e}")
    
    # ========================================================================
    # Private Methods - Main Streaming Loop
    # ========================================================================
    
    def _stream_loop(
        self,
        source: Union[str, int],
        stream_key: str,
        stream_group_key: str,
        topic: str,
        fps: int,
        quality: int,
        width: Optional[int],
        height: Optional[int],
        simulate_video_file_stream: bool,
        is_video_chunk: bool,
        chunk_duration_seconds: Optional[float],
        chunk_frames: Optional[int],
        camera_location: str
    ):
        """Main streaming loop with infinite retry logic."""
        cap = None
        retry_mgr = RetryManager(stream_key)
        
        # Prepare source once (download if needed)
        prepared_source = self.capture_manager.prepare_source(source, stream_key)
        
        # Setup topic
        if not self.setup_stream_for_topic(topic):
            self.logger.error(f"Failed to setup topic {topic}")
            return
        
        # OUTER LOOP: Retry forever - NEVER GIVE UP!
        while not self._stop_streaming:
            try:
                # Open capture
                cap, source_type = self.capture_manager.open_capture(prepared_source, width, height)
                video_props = self.capture_manager.get_video_properties(cap)
                
                # Calculate dimensions and frame skip
                actual_width, actual_height = FrameProcessor.calculate_actual_dimensions(
                    video_props["width"], video_props["height"], width, height
                )
                frame_skip = self.capture_manager.calculate_frame_skip(
                    source_type, video_props["original_fps"], fps
                )
                
                # Mark successful connection
                retry_mgr.handle_successful_reconnect()
                
                # INNER LOOP: Process frames
                self._process_frames_loop(
                    cap, source_type, stream_key, stream_group_key, topic,
                    source, video_props, fps, quality, actual_width, actual_height,
                    frame_skip, is_video_chunk, chunk_duration_seconds,
                    chunk_frames, camera_location, retry_mgr
                )
                
                # Check if we should restart video file
                if source_type == "video_file":
                    if simulate_video_file_stream:
                        self.logger.info(f"End of video file, restarting: {prepared_source}")
                        cap.release()
                        cap = None
                        retry_mgr.wait_before_restart()
                        continue
                    else:
                        self.logger.info(f"End of video file (no loop): {stream_key}")
                        break
                        
            except Exception as e:
                retry_mgr.handle_connection_failure(e)
                
                if cap:
                    cap.release()
                    cap = None
                
                # Wait with exponential backoff, then retry forever
                retry_mgr.wait_before_retry()
        
        # Cleanup
        if cap:
            cap.release()
        self.logger.info(f"Stream ended for {stream_key}")
    
    def _process_frames_loop(
        self,
        cap: cv2.VideoCapture,
        source_type: str,
        stream_key: str,
        stream_group_key: str,
        topic: str,
        source: Union[str, int],
        video_props: Dict[str, Any],
        fps: int,
        quality: int,
        actual_width: int,
        actual_height: int,
        frame_skip: int,
        is_video_chunk: bool,
        chunk_duration_seconds: Optional[float],
        chunk_frames: Optional[int],
        camera_location: str,
        retry_mgr: RetryManager
    ):
        """Inner loop that processes and sends frames."""
        frame_counter = 0
        processed_frame_counter = 0
        is_rtsp = source_type == "rtsp"
        
        while not self._stop_streaming:
            loop_start = time.time()
            
            # Read frame
            read_start = time.time()
            ret, frame = cap.read()
            read_time = time.time() - read_start
            
            if not ret:
                retry_mgr.record_read_failure()
                if retry_mgr.should_reconnect():
                    break
                retry_mgr.wait_after_read_failure()
                continue
            
            # Mark success
            retry_mgr.record_success()
            frame_counter += 1
            
            # Handle RTSP frame skipping
            if is_rtsp:
                if FrameProcessor.should_skip_frame(frame_counter, frame_skip):
                    continue
                processed_frame_counter += 1
            else:
                processed_frame_counter = frame_counter
            
            # Resize frame if needed
            frame = FrameProcessor.resize_frame(frame, actual_width, actual_height)
            
            # Process and send frame
            encoding_time, write_time = self._process_and_send_frame(
                frame, stream_key, stream_group_key, topic, source,
                video_props, fps, quality, actual_width, actual_height,
                source_type, processed_frame_counter, is_video_chunk,
                chunk_duration_seconds, chunk_frames, camera_location,
                read_time
            )
            
            # Log statistics periodically
            self.statistics.log_periodic_stats(stream_key, read_time, encoding_time, write_time)
            
            # Maintain FPS for non-RTSP streams
            if not is_rtsp:
                elapsed = time.time() - loop_start
                sleep_time = max(0, (1.0 / fps) - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
    
    def _process_and_send_frame(
        self,
        frame,
        stream_key: str,
        stream_group_key: str,
        topic: str,
        source: Union[str, int],
        video_props: Dict[str, Any],
        fps: int,
        quality: int,
        actual_width: int,
        actual_height: int,
        source_type: str,
        frame_counter: int,
        is_video_chunk: bool,
        chunk_duration_seconds: Optional[float],
        chunk_frames: Optional[int],
        camera_location: str,
        read_time: float
    ) -> tuple:
        """Process frame: encode, build message, and send."""
        # Build metadata
        metadata = self.message_builder.build_frame_metadata(
            source, video_props, fps, quality, actual_width, actual_height,
            source_type, frame_counter, is_video_chunk, chunk_duration_seconds,
            chunk_frames, camera_location
        )
        metadata["feed_type"] = "disk" if source_type == "video_file" else "camera"
        metadata["frame_count"] = 1
        metadata["stream_unit"] = "segment" if is_video_chunk else "frame"
        
        # Encode frame
        encoding_start = time.time()
        if self.video_codec in ["h265-frame", "h265-chunk"]:
            frame_data, metadata, codec = self.encoder_manager.encode_frame(
                frame, stream_key, fps, actual_width, actual_height, metadata
            )
            codec = "h265"
        else:
            frame_data = frame.tobytes()
            codec = "h264"
            metadata["encoding_type"] = "raw"
        encoding_time = time.time() - encoding_start
        
        # Get timing stats
        last_read, last_write, last_process = self.statistics.get_timing(stream_key)
        input_order = self.statistics.get_next_input_order(stream_key)
        
        # Build and send message
        write_start = time.time()
        try:
            message = self.message_builder.build_message(
                frame_data, stream_key, stream_group_key, codec, metadata, topic,
                self.matrice_stream.config.get('bootstrap_servers', 'localhost:9092'),
                input_order, last_read, last_write, last_process
            )
            
            self.matrice_stream.add_message(
                topic_or_channel=topic,
                message=message,
                key=str(stream_key)
            )
            write_time = time.time() - write_start
            
            # Record success
            self._record_send_success()
            
            # Update statistics
            self.statistics.increment_frames_sent()
            process_time = read_time + write_time
            self.statistics.update_timing(stream_key, read_time, write_time, process_time)
            
        except Exception as e:
            write_time = time.time() - write_start
            self.logger.error(f"Failed to send message for {stream_key}: {e}")
            
            # Record failure (will trigger connection refresh if threshold reached)
            self._record_send_failure()
        
        return encoding_time, write_time
    
    # ========================================================================
    # Private Methods - Helpers
    # ========================================================================
    
    def _mask_sensitive_config(self, config: Dict) -> Dict:
        """Mask sensitive information in configuration for logging.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Dict: Configuration with sensitive fields masked
        """
        if not config:
            return config
        
        masked = config.copy()
        sensitive_keys = ['password', 'sasl_password', 'sasl_username', 'username']
        
        for key in sensitive_keys:
            if key in masked and masked[key]:
                masked[key] = '***MASKED***'
        
        return masked
    
    @staticmethod
    def _normalize_video_codec(video_codec: Optional[str], h265_mode: str) -> str:
        """Normalize codec selection."""
        if not video_codec or str(video_codec).strip() == "":
            return "h264"
        
        vc = str(video_codec).lower().strip()
        if vc in {"h264", "h265-frame", "h265-chunk"}:
            return vc
        if vc in {"h265", "hevc", "frame"}:
            return "h265-frame"
        if vc in {"h265-stream", "stream", "chunk"}:
            return "h265-chunk"
        return "h264"
