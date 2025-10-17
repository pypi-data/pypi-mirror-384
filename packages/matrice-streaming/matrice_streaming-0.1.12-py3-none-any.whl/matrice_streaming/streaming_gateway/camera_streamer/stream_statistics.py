"""Statistics tracking for streaming."""
import logging
from typing import Dict, Optional, Tuple, Any


class StreamStatistics:
    """Manages streaming statistics and timing data."""
    
    STATS_LOG_INTERVAL = 50
    
    def __init__(self):
        """Initialize statistics tracker."""
        self.frames_sent = 0
        self.frames_skipped = 0
        self.frames_diff_sent = 0
        self.bytes_saved = 0
        
        # Per-stream timing data
        self.last_read_times: Dict[str, float] = {}
        self.last_write_times: Dict[str, float] = {}
        self.last_process_times: Dict[str, float] = {}
        
        # Per-stream input order tracking
        self.input_order: Dict[str, int] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def increment_frames_sent(self):
        """Increment sent frames counter."""
        self.frames_sent += 1
    
    def increment_frames_skipped(self):
        """Increment skipped frames counter."""
        self.frames_skipped += 1
    
    def increment_frames_diff_sent(self):
        """Increment diff frames counter."""
        self.frames_diff_sent += 1
    
    def add_bytes_saved(self, bytes_count: int):
        """Add to bytes saved counter."""
        self.bytes_saved += bytes_count
    
    def update_timing(
        self,
        stream_key: str,
        read_time: float,
        write_time: float,
        process_time: float
    ):
        """Update timing statistics for a stream.
        
        Args:
            stream_key: Stream identifier
            read_time: Time spent reading frame
            write_time: Time spent writing/sending frame
            process_time: Total processing time
        """
        key = self._normalize_key(stream_key)
        self.last_read_times[key] = read_time
        self.last_write_times[key] = write_time
        self.last_process_times[key] = process_time
    
    def get_timing(self, stream_key: str) -> Tuple[float, float, float]:
        """Get timing data for a stream.
        
        Args:
            stream_key: Stream identifier
            
        Returns:
            Tuple of (read_time, write_time, process_time)
        """
        key = self._normalize_key(stream_key)
        return (
            self.last_read_times.get(key, 0.0),
            self.last_write_times.get(key, 0.0),
            self.last_process_times.get(key, 0.0)
        )
    
    def get_next_input_order(self, stream_key: str) -> int:
        """Get next input order number for a stream.
        
        Args:
            stream_key: Stream identifier
            
        Returns:
            Next input order number
        """
        key = self._normalize_key(stream_key)
        if key not in self.input_order:
            self.input_order[key] = 0
        self.input_order[key] += 1
        return self.input_order[key]
    
    def should_log_stats(self) -> bool:
        """Check if it's time to log statistics.
        
        Returns:
            True if should log stats based on interval
        """
        return self.frames_sent % self.STATS_LOG_INTERVAL == 0
    
    def log_periodic_stats(
        self,
        stream_key: str,
        read_time: float,
        encoding_time: float,
        write_time: float
    ):
        """Log periodic statistics.
        
        Args:
            stream_key: Stream identifier
            read_time: Time spent reading frame
            encoding_time: Time spent encoding frame
            write_time: Time spent writing frame
        """
        if self.should_log_stats():
            total = self.frames_sent + self.frames_skipped + self.frames_diff_sent
            self.logger.info(
                f"Stream [{stream_key}]: {self.frames_sent} sent, "
                f"{self.frames_skipped} skipped, {self.frames_diff_sent} diff | "
                f"Timing: read={read_time*1000:.1f}ms, encode={encoding_time*1000:.1f}ms, "
                f"write={write_time*1000:.1f}ms"
            )
    
    def get_transmission_stats(self, video_codec: str, active_streams: int) -> Dict[str, Any]:
        """Get comprehensive transmission statistics.
        
        Args:
            video_codec: Current video codec being used
            active_streams: Number of active streams
            
        Returns:
            Dictionary with all transmission statistics
        """
        total = self.frames_sent + self.frames_skipped + self.frames_diff_sent
        return {
            "frames_sent_full": self.frames_sent,
            "frames_skipped": self.frames_skipped,
            "frames_diff_sent": self.frames_diff_sent,
            "total_frames_processed": total,
            "skip_rate": (self.frames_skipped / total) if total > 0 else 0.0,
            "diff_rate": (self.frames_diff_sent / total) if total > 0 else 0.0,
            "full_rate": (self.frames_sent / total) if total > 0 else 0.0,
            "bytes_saved": self.bytes_saved,
            "video_codec": video_codec,
            "active_streams": active_streams,
        }
    
    def get_timing_stats(self, stream_key: Optional[str] = None) -> Dict[str, Any]:
        """Get timing statistics for streams.
        
        Args:
            stream_key: Specific stream key, or None for all streams
            
        Returns:
            Dictionary with timing statistics
        """
        if stream_key is None:
            return {
                "per_stream": {
                    sk: {
                        "last_read_time_sec": self.last_read_times.get(sk, 0),
                        "last_write_time_sec": self.last_write_times.get(sk, 0),
                        "last_process_time_sec": self.last_process_times.get(sk, 0),
                    }
                    for sk in self.last_read_times.keys()
                },
                "active_streams": list(self.last_read_times.keys()),
            }
        else:
            read, write, process = self.get_timing(stream_key)
            return {
                "stream_key": stream_key,
                "last_read_time_sec": read,
                "last_write_time_sec": write,
                "last_process_time_sec": process,
            }
    
    def reset(self):
        """Reset all statistics."""
        self.frames_sent = 0
        self.frames_skipped = 0
        self.frames_diff_sent = 0
        self.bytes_saved = 0
        self.last_read_times.clear()
        self.last_write_times.clear()
        self.last_process_times.clear()
        self.logger.info("Reset transmission statistics")
    
    def _normalize_key(self, stream_key: Optional[str]) -> str:
        """Normalize stream key to handle None values."""
        return stream_key if stream_key is not None else "default"

