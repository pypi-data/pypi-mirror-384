"""Dynamic camera manager for runtime camera add/update/delete operations."""
import logging
import threading
from typing import Dict, Any, Optional
from .streaming_gateway_utils import InputStream, StreamingGatewayUtil


class DynamicCameraManager:
    """Manages dynamic camera operations during runtime.
    
    This class handles:
    - Adding new cameras while streaming
    - Updating existing camera configurations
    - Removing cameras and stopping their streams
    - Managing camera group settings
    - Topic updates
    """
    
    def __init__(
        self,
        camera_streamer,
        streaming_gateway_id: str,
        session=None
    ):
        """Initialize dynamic camera manager.
        
        Args:
            camera_streamer: CameraStreamer instance to control streams
            streaming_gateway_id: ID of the streaming gateway
            session: Session object for API calls (optional)
        """
        self.camera_streamer = camera_streamer
        self.streaming_gateway_id = streaming_gateway_id
        self.session = session
        
        # Initialize gateway util for API calls
        self.gateway_util = None
        if session and streaming_gateway_id:
            try:
                self.gateway_util = StreamingGatewayUtil(session, streaming_gateway_id)
            except Exception as e:
                logging.warning(f"Could not initialize StreamingGatewayUtil: {e}")
        
        # Camera storage
        self.cameras: Dict[str, Dict[str, Any]] = {}  # camera_id -> camera_data
        self.camera_groups: Dict[str, Dict[str, Any]] = {}  # group_id -> group_data
        self.camera_topics: Dict[str, Dict[str, str]] = {}  # camera_id -> {input, output}
        
        # Stream key mapping
        self.camera_stream_keys: Dict[str, str] = {}  # camera_id -> stream_key
        
        # Lock for thread-safe operations
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'cameras_added': 0,
            'cameras_updated': 0,
            'cameras_removed': 0,
            'active_cameras': 0,
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"DynamicCameraManager initialized for gateway {streaming_gateway_id}")
    
    def initialize_from_config(self, input_streams: list):
        """Initialize with existing input stream configurations.
        
        Args:
            input_streams: List of InputStream objects
        """
        with self._lock:
            # Fetch and cache camera groups if we have gateway_util
            if self.gateway_util:
                try:
                    all_groups = self.gateway_util.get_camera_groups()
                    if all_groups:
                        for group in all_groups:
                            self.camera_groups[group['id']] = group
                        self.logger.info(f"Cached {len(all_groups)} camera groups")
                except Exception as e:
                    self.logger.warning(f"Failed to fetch camera groups during init: {e}")
            
            # Initialize cameras from input streams
            for input_stream in input_streams:
                camera_id = input_stream.camera_id
                
                # Store camera data
                self.cameras[camera_id] = {
                    'id': camera_id,
                    'cameraName': input_stream.camera_key,
                    'cameraGroupId': input_stream.camera_group_key,
                    'source': input_stream.source,
                    'fps': input_stream.fps,
                    'quality': input_stream.quality,
                    'width': input_stream.width,
                    'height': input_stream.height,
                    'camera_location': input_stream.camera_location,
                    'simulate_video_file_stream': input_stream.simulate_video_file_stream,
                }
                
                # Store topic mapping
                self.camera_topics[camera_id] = {
                    'input': input_stream.camera_input_topic,
                    'output': None,
                }
                
                # Store stream key mapping
                self.camera_stream_keys[camera_id] = input_stream.camera_key
                
                self.stats['active_cameras'] += 1
            
            self.logger.info(f"Initialized with {len(input_streams)} cameras")
    
    def add_camera(self, camera_data: Dict[str, Any]) -> bool:
        """Add a new camera and start streaming.
        
        Args:
            camera_data: Camera configuration data from event
            
        Returns:
            bool: True if camera was added successfully
        """
        camera_id = camera_data.get('id')
        camera_name = camera_data.get('cameraName', 'Unknown')
        
        with self._lock:
            # Check if camera already exists
            if camera_id in self.cameras:
                self.logger.warning(f"Camera {camera_id} already exists, updating instead")
                return self.update_camera(camera_data)
            
            try:
                # Create InputStream from camera data
                input_stream = self._create_input_stream(camera_data)
                
                if not input_stream:
                    self.logger.error(f"Failed to create input stream for camera {camera_id}")
                    return False
                
                # Register topic - generate default if not provided
                topic = input_stream.camera_input_topic
                if not topic:
                    # Generate default topic name
                    topic = f"{camera_id}_input_topic"
                    self.logger.warning(f"No input topic for camera {camera_name}, using default: {topic}")
                
                self.camera_streamer.register_stream_topic(input_stream.camera_key, topic)
                
                # Start streaming
                success = self.camera_streamer.start_background_stream(
                    input=input_stream.source,
                    fps=input_stream.fps,
                    stream_key=input_stream.camera_key,
                    stream_group_key=input_stream.camera_group_key,
                    quality=input_stream.quality,
                    width=input_stream.width,
                    height=input_stream.height,
                    simulate_video_file_stream=input_stream.simulate_video_file_stream,
                    camera_location=input_stream.camera_location,
                )
                
                if not success:
                    self.logger.error(f"Failed to start streaming for camera {camera_name}")
                    return False
                
                # Store camera data
                self.cameras[camera_id] = camera_data
                self.camera_stream_keys[camera_id] = input_stream.camera_key
                self.camera_topics[camera_id] = {
                    'input': topic,
                    'output': None,
                }
                
                # Update statistics
                self.stats['cameras_added'] += 1
                self.stats['active_cameras'] += 1
                
                self.logger.info(f"Successfully added and started streaming for camera: {camera_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error adding camera {camera_name}: {e}", exc_info=True)
                return False
    
    def update_camera(self, camera_data: Dict[str, Any]) -> bool:
        """Update an existing camera's configuration.
        
        This will restart the stream with new settings.
        
        Args:
            camera_data: Updated camera configuration data
            
        Returns:
            bool: True if camera was updated successfully
        """
        camera_id = camera_data.get('id')
        camera_name = camera_data.get('cameraName', 'Unknown')
        
        with self._lock:
            # Check if camera exists
            if camera_id not in self.cameras:
                self.logger.warning(f"Camera {camera_id} not found, adding instead")
                return self.add_camera(camera_data)
            
            try:
                # Get current stream key
                stream_key = self.camera_stream_keys.get(camera_id)
                
                if not stream_key:
                    self.logger.error(f"No stream key found for camera {camera_id}")
                    return False
                                
                # Create new input stream with updated data
                input_stream = self._create_input_stream(camera_data)
                
                if not input_stream:
                    self.logger.error(f"Failed to create updated input stream for camera {camera_id}")
                    return False
                
                # Register topic (may have changed) - generate default if not provided
                topic = input_stream.camera_input_topic
                if not topic:
                    # Generate default topic name
                    topic = f"{camera_id}_input_topic"
                    self.logger.warning(f"No input topic for camera {camera_name}, using default: {topic}")
                
                self.camera_streamer.register_stream_topic(input_stream.camera_key, topic)
                
                # Restart streaming with new configuration
                success = self.camera_streamer.start_background_stream(
                    input=input_stream.source,
                    fps=input_stream.fps,
                    stream_key=input_stream.camera_key,
                    stream_group_key=input_stream.camera_group_key,
                    quality=input_stream.quality,
                    width=input_stream.width,
                    height=input_stream.height,
                    simulate_video_file_stream=input_stream.simulate_video_file_stream,
                    camera_location=input_stream.camera_location,
                )
                
                if not success:
                    self.logger.error(f"Failed to restart streaming for camera {camera_name}")
                    return False
                
                # Update stored camera data
                self.cameras[camera_id] = camera_data
                self.camera_stream_keys[camera_id] = input_stream.camera_key
                
                # Update statistics
                self.stats['cameras_updated'] += 1
                
                self.logger.info(f"Successfully updated camera: {camera_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error updating camera {camera_name}: {e}", exc_info=True)
                return False
    
    def remove_camera(self, camera_id: str) -> bool:
        """Remove a camera and stop its stream.
        
        Args:
            camera_id: ID of camera to remove
            
        Returns:
            bool: True if camera was removed successfully
        """
        with self._lock:
            camera_data = self.cameras.get(camera_id)
            
            if not camera_data:
                self.logger.warning(f"Camera {camera_id} not found")
                return False
            
            camera_name = camera_data.get('cameraName', 'Unknown')
            
            try:                
                # Remove from storage
                del self.cameras[camera_id]
                if camera_id in self.camera_stream_keys:
                    del self.camera_stream_keys[camera_id]
                if camera_id in self.camera_topics:
                    del self.camera_topics[camera_id]
                
                # Update statistics
                self.stats['cameras_removed'] += 1
                self.stats['active_cameras'] -= 1
                
                self.logger.info(f"Successfully removed camera: {camera_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error removing camera {camera_name}: {e}", exc_info=True)
                return False
    
    def update_camera_group(self, group_data: Dict[str, Any]):
        """Update camera group information.
        
        Args:
            group_data: Camera group data
        """
        group_id = group_data.get('id')
        
        with self._lock:
            self.camera_groups[group_id] = group_data
            self.logger.info(f"Updated camera group: {group_data.get('cameraGroupName')}")
    
    def remove_camera_group(self, group_id: str):
        """Remove camera group information.
        
        Args:
            group_id: ID of camera group to remove
        """
        with self._lock:
            if group_id in self.camera_groups:
                del self.camera_groups[group_id]
                self.logger.info(f"Removed camera group: {group_id}")
    
    def update_cameras_in_group(self, group_id: str, group_data: Dict[str, Any]):
        """Update all cameras in a group with new default settings.
        
        Args:
            group_id: Camera group ID
            group_data: Updated group data with new default settings
        """
        default_settings = group_data.get('defaultStreamSettings', {})
        
        with self._lock:
            # Find all cameras in this group
            cameras_to_update = [
                camera_id for camera_id, camera_data in self.cameras.items()
                if camera_data.get('cameraGroupId') == group_id
            ]
            
            self.logger.info(
                f"Updating {len(cameras_to_update)} cameras in group {group_id} "
                f"with new default settings"
            )
            
            # Update each camera
            for camera_id in cameras_to_update:
                camera_data = self.cameras[camera_id].copy()
                
                # Merge default settings (only if camera doesn't have custom settings)
                custom_settings = camera_data.get('customStreamSettings', {})
                for key, value in default_settings.items():
                    if key not in custom_settings:
                        camera_data[key] = value
                
                # Update camera
                self.update_camera(camera_data)
    
    def update_camera_input_topic(self, camera_id: str, topic_name: Optional[str]):
        """Update input topic for a camera.
        
        Args:
            camera_id: Camera ID
            topic_name: New topic name (None to remove)
        """
        with self._lock:
            if camera_id not in self.camera_topics:
                self.camera_topics[camera_id] = {'input': None, 'output': None}
            
            self.camera_topics[camera_id]['input'] = topic_name
            
            # Update stream topic registration
            stream_key = self.camera_stream_keys.get(camera_id)
            if stream_key and topic_name:
                self.camera_streamer.register_stream_topic(stream_key, topic_name)
            
            self.logger.info(f"Updated input topic for camera {camera_id}: {topic_name}")
    
    def update_camera_output_topic(self, camera_id: str, topic_name: Optional[str]):
        """Update output topic for a camera.
        
        Args:
            camera_id: Camera ID
            topic_name: New topic name (None to remove)
        """
        with self._lock:
            if camera_id not in self.camera_topics:
                self.camera_topics[camera_id] = {'input': None, 'output': None}
            
            self.camera_topics[camera_id]['output'] = topic_name
            
            self.logger.info(f"Updated output topic for camera {camera_id}: {topic_name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get camera manager statistics.
        
        Returns:
            Dict with statistics
        """
        with self._lock:
            return {
                **self.stats,
                'camera_ids': list(self.cameras.keys()),
                'camera_groups': len(self.camera_groups),
            }
    
    def _fetch_camera_group(self, camera_group_id: str) -> Optional[Dict[str, Any]]:
        """Fetch camera group from API if not in cache.
        
        Args:
            camera_group_id: Camera group ID
            
        Returns:
            Camera group data or None
        """
        # Check cache first
        if camera_group_id in self.camera_groups:
            return self.camera_groups[camera_group_id]
        
        # Fetch from API if we have gateway_util
        if self.gateway_util:
            try:
                all_groups = self.gateway_util.get_camera_groups()
                if all_groups:
                    # Cache all groups
                    for group in all_groups:
                        self.camera_groups[group['id']] = group
                    
                    # Return requested group
                    return self.camera_groups.get(camera_group_id)
            except Exception as e:
                self.logger.warning(f"Failed to fetch camera groups: {e}")
        
        return None
    
    def _fetch_input_topic(self, camera_id: str) -> Optional[str]:
        """Fetch input topic for camera from API if not in cache.
        
        Args:
            camera_id: Camera ID
            
        Returns:
            Input topic name or None
        """
        # Check cache first
        if camera_id in self.camera_topics:
            return self.camera_topics[camera_id].get('input')
        
        # Fetch from API if we have gateway_util
        if self.gateway_util:
            try:
                all_topics = self.gateway_util.get_streaming_input_topics()
                if all_topics:
                    # Cache all topics
                    for topic in all_topics:
                        topic_camera_id = topic.get('cameraId')
                        if topic_camera_id:
                            if topic_camera_id not in self.camera_topics:
                                self.camera_topics[topic_camera_id] = {'input': None, 'output': None}
                            self.camera_topics[topic_camera_id]['input'] = topic.get('topicName')
                    
                    # Return requested topic
                    return self.camera_topics.get(camera_id, {}).get('input')
            except Exception as e:
                self.logger.warning(f"Failed to fetch input topics: {e}")
        
        return None
    
    def _create_input_stream(self, camera_data: Dict[str, Any]) -> Optional[InputStream]:
        """Create InputStream object from camera data.
        
        Args:
            camera_data: Camera configuration data
            
        Returns:
            InputStream object or None if failed
        """
        try:
            camera_id = camera_data.get('id')
            camera_group_id = camera_data.get('cameraGroupId')
            
            # Get camera group for default settings (fetch if needed)
            camera_group = self._fetch_camera_group(camera_group_id) or {}
            default_settings = camera_group.get('defaultStreamSettings', {})
            custom_settings = camera_data.get('customStreamSettings', {})
            
            # Merge settings (custom overrides default)
            settings = {**default_settings, **custom_settings}
            
            # Determine source
            source = camera_data.get('cameraFeedPath', '')
            simulate_video = False
            
            if camera_data.get('protocolType') == 'FILE':
                # Use simulation video path for file type
                source = camera_data.get('simulationVideoPath', '')
                simulate_video = True
                
                # Try to get signed URL if we have gateway_util
                if self.gateway_util and source:
                    try:
                        stream_url_data = self.gateway_util.get_simulated_stream_url(camera_id)
                        if stream_url_data and stream_url_data.get('url'):
                            source = stream_url_data['url']
                    except Exception as e:
                        self.logger.warning(f"Failed to get signed URL for camera {camera_id}: {e}")
            
            # Get input topic (fetch if needed)
            input_topic = self._fetch_input_topic(camera_id)
            
            if not input_topic:
                self.logger.warning(f"No input topic found for camera {camera_id}")
            
            # Create InputStream
            input_stream = InputStream(
                source=source,
                fps=settings.get('streamingFPS', 10),
                quality=settings.get('videoQuality', 100),
                width=settings.get('width', 640),
                height=settings.get('height', 480),
                camera_id=camera_id,
                camera_key=camera_data.get('cameraName', f'Camera_{camera_id}'),
                camera_group_key=camera_group.get('cameraGroupName', 'Unknown Group'),
                camera_location=camera_group.get('locationId', 'Unknown Location'),
                camera_input_topic=input_topic,
                camera_connection_info=camera_data,
                simulate_video_file_stream=simulate_video
            )
            
            return input_stream
            
        except Exception as e:
            self.logger.error(f"Error creating input stream: {e}", exc_info=True)
            return None

