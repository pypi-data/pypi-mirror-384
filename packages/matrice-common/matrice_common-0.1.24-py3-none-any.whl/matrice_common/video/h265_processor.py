"""Clean H.265 encoder/decoder classes for frame-wise and byte-wise streaming."""
import cv2
import subprocess
import threading
import queue
import logging
import time
import numpy as np
from typing import Optional, Generator
import redis

logger = logging.getLogger(__name__)

# class H265FrameEncoder:
#     """H.265 encoder for individual frames using persistent FFmpeg process for performance."""
    
#     def __init__(self, preset: str = "ultrafast", quality: int = 23, use_hardware: bool = False):
#         """Initialize H.265 frame encoder.
        
#         Args:
#             preset: FFmpeg encoding preset (ultrafast, fast, medium, slow)
#             quality: CRF quality (0-51, lower=better quality)
#             use_hardware: Use hardware acceleration if available
#         """
#         self.preset = preset
#         self.quality = quality
#         self.use_hardware = use_hardware
#         self.process: Optional[subprocess.Popen] = None
#         self.width: Optional[int] = None
#         self.height: Optional[int] = None
#         self.frame_size_bytes: int = 0
#         self._lock = threading.Lock()  # Thread safety for encoder access
        
#     def _start_process(self, width: int, height: int) -> bool:
#         """Start persistent FFmpeg encoding process."""
#         if self.process and self.width == width and self.height == height:
#             return True  # Already running with correct dimensions
            
#         # Stop existing process if dimensions changed
#         if self.process:
#             self._stop_process()
            
#         try:
#             self.width = width
#             self.height = height
#             self.frame_size_bytes = width * height * 3  # BGR
            
#             # Build FFmpeg command for continuous encoding with per-frame keyframes
#             cmd = [
#                 "ffmpeg",
#                 "-f", "rawvideo",
#                 "-pix_fmt", "bgr24",
#                 "-s", f"{width}x{height}",
#                 "-r", "30",  # Nominal framerate (doesn't affect frame independence)
#                 "-i", "-",
#                 "-c:v", "libx265" if not self.use_hardware else "hevc_nvenc",
#                 "-preset", self.preset,
#                 "-x265-params", "keyint=1:min-keyint=1",  # Every frame is keyframe
#                 "-crf", str(self.quality),
#                 "-f", "hevc",
#                 "-flush_packets", "1",  # Flush output immediately
#                 "pipe:1"
#             ]
            
#             # Start persistent process
#             self.process = subprocess.Popen(
#                 cmd,
#                 stdin=subprocess.PIPE,
#                 stdout=subprocess.PIPE,
#                 stderr=subprocess.PIPE,
#                 bufsize=0  # Unbuffered for immediate processing
#             )
            
#             logger.info(f"Started persistent H.265 frame encoder: {width}x{height}")
#             return True
            
#         except Exception as e:
#             logger.error(f"Failed to start H.265 frame encoder: {e}")
#             self._stop_process()
#             return False
            
#     def _stop_process(self):
#         """Stop the encoding process."""
#         if self.process:
#             try:
#                 if self.process.stdin:
#                     self.process.stdin.close()
#                 if self.process.stdout:
#                     self.process.stdout.close()
#                 self.process.terminate()
#                 self.process.wait(timeout=2)
#             except:
#                 try:
#                     self.process.kill()
#                 except:
#                     pass
#             self.process = None
            
#     def _find_nal_unit_boundary(self, data: bytes, start_pos: int = 0) -> int:
#         """Find the next NAL unit start code in H.265 stream.
        
#         H.265 NAL units start with:
#         - 0x00 0x00 0x00 0x01 (4-byte start code)
#         - 0x00 0x00 0x01 (3-byte start code)
        
#         Args:
#             data: Byte stream to search
#             start_pos: Position to start searching from
            
#         Returns:
#             Position of next NAL start code, or -1 if not found
#         """
#         i = start_pos
#         while i < len(data) - 3:
#             # Check for 4-byte start code (0x00 0x00 0x00 0x01)
#             if data[i] == 0x00 and data[i+1] == 0x00 and data[i+2] == 0x00 and data[i+3] == 0x01:
#                 return i
#             # Check for 3-byte start code (0x00 0x00 0x01)
#             elif data[i] == 0x00 and data[i+1] == 0x00 and data[i+2] == 0x01:
#                 return i
#             i += 1
#         return -1
    
#     def encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
#         """Encode single frame to H.265 bytes using persistent process.
        
#         Uses NAL unit boundary detection to ensure complete frames are read.
        
#         Args:
#             frame: OpenCV frame (BGR format)
            
#         Returns:
#             H.265 encoded frame bytes or None if failed
#         """
#         with self._lock:  # Thread-safe encoding
#             try:
#                 height, width = frame.shape[:2]
                
#                 # Start or restart process if needed
#                 if not self._start_process(width, height):
#                     return None
                
#                 if not self.process or not self.process.stdin or not self.process.stdout:
#                     return None
                
#                 # Write frame to encoder
#                 try:
#                     frame_bytes = frame.tobytes()
#                     self.process.stdin.write(frame_bytes)
#                     self.process.stdin.flush()
#                 except (BrokenPipeError, OSError) as e:
#                     logger.warning(f"Encoder pipe broken, restarting: {e}")
#                     self._stop_process()
#                     if not self._start_process(width, height):
#                         return None
#                     frame_bytes = frame.tobytes()
#                     self.process.stdin.write(frame_bytes)
#                     self.process.stdin.flush()
                
#                 # Read encoded frame using NAL unit boundary detection + no-more-data detection
#                 # Since we're in a lock, only one frame is being encoded at a time
#                 buffer = bytearray()
#                 chunk_size = 4096
#                 max_size = self.frame_size_bytes  # Max = raw frame size (safety limit)
#                 read_timeout = 1.0  # 1 second absolute timeout
#                 no_data_timeout = 0.05  # 50ms timeout when no data arrives
#                 start_read_time = time.time()
#                 last_data_time = time.time()
#                 first_nal_found = False
#                 consecutive_empty_reads = 0
#                 max_empty_reads = 5
                
#                 while len(buffer) < max_size:
#                     # Check absolute timeout
#                     if time.time() - start_read_time > read_timeout:
#                         if len(buffer) > 0:
#                             logger.warning(f"Absolute timeout after {len(buffer)} bytes, returning data")
#                             return bytes(buffer)
#                         logger.error("Read timeout with no data")
#                         return None
                    
#                     # Read chunk (non-blocking behavior via small reads)
#                     try:
#                         chunk = self.process.stdout.read(chunk_size)
                        
#                         if chunk:
#                             # Got data
#                             buffer.extend(chunk)
#                             last_data_time = time.time()
#                             consecutive_empty_reads = 0
                            
#                             # Mark that we found first NAL
#                             if not first_nal_found:
#                                 first_nal_pos = self._find_nal_unit_boundary(buffer, 0)
#                                 if first_nal_pos >= 0:
#                                     first_nal_found = True
#                         else:
#                             # No data available
#                             consecutive_empty_reads += 1
                            
#                             # If we have data and no new data is coming, frame is complete
#                             if len(buffer) > 0 and first_nal_found:
#                                 time_since_last_data = time.time() - last_data_time
                                
#                                 if time_since_last_data > no_data_timeout or consecutive_empty_reads >= max_empty_reads:
#                                     # No data for 50ms or 5 consecutive empty reads
#                                     # Frame encoding is complete
#                                     return bytes(buffer)
                            
#                             # Wait briefly before next read attempt
#                             time.sleep(0.005)  # 5ms
#                             continue
                    
#                     except Exception as e:
#                         if len(buffer) > 0:
#                             logger.debug(f"Read error after {len(buffer)} bytes: {e}, returning data")
#                             return bytes(buffer)
#                         else:
#                             raise
                
#                 # Reached max size
#                 if len(buffer) > 0:
#                     logger.warning(f"Reached max size {max_size}, returning {len(buffer)} bytes")
#                     return bytes(buffer)
                
#                 logger.error("No data read from encoder")
#                 return None
                    
#             except Exception as e:
#                 logger.error(f"Frame encoding error: {e}")
#                 self._stop_process()  # Reset on error
#                 return None
    
#     def close(self):
#         """Close the encoder and cleanup resources."""
#         with self._lock:
#             self._stop_process()
            
#     def __del__(self):
#         """Cleanup on deletion."""
#         self.close()
        
class H265FrameEncoder:
    """H.265 encoder for individual frames (like your RTSP → Redis frame-wise example)."""
    
    def __init__(self, preset: str = "ultrafast", quality: int = 23, use_hardware: bool = False):
        """Initialize H.265 frame encoder.
        
        Args:
            preset: FFmpeg encoding preset (ultrafast, fast, medium, slow)
            quality: CRF quality (0-51, lower=better quality)
            use_hardware: Use hardware acceleration if available
        """
        self.preset = preset
        self.quality = quality
        self.use_hardware = use_hardware
        
    def encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        """Encode single frame to H.265 bytes.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            H.265 encoded frame bytes or None if failed
        """
        try:
            height, width = frame.shape[:2]
            
            # Build FFmpeg command for single frame H.265 encoding
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{width}x{height}",
                "-i", "-",
                "-c:v", "libx265" if not self.use_hardware else "hevc_nvenc",
                "-preset", self.preset,
                "-x265-params", "keyint=1",  # Every frame is keyframe for compatibility
                "-crf", str(self.quality),
                "-f", "hevc",
                "pipe:1"
            ]
            
            # Execute FFmpeg process
            process = subprocess.Popen(
                cmd, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send frame data and get H.265 output
            stdout, stderr = process.communicate(input=frame.tobytes(), timeout=5)
            
            if process.returncode == 0 and stdout:
                return stdout
            else:
                logger.error(f"Frame encoding failed: {stderr.decode() if stderr else 'Unknown error'}")
                return None
                
        except Exception as e:
            logger.error(f"Frame encoding error: {e}")
            return None


class H265StreamEncoder:
    """H.265 encoder for continuous byte streams (like your RTSP → Redis stream example)."""
    
    def __init__(self, width: int, height: int, fps: int, preset: str = "fast", quality: int = 23, use_hardware: bool = False):
        """Initialize H.265 stream encoder.
        
        Args:
            width: Frame width
            height: Frame height
            fps: Frames per second
            preset: FFmpeg encoding preset
            quality: CRF quality (0-51, lower=better quality)
            use_hardware: Use hardware acceleration if available
        """
        self.width = width
        self.height = height
        self.fps = fps
        self.preset = preset
        self.quality = quality
        self.use_hardware = use_hardware
        self.process: Optional[subprocess.Popen] = None
        
    def start(self) -> bool:
        """Start the continuous H.265 encoding process."""
        if self.process:
            return True
            
        try:
            # Build FFmpeg command for continuous stream encoding
            cmd = [
                "ffmpeg", "-y",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "-s", f"{self.width}x{self.height}",
                "-r", str(self.fps),
                "-i", "-",
                "-c:v", "libx265" if not self.use_hardware else "hevc_nvenc", 
                "-preset", self.preset,
                "-crf", str(self.quality),
                "-f", "hevc",
                "pipe:1"
            ]
            
            # Start FFmpeg process with pipes
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # Unbuffered for real-time
            )
            
            logger.info(f"Started H.265 stream encoder: {self.width}x{self.height}@{self.fps}fps")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start H.265 stream encoder: {e}")
            self.stop()
            return False
            
    def stop(self):
        """Stop the encoding process."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                self.process.kill()
            self.process = None
            
    def encode_frame(self, frame: np.ndarray) -> bool:
        """Add frame to continuous encoding stream.
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            True if frame was added successfully
        """
        if not self.process or not self.process.stdin:
            return False
            
        try:
            self.process.stdin.write(frame.tobytes())
            self.process.stdin.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to encode frame: {e}")
            return False
            
    def read_bytes(self, chunk_size: int = 4096) -> Optional[bytes]:
        """Read encoded H.265 bytes from the stream.
        
        Args:
            chunk_size: Size of chunk to read
            
        Returns:
            H.265 encoded bytes or None
        """
        if not self.process or not self.process.stdout:
            return None
            
        try:
            return self.process.stdout.read(chunk_size)
        except Exception as e:
            logger.error(f"Failed to read H.265 bytes: {e}")
            return None


class H265FrameDecoder:
    """H.265 decoder for individual frames."""
    
    def __init__(self, use_hardware: bool = False):
        """Initialize H.265 frame decoder.
        
        Args:
            use_hardware: Use hardware decoding if available
        """
        self.use_hardware = use_hardware
        
    def decode_frame(self, h265_data: bytes, width: int, height: int) -> Optional[np.ndarray]:
        """Decode H.265 frame to OpenCV frame.
        
        Args:
            h265_data: H.265 encoded frame bytes
            width: Expected frame width
            height: Expected frame height
            
        Returns:
            OpenCV frame (BGR format) or None if failed
        """
        try:
            # Build FFmpeg command for single frame decoding
            cmd = [
                "ffmpeg", "-y",
                "-f", "hevc",
                "-i", "-",
                "-f", "rawvideo", 
                "-pix_fmt", "bgr24",
                "pipe:1"
            ]
            
            # Execute FFmpeg
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send H.265 data and get raw frame
            stdout, stderr = process.communicate(input=h265_data, timeout=5)
            
            if process.returncode == 0 and stdout:
                # Convert raw bytes to OpenCV frame
                frame_data = np.frombuffer(stdout, dtype=np.uint8)
                
                # Calculate expected frame size
                expected_size = width * height * 3  # BGR
                if len(frame_data) >= expected_size:
                    frame = frame_data[:expected_size].reshape((height, width, 3))
                    return frame
                else:
                    logger.error(f"Insufficient frame data: {len(frame_data)}/{expected_size}")
                    return None
            else:
                logger.error(f"Frame decoding failed: {stderr.decode() if stderr else 'Unknown error'}")
                return None
                
        except Exception as e:
            logger.error(f"Frame decoding error: {e}")
            return None


class H265StreamDecoder:
    """H.265 decoder for continuous byte streams."""
    
    def __init__(self, width: int, height: int, use_hardware: bool = False):
        """Initialize H.265 stream decoder.
        
        Args:
            width: Expected frame width
            height: Expected frame height
            use_hardware: Use hardware decoding if available
        """
        self.width = width
        self.height = height
        self.use_hardware = use_hardware
        self.process: Optional[subprocess.Popen] = None
        
    def start(self) -> bool:
        """Start the continuous H.265 decoding process."""
        if self.process:
            return True
            
        try:
            # Build FFmpeg command for continuous stream decoding
            cmd = [
                "ffmpeg", "-y",
                "-f", "hevc",
                "-i", "-",
                "-f", "rawvideo",
                "-pix_fmt", "bgr24",
                "pipe:1"
            ]
            
            # Start FFmpeg process
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # Unbuffered for real-time
            )
            
            logger.info(f"Started H.265 stream decoder: {self.width}x{self.height}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start H.265 stream decoder: {e}")
            self.stop()
            return False
            
    def stop(self):
        """Stop the decoding process."""
        if self.process:
            try:
                self.process.stdin.close()
                self.process.stdout.close()
                self.process.terminate()
                self.process.wait(timeout=3)
            except:
                self.process.kill()
            self.process = None
            
    def decode_bytes(self, h265_chunk: bytes) -> bool:
        """Add H.265 bytes to decoding stream.
        
        Args:
            h265_chunk: H.265 encoded bytes
            
        Returns:
            True if bytes were added successfully
        """
        if not self.process or not self.process.stdin:
            return False
            
        try:
            self.process.stdin.write(h265_chunk)
            self.process.stdin.flush()
            return True
        except Exception as e:
            logger.error(f"Failed to decode bytes: {e}")
            return False
            
    def read_frame(self) -> Optional[np.ndarray]:
        """Read next decoded frame from stream.
        
        Returns:
            OpenCV frame (BGR format) or None
        """
        if not self.process or not self.process.stdout:
            return None
            
        try:
            # Read one complete frame
            frame_size = self.width * self.height * 3  # BGR
            frame_data = self.process.stdout.read(frame_size)
            
            if len(frame_data) == frame_size:
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((self.height, self.width, 3))
                return frame
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to read decoded frame: {e}")
            return None


# Consumer Classes for Redis Integration

class H265FrameConsumer:
    """Consumer for frame-wise H.265 from Redis (like your consumer example)."""
    
    def __init__(self, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """Initialize frame consumer."""
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.decoder = H265FrameDecoder()
        
    def consume_frames(self, channel: str, width: int, height: int) -> Generator[np.ndarray, None, None]:
        """Consume H.265 frames from Redis channel.
        
        Args:
            channel: Redis channel name
            width: Frame width
            height: Frame height
            
        Yields:
            Decoded OpenCV frames
        """
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channel)
        
        logger.info(f"Consuming H.265 frames from channel: {channel}")
        
        try:
            for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                    
                try:
                    h265_data = message["data"]
                    frame = self.decoder.decode_frame(h265_data, width, height)
                    if frame is not None:
                        yield frame
                except Exception as e:
                    logger.error(f"Frame decode error: {e}")
                    
        finally:
            pubsub.close()


class H265StreamConsumer:
    """Consumer for continuous H.265 stream from Redis (like your stream consumer example)."""
    
    def __init__(self, width: int, height: int, redis_host: str = "localhost", redis_port: int = 6379, redis_db: int = 0):
        """Initialize stream consumer."""
        self.width = width
        self.height = height
        self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)
        self.decoder = H265StreamDecoder(width, height)
        self.frame_queue = queue.Queue(maxsize=30)
        self.stop_consuming = False
        
    def start_consuming(self, channel: str) -> bool:
        """Start consuming H.265 stream from Redis.
        
        Args:
            channel: Redis channel name
            
        Returns:
            True if started successfully
        """
        if not self.decoder.start():
            return False
            
        # Start Redis consumer thread
        self.stop_consuming = False
        self.redis_thread = threading.Thread(target=self._consume_redis_stream, args=(channel,), daemon=True)
        self.frame_reader_thread = threading.Thread(target=self._read_frames, daemon=True)
        
        self.redis_thread.start()
        self.frame_reader_thread.start()
        
        logger.info(f"Started consuming H.265 stream from channel: {channel}")
        return True
        
    def stop_consuming(self):
        """Stop consuming."""
        self.stop_consuming = True
        self.decoder.stop()
        
    def get_frames(self) -> Generator[np.ndarray, None, None]:
        """Generator that yields decoded frames."""
        while not self.stop_consuming:
            try:
                frame = self.frame_queue.get(timeout=0.1)
                yield frame
            except queue.Empty:
                continue
                
    def _consume_redis_stream(self, channel: str):
        """Background thread to consume H.265 chunks from Redis."""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channel)
        
        try:
            for message in pubsub.listen():
                if self.stop_consuming:
                    break
                    
                if message["type"] != "message":
                    continue
                    
                try:
                    h265_chunk = message["data"]
                    self.decoder.decode_bytes(h265_chunk)
                except Exception as e:
                    logger.error(f"Stream decode error: {e}")
        finally:
            pubsub.close()
            
    def _read_frames(self):
        """Background thread to read decoded frames."""
        while not self.stop_consuming:
            try:
                frame = self.decoder.read_frame()
                if frame is not None:
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame)
                    else:
                        # Drop oldest frame
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put(frame)
                        except queue.Empty:
                            pass
                else:
                    time.sleep(0.001)  # Small delay if no frame
            except Exception as e:
                logger.error(f"Frame read error: {e}")


# Utility functions for easy usage
def encode_frame_h265(frame: np.ndarray, quality: int = 23) -> Optional[bytes]:
    """Quick utility to encode a frame to H.265."""
    encoder = H265FrameEncoder(quality=quality)
    return encoder.encode_frame(frame)


def decode_frame_h265(h265_data: bytes, width: int, height: int) -> Optional[np.ndarray]:
    """Quick utility to decode H.265 frame.""" 
    decoder = H265FrameDecoder()
    return decoder.decode_frame(h265_data, width, height)