import logging
import base64
import time
import threading
from typing import Dict, List, Optional
from .camera_streamer import CameraStreamer
from .streaming_gateway_utils import StreamingGatewayUtil, InputStream
from .event_listener import EventListener
from .dynamic_camera_manager import DynamicCameraManager


class StreamingGateway:
    """Simplified streaming gateway for managing camera streams."""

    # Class-level tracking of active instances
    _active_instances: Dict[str, "StreamingGateway"] = {}
    _class_lock = threading.RLock()

    def __init__(
        self,
        session,
        streaming_gateway_id: str = None,
        server_id: str = None,
        server_type: str = None,
        inputs_config: List[InputStream] = None,
        video_codec: Optional[str] = None,
        force_restart: bool = False,
        enable_event_listening: bool = True,
    ):
        """Initialize StreamingGateway.

        Args:
            session: Session object for authentication
            streaming_gateway_id: ID of the streaming gateway
            server_id: ID of the server (Kafka/Redis)
            server_type: Type of server (kafka or redis)
            inputs_config: List of InputStream configurations
            video_codec: Video codec (h264 or h265)
            force_restart: Force stop existing streams and restart
            enable_event_listening: Enable dynamic event listening for configuration updates
        """
        if not session:
            raise ValueError("Session is required")
        if not streaming_gateway_id:
            raise ValueError("streaming_gateway_id is required")

        self.session = session
        self.streaming_gateway_id = streaming_gateway_id
        self.force_restart = force_restart
        self.enable_event_listening = enable_event_listening
        self.server_type = server_type

        # Initialize utility for API interactions
        self.gateway_util = StreamingGatewayUtil(session, streaming_gateway_id, server_id)

        # Get input configurations
        if inputs_config is None:
            logging.info("Fetching input configurations from API")
            self.inputs_config = self.gateway_util.get_input_streams()
        else:
            self.inputs_config = inputs_config if isinstance(inputs_config, list) else [inputs_config]

        if not self.inputs_config:
            raise ValueError("No input configurations available")

        # Validate inputs
        for i, config in enumerate(self.inputs_config):
            if not isinstance(config, InputStream):
                raise ValueError(f"Input config {i} must be an InputStream instance")

        # Initialize CameraStreamer
        self.camera_streamer = CameraStreamer(
            session=self.session,
            service_id=streaming_gateway_id,
            server_type=server_type,
            video_codec=video_codec,
            gateway_util=self.gateway_util,
        )

        # Initialize dynamic camera manager
        self.camera_manager = DynamicCameraManager(
            camera_streamer=self.camera_streamer,
            streaming_gateway_id=streaming_gateway_id,
            session=self.session
        )

        # Initialize with current camera configurations
        self.camera_manager.initialize_from_config(self.inputs_config)

        # Initialize event system (if enabled)
        self.event_listener: Optional[EventListener] = None
        
        if self.enable_event_listening:
            try:
                self.event_listener = EventListener(
                    session=self.session,
                    streaming_gateway_id=self.streaming_gateway_id,
                    camera_manager=self.camera_manager
                )
            except Exception as e:
                logging.warning(f"Could not initialize event system: {e}")
                logging.info("Continuing without event listening")

        # State management
        self.is_streaming = False
        self._stop_event = threading.Event()
        self._state_lock = threading.RLock()
        self._my_stream_keys = set()

        # Statistics
        self.stats = {
            "start_time": None,
            "current_status": "initialized",
        }

        logging.info(f"StreamingGateway initialized for {self.streaming_gateway_id}")

    def _register_as_active(self):
        """Register this instance as active."""
        with self.__class__._class_lock:
            self.__class__._active_instances[self.streaming_gateway_id] = self
        logging.info(f"Registered as active: {self.streaming_gateway_id}")

    def _unregister_as_active(self):
        """Unregister this instance from active tracking."""
        with self.__class__._class_lock:
            if self.streaming_gateway_id in self.__class__._active_instances:
                if self.__class__._active_instances[self.streaming_gateway_id] is self:
                    del self.__class__._active_instances[self.streaming_gateway_id]
        logging.info(f"Unregistered: {self.streaming_gateway_id}")

    def _stop_existing_streams(self):
        """Stop existing streams if force_restart is enabled."""
        if not self.force_restart:
            return

        logging.warning(f"Force stopping existing streams for {self.streaming_gateway_id}")

        with self.__class__._class_lock:
            if self.streaming_gateway_id in self.__class__._active_instances:
                existing_instance = self.__class__._active_instances[self.streaming_gateway_id]
                try:
                    existing_instance.stop_streaming()
                    logging.info(f"Force stopped existing streams for {self.streaming_gateway_id}")
                except Exception as e:
                    logging.warning(f"Error during force stop: {e}")
                time.sleep(1.0)

    def start_streaming(self) -> bool:
        """Start streaming.

        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        with self._state_lock:
            if self.is_streaming:
                logging.warning("Streaming is already active")
                return False

        if not self.inputs_config:
            logging.error("No input configurations available")
            return False

        # Force stop existing streams if requested
        self._stop_existing_streams()

        # Register as active
        self._register_as_active()

        # Start streaming for each input
        started_streams = []
        try:
            for i, input_config in enumerate(self.inputs_config):
                stream_key = input_config.camera_key or f"stream_{i}"

                # Register topic - generate default if not provided
                topic = input_config.camera_input_topic
                if not topic:
                    # Generate default topic name
                    camera_id = input_config.camera_id or stream_key
                    topic = f"{camera_id}_input_topic"
                    logging.warning(f"No input topic for camera {input_config.camera_key}, using default: {topic}")
                
                self.camera_streamer.register_stream_topic(stream_key, topic)

                # Start streaming
                success = self.camera_streamer.start_background_stream(
                    input=input_config.source,
                    fps=input_config.fps,
                    stream_key=stream_key,
                    stream_group_key=input_config.camera_group_key,
                    quality=input_config.quality,
                    width=input_config.width,
                    height=input_config.height,
                    simulate_video_file_stream=input_config.simulate_video_file_stream,
                    camera_location=input_config.camera_location,
                )

                if not success:
                    logging.error(f"Failed to start streaming for {input_config.source}")
                    if started_streams:
                        logging.info("Stopping already started streams")
                        self.stop_streaming()
                    return False

                started_streams.append(stream_key)
                self._my_stream_keys.add(stream_key)
                logging.info(f"Started streaming for camera: {input_config.camera_key}")

            with self._state_lock:
                self._stop_event.clear()
                self.is_streaming = True
                self.stats["start_time"] = time.time()
                self.stats["current_status"] = "running"

            # Start event listener if enabled
            if self.event_listener and not self.event_listener.is_listening:
                logging.info("Starting event listener for dynamic updates")
                self.event_listener.start()

            logging.info(f"Started streaming with {len(self.inputs_config)} inputs")
            return True

        except Exception as exc:
            logging.error(f"Error starting streaming: {exc}", exc_info=True)
            try:
                self.stop_streaming()
            except Exception as cleanup_exc:
                logging.error(f"Error during cleanup: {cleanup_exc}")
            return False

    def stop_streaming(self):
        """Stop all streaming operations."""
        with self._state_lock:
            if not self.is_streaming:
                logging.warning("Streaming is not active")
                return

            logging.info("Stopping streaming...")
            self._stop_event.set()
            self.is_streaming = False
            self.stats["current_status"] = "stopped"

        # Stop event listener first
        if self.event_listener and self.event_listener.is_listening:
            logging.info("Stopping event listener")
            try:
                self.event_listener.stop()
            except Exception as exc:
                logging.error(f"Error stopping event listener: {exc}")

        # Stop camera streaming
        if self.camera_streamer:
            try:
                self.camera_streamer.stop_streaming()
            except Exception as exc:
                logging.error(f"Error stopping camera streaming: {exc}")

        # Notify API
        try:
            self.gateway_util.stop_streaming()
        except Exception as exc:
            logging.error(f"Error notifying API: {exc}")

        # Unregister
        self._unregister_as_active()

        # Clear stream keys
        self._my_stream_keys.clear()

        logging.info("Streaming stopped")

    def get_statistics(self) -> Dict:
        """Get streaming statistics."""
        with self._state_lock:
            stats = self.stats.copy()

        if stats["start_time"]:
            stats["runtime_seconds"] = time.time() - stats["start_time"]
        else:
            stats["runtime_seconds"] = 0

        stats["is_streaming"] = self.is_streaming
        stats["my_stream_keys"] = list(self._my_stream_keys)
        stats["event_listening_enabled"] = self.enable_event_listening

        # Add camera streamer statistics
        if self.camera_streamer:
            try:
                stats["transmission_stats"] = self.camera_streamer.get_transmission_stats()
            except Exception as exc:
                logging.warning(f"Failed to get transmission stats: {exc}")

        # Add camera manager statistics
        if self.camera_manager:
            try:
                stats["camera_manager_stats"] = self.camera_manager.get_statistics()
            except Exception as exc:
                logging.warning(f"Failed to get camera manager stats: {exc}")

        # Add event listener statistics
        if self.event_listener:
            try:
                stats["event_listener_stats"] = self.event_listener.get_statistics()
            except Exception as exc:
                logging.warning(f"Failed to get event listener stats: {exc}")

        return stats

    def get_config(self) -> Dict:
        """Get current configuration."""
        inputs_config_dict = []
        for config in self.inputs_config:
            inputs_config_dict.append({
                'source': config.source,
                'fps': config.fps,
                'quality': config.quality,
                'width': config.width,
                'height': config.height,
                'camera_id': config.camera_id,
                'camera_key': config.camera_key,
                'camera_group_key': config.camera_group_key,
                'camera_location': config.camera_location,
                'simulate_video_file_stream': config.simulate_video_file_stream,
            })

        return {
            "streaming_gateway_id": self.streaming_gateway_id,
            "inputs_config": inputs_config_dict,
            "force_restart": self.force_restart,
        }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_streaming()
