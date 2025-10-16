"""
Audio processing utilities for voice operations
"""

import logging
import numpy as np

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio processing operations."""
    
    @staticmethod
    def process_audio_chunk(audio_chunk, sample_rate: int = 16000) -> np.ndarray:
        """Process audio chunk from websocket (typically from VAD) into numpy array.
        
        Args:
            audio_chunk: Raw audio data from websocket (bytes, bytearray, or memoryview)
            sample_rate: Sample rate of the audio (default 16kHz from VAD)
            
        Returns:
            np.ndarray: Processed audio buffer ready for voice pipeline
        """
        try:
            # Handle different input types
            if hasattr(audio_chunk, 'tobytes'):
                # Handle memoryview or similar objects
                audio_bytes = audio_chunk.tobytes()
            elif isinstance(audio_chunk, (bytes, bytearray)):
                # Handle bytes or bytearray directly
                audio_bytes = bytes(audio_chunk)
            else:
                # Try to convert to bytes if it's not already
                try:
                    audio_bytes = bytes(audio_chunk)
                except Exception as convert_error:
                    logger.error(f"Unable to convert audio_chunk to bytes: {convert_error}")
                    logger.error(f"Audio chunk type: {type(audio_chunk)}")
                    raise ValueError(f"Unsupported audio chunk type: {type(audio_chunk)}")
            
            logger.debug(f"Processing audio chunk: {len(audio_bytes)} bytes, type: {type(audio_chunk)}")
            
            # Convert bytes to numpy array (assuming float32 from VAD web)
            try:
                audio_float32 = np.frombuffer(audio_bytes, dtype=np.float32)
                logger.debug(f"Converted to float32 array: {len(audio_float32)} samples")
            except ValueError as e:
                # If float32 doesn't work, try other formats
                logger.warning(f"Failed to parse as float32: {e}. Trying other formats...")
                
                # Try int16 format
                try:
                    audio_int16_raw = np.frombuffer(audio_bytes, dtype=np.int16)
                    audio_float32 = audio_int16_raw.astype(np.float32) / 32767.0
                    logger.debug(f"Converted from int16 to float32: {len(audio_float32)} samples")
                except ValueError:
                    # Try uint8 format
                    try:
                        audio_uint8 = np.frombuffer(audio_bytes, dtype=np.uint8)
                        audio_float32 = (audio_uint8.astype(np.float32) - 128) / 128.0
                        logger.debug(f"Converted from uint8 to float32: {len(audio_float32)} samples")
                    except ValueError as final_error:
                        logger.error(f"Unable to parse audio data in any known format: {final_error}")
                        raise ValueError(f"Unable to parse audio data: {final_error}")
            
            # Resample to 24kHz if needed (voice pipeline expects 24kHz)
            if sample_rate != 24000:
                # Simple resampling - for production use proper resampling library
                resample_ratio = 24000 / sample_rate
                new_length = int(len(audio_float32) * resample_ratio)
                indices = np.linspace(0, len(audio_float32) - 1, new_length)
                audio_float32 = np.interp(indices, np.arange(len(audio_float32)), audio_float32)
                logger.debug(f"Resampled from {sample_rate}Hz to 24kHz: {new_length} samples")
            
            # Convert to int16 as expected by voice pipeline
            audio_int16 = (audio_float32 * 32767).astype(np.int16)
            
            logger.debug(f"Final processed audio: {len(audio_int16)} samples at 24kHz")
            return audio_int16
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            logger.error(f"Audio chunk info - Type: {type(audio_chunk)}, Length: {len(audio_chunk) if hasattr(audio_chunk, '__len__') else 'N/A'}")
            raise e