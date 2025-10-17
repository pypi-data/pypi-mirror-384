"""Simple Kafka event listener for camera events."""
import logging
import threading
import time
import base64
from typing import Optional, Any, Dict
from kafka import KafkaConsumer
from kafka.errors import KafkaError
from matrice_common.session import Session
from .dynamic_camera_manager import DynamicCameraManager

class EventListener:
    """Simple listener for camera add/update/delete events from Kafka."""
    
    def __init__(
        self,
        session: Session,
        streaming_gateway_id: str,
        camera_manager: DynamicCameraManager,
    ) -> None:
        """Initialize event listener.
        
        Args:
            session: Session object for authentication
            streaming_gateway_id: ID of streaming gateway to filter events
            camera_manager: Camera manager instance
        """
        self.streaming_gateway_id = streaming_gateway_id
        self.camera_manager = camera_manager
        self.session = session        
        # State
        self.consumer: Optional[KafkaConsumer] = None
        self.is_listening = False
        self._stop_event = threading.Event()
        self._listener_thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            'events_received': 0,
            'events_processed': 0,
            'events_failed': 0,
        }
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"EventListener initialized for gateway {streaming_gateway_id}")
    
    def _get_kafka_config(self):
        """Get Kafka configuration from API."""
        # Get Kafka info from API
        response = self.session.rpc.get("/v1/actions/get_kafka_info")
        
        if not response or not response.get("success"):
            logging.warning(f"Failed to fetch Kafka event config: {response.get('message', 'No response')}")
            return None
        
        # Decode base64 encoded values
        data = response.get("data", {})
        encoded_ip = data.get("ip")
        encoded_port = data.get("port")
        
        if not encoded_ip or not encoded_port:
            logging.warning("Missing IP or port in Kafka config response")
            return None
        
        ip = base64.b64decode(encoded_ip).decode("utf-8")
        port = base64.b64decode(encoded_port).decode("utf-8")
        bootstrap_servers = f"{ip}:{port}"
        
        # Build Kafka config with consumer settings
        config = {
            'bootstrap_servers': bootstrap_servers,
            'group_id': f"stg_events_{self.streaming_gateway_id}",
            'auto_offset_reset': 'latest',
            'enable_auto_commit': True,
            'value_deserializer': lambda m: self._deserialize_json(m),
            'key_deserializer': lambda m: m.decode('utf-8') if m else None,
        }
        
        # Add authentication if credentials are available
        # Using standard matrice-sdk credentials
        # config.update({
        #     'security_protocol': 'SASL_PLAINTEXT',
        #     'sasl_mechanism': 'SCRAM-SHA-256',
        #     'sasl_plain_username': 'matrice-sdk-user',
        #     'sasl_plain_password': 'matrice-sdk-password',
        # })
        
        return config
    
    def _deserialize_json(self, message):
        """Deserialize JSON message."""
        import json
        try:
            return json.loads(message.decode('utf-8'))
        except Exception as e:
            self.logger.error(f"Failed to deserialize message: {e}")
            return {}
    
    def start(self) -> bool:
        """Start listening to camera events.
        
        Returns:
            bool: True if started successfully
        """
        if self.is_listening:
            self.logger.warning("Event listener already running")
            return False
        
        try:
            # Create Kafka consumer
            kafka_config = self._get_kafka_config()
            if kafka_config:
                self.consumer = KafkaConsumer(**kafka_config)
            else:
                self.logger.error("Failed to get Kafka configuration")
                return False
            
            # Subscribe to Camera Events Topic only
            self.consumer.subscribe(['Camera_Events_Topic'])
            
            self.logger.info("Subscribed to Camera_Events_Topic")
            
            # Start listener thread
            self._stop_event.clear()
            self.is_listening = True
            
            self._listener_thread = threading.Thread(
                target=self._listen_loop,
                daemon=True,
                name=f"CameraEvents-{self.streaming_gateway_id}"
            )
            self._listener_thread.start()
            
            self.logger.info("Camera event listener started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start event listener: {e}")
            self.is_listening = False
            return False
    
    def stop(self):
        """Stop listening."""
        if not self.is_listening:
            return
        
        self.logger.info("Stopping camera event listener...")
        self.is_listening = False
        self._stop_event.set()
        
        # Wait for thread to stop
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=3.0)
        
        # Close consumer
        if self.consumer:
            try:
                self.consumer.close()
            except Exception as e:
                self.logger.error(f"Error closing consumer: {e}")
        
        self.logger.info("Camera event listener stopped")
    
    def _listen_loop(self):
        """Listen and process camera events."""
        self.logger.info("Camera event listening started")
        
        while not self._stop_event.is_set():
            try:
                messages = self.consumer.poll(timeout_ms=1000, max_records=10)
                
                for topic_partition, records in messages.items():
                    for record in records:
                        try:
                            self._process_camera_event(record)
                        except Exception as e:
                            self.logger.error(f"Error processing event: {e}")
                            self.stats['events_failed'] += 1
                
            except KafkaError as e:
                self.logger.error(f"Kafka error: {e}")
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in listen loop: {e}")
                time.sleep(1)
        
        self.logger.info("Camera event listening ended")
    
    def _process_camera_event(self, record):
        """Process a camera event.
        
        Args:
            record: Kafka consumer record
        """
        self.stats['events_received'] += 1
        
        event = record.value
        gateway_id = event.get('streamingGatewayId')
        
        # Filter by gateway ID
        if gateway_id != self.streaming_gateway_id:
            return
        
        # Get event details
        event_type = event.get('eventType')
        camera_data = event.get('data', {})
        camera_id = camera_data.get('id')
        
        self.logger.info(
            f"Camera event: {event_type} - "
            f"camera_id={camera_id}, "
            f"name={camera_data.get('cameraName', 'Unknown')}"
        )
        
        # Call handler
        try:
            self.handle_event(event)
            self.stats['events_processed'] += 1
        except Exception as e:
            self.logger.error(f"Error in camera handler: {e}")
            self.stats['events_failed'] += 1
    
    def handle_event(self, event: Dict[str, Any]):
        """Handle camera event.
        
        Args:
            event: Camera event dict
        """
        event_type = event.get('eventType')
        camera_data = event.get('data', {})
        camera_id = camera_data.get('id')
        camera_name = camera_data.get('cameraName', 'Unknown')
        
        self.logger.info(f"Handling {event_type} event for camera: {camera_name}")
        
        try:
            if event_type == 'add':
                self.camera_manager.add_camera(camera_data)
            elif event_type == 'update':
                self.camera_manager.update_camera(camera_data)
            elif event_type == 'delete':
                self.camera_manager.remove_camera(camera_id)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
        
        except Exception as e:
            self.logger.error(f"Error handling {event_type} for {camera_id}: {e}")
            
    def get_statistics(self) -> dict:
        """Get statistics."""
        return {
            **self.stats,
            'is_listening': self.is_listening,
        }
        

