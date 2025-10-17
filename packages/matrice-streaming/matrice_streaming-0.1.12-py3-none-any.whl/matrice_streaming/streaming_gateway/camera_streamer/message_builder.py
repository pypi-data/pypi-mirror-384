"""Message building for stream messages."""
import base64
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Union, Optional, Any


class StreamMessageBuilder:
    """Builds stream messages with proper structure and metadata."""
    
    def __init__(self, service_id: str, strip_input_content: bool = False):
        """Initialize message builder.
        
        Args:
            service_id: Service/deployment identifier
            strip_input_content: Strip content for out-of-band retrieval
        """
        self.service_id = service_id
        self.strip_input_content = strip_input_content
    
    def build_frame_metadata(
        self,
        input_source: Union[str, int],
        video_props: Dict[str, Any],
        fps: int,
        quality: int,
        actual_width: int,
        actual_height: int,
        stream_type: str,
        frame_counter: int,
        is_video_chunk: bool,
        chunk_duration_seconds: Optional[float],
        chunk_frames: Optional[int],
        camera_location: Optional[str]
    ) -> Dict[str, Any]:
        """Build frame metadata dictionary.
        
        Args:
            input_source: Input source identifier
            video_props: Video properties dictionary
            fps: Target FPS
            quality: Quality setting
            actual_width: Frame width
            actual_height: Frame height
            stream_type: Type of stream source
            frame_counter: Current frame number
            is_video_chunk: Whether this is a chunked stream
            chunk_duration_seconds: Chunk duration
            chunk_frames: Number of frames per chunk
            camera_location: Camera location description
            
        Returns:
            Metadata dictionary
        """
        original_fps = video_props.get("original_fps", 0)
        frame_sample_rate = original_fps / fps if (original_fps and fps) else 1.0
        
        video_timestamp = self._calculate_video_timestamp(frame_counter, fps)
        video_format = self._get_video_format(input_source)
        
        return {
            "fps": fps,
            "quality": quality,
            "width": actual_width,
            "height": actual_height,
            "stream_type": stream_type,
            "frame_counter": frame_counter,
            "original_fps": original_fps,
            "frame_sample_rate": frame_sample_rate,
            "video_timestamp": video_timestamp,
            "video_properties": video_props,
            "is_video_chunk": is_video_chunk,
            "chunk_duration_seconds": chunk_duration_seconds,
            "chunk_frames": chunk_frames,
            "video_format": video_format,
            "camera_location": camera_location or "Unknown Location",
        }
    
    def build_message(
        self,
        frame_data: bytes,
        stream_key: str,
        stream_group_key: str,
        codec: str,
        metadata: Dict[str, Any],
        topic: str,
        broker_config: str,
        input_order: int,
        last_read_time: float,
        last_write_time: float,
        last_process_time: float
    ) -> Dict[str, Any]:
        """Build complete stream message.
        
        Args:
            frame_data: Encoded frame bytes
            stream_key: Stream identifier
            stream_group_key: Stream group identifier
            codec: Video codec
            metadata: Frame metadata
            topic: Topic name
            broker_config: Broker configuration string
            input_order: Input order number
            last_read_time: Last read time
            last_write_time: Last write time
            last_process_time: Last process time
            
        Returns:
            Complete message dictionary
        """
        # Encode content
        if frame_data and not self.strip_input_content:
            content_b64 = base64.b64encode(frame_data).decode("utf-8")
        else:
            content_b64 = ""
        
        # Build input stream
        input_stream = {
            "ip_key_name": self.service_id,
            "stream_info": {
                "broker": broker_config,
                "topic": topic,
                "stream_time": self._get_high_precision_timestamp(),
            },
            "feed_type": metadata.get("feed_type", "camera"),
            "original_fps": metadata.get("original_fps", 30.0),
            "stream_fps": metadata.get("fps", 30),
            "stream_unit": metadata.get("stream_unit", "frame"),
            "input_order": input_order,
            "frame_count": metadata.get("frame_count", 1),
            "start_frame": metadata.get("start_frame"),
            "end_frame": metadata.get("end_frame"),
            "video_codec": codec,
            "bw_opt_alg": None,
            "original_resolution": {
                "width": metadata.get("width", 1024),
                "height": metadata.get("height", 1080),
            },
            "stream_resolution": {
                "width": metadata.get("width", 1024),
                "height": metadata.get("height", 1080),
            },
            "camera_info": {
                "camera_name": stream_key,
                "camera_group": stream_group_key,
                "location": metadata.get("camera_location", "Unknown Location")
            },
            "latency_stats": {
                "last_read_time_sec": last_read_time,
                "last_write_time_sec": last_write_time,
                "last_process_time_sec": last_process_time,
            },
            "content": content_b64,
            "input_hash": hashlib.md5(frame_data, usedforsecurity=False).hexdigest() if frame_data else None,
        }
        
        # Add passthrough metadata
        passthrough_keys = {
            "similarity_score", "skip_reason",
            "difference_metadata", "video_timestamp", "video_properties",
            "frame_sample_rate", "is_video_chunk", "chunk_duration_seconds",
            "video_format", "stream_type", "reference_input_hash",
            "encoding_type", "compression_format", "chunk_frames"
        }
        for k, v in metadata.items():
            if k in passthrough_keys and v is not None:
                input_stream[k] = v
        
        return {
            "frame_id": uuid.uuid4().hex,
            "input_name": f"{input_stream['stream_unit']}_{input_stream['input_order']}",
            "input_unit": input_stream["stream_unit"],
            "input_stream": input_stream,
        }
    
    @staticmethod
    def _calculate_video_timestamp(frame_number: int, fps: float) -> str:
        """Calculate video timestamp from frame number.
        
        Args:
            frame_number: Current frame number
            fps: Frames per second
            
        Returns:
            Timestamp string in format HH:MM:SS:mmm
        """
        total_seconds = frame_number / fps if fps else 0.0
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int(round((total_seconds - int(total_seconds)) * 1000))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{milliseconds:03d}"
    
    @staticmethod
    def _get_video_format(input_source: Union[str, int]) -> str:
        """Get video format extension from input.
        
        Args:
            input_source: Input source
            
        Returns:
            File extension
        """
        if isinstance(input_source, str) and "." in input_source:
            return "." + input_source.split("?")[0].split(".")[-1].lower()
        return ".mp4"
    
    @staticmethod
    def _get_high_precision_timestamp() -> str:
        """Get high precision timestamp with microsecond granularity.
        
        Returns:
            Timestamp string
        """
        return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H:%M:%S.%f UTC")

