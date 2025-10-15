"""
Voice processing runner with audio utilities
"""

import numpy as np
from typing import Optional, AsyncGenerator, Dict, Any
from agents.voice import SingleAgentVoiceWorkflow, VoicePipeline, AudioInput
from ..event_handlers import MCPServerManager
from .base_runner import BaseRunner


class VoiceRunner(BaseRunner):
    """Runner for voice processing workflows."""
    
    def process_audio_chunk(self, audio_chunk, sample_rate: int = 16000) -> np.ndarray:
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
                    self.logger.error(f"Unable to convert audio_chunk to bytes: {convert_error}")
                    self.logger.error(f"Audio chunk type: {type(audio_chunk)}")
                    raise ValueError(f"Unsupported audio chunk type: {type(audio_chunk)}")
            
            self.logger.debug(f"Processing audio chunk: {len(audio_bytes)} bytes, type: {type(audio_chunk)}")
            
            # Convert bytes to numpy array (assuming float32 from VAD web)
            try:
                audio_float32 = np.frombuffer(audio_bytes, dtype=np.float32)
                self.logger.debug(f"Converted to float32 array: {len(audio_float32)} samples")
            except ValueError as e:
                # If float32 doesn't work, try other formats
                self.logger.warning(f"Failed to parse as float32: {e}. Trying other formats...")
                
                # Try int16 format
                try:
                    audio_int16_raw = np.frombuffer(audio_bytes, dtype=np.int16)
                    audio_float32 = audio_int16_raw.astype(np.float32) / 32767.0
                    self.logger.debug(f"Converted from int16 to float32: {len(audio_float32)} samples")
                except ValueError:
                    # Try uint8 format
                    try:
                        audio_uint8 = np.frombuffer(audio_bytes, dtype=np.uint8)
                        audio_float32 = (audio_uint8.astype(np.float32) - 128) / 128.0
                        self.logger.debug(f"Converted from uint8 to float32: {len(audio_float32)} samples")
                    except ValueError as final_error:
                        self.logger.error(f"Unable to parse audio data in any known format: {final_error}")
                        raise ValueError(f"Unable to parse audio data: {final_error}")
            
            # Resample to 24kHz if needed (voice pipeline expects 24kHz)
            if sample_rate != 24000:
                # Simple resampling - for production use proper resampling library
                resample_ratio = 24000 / sample_rate
                new_length = int(len(audio_float32) * resample_ratio)
                indices = np.linspace(0, len(audio_float32) - 1, new_length)
                audio_float32 = np.interp(indices, np.arange(len(audio_float32)), audio_float32)
                self.logger.debug(f"Resampled from {sample_rate}Hz to 24kHz: {new_length} samples")
            
            # Convert to int16 as expected by voice pipeline
            audio_int16 = (audio_float32 * 32767).astype(np.int16)
            
            self.logger.debug(f"Final processed audio: {len(audio_int16)} samples at 24kHz")
            return audio_int16
            
        except Exception as e:
            self.logger.error(f"Audio processing error: {e}")
            self.logger.error(f"Audio chunk info - Type: {type(audio_chunk)}, Length: {len(audio_chunk) if hasattr(audio_chunk, '__len__') else 'N/A'}")
            raise e
    
    async def _process_voice_events(self, result, agent_name: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process voice streaming events from pipeline.
        
        Args:
            result: Voice pipeline result
            agent_name: Name of the agent processing voice
            
        Yields:
            Dict: Voice event responses
        """
        async for event in result.stream():
            self.logger.debug(f"Received voice event: {event.type}, event object: {type(event)}")
            if hasattr(event, '__dict__'):
                self.logger.debug(f"Event attributes: {vars(event)}")
            
            if event.type == "voice_stream_event_audio":
                # Audio output from TTS - ensure data is bytes-like
                try:
                    if hasattr(event.data, 'tobytes'):
                        audio_data = event.data.tobytes()
                    elif isinstance(event.data, (bytes, bytearray)):
                        audio_data = bytes(event.data)
                    elif isinstance(event.data, np.ndarray):
                        audio_data = event.data.tobytes()
                    else:
                        self.logger.warning(f"Unknown audio data type: {type(event.data)}, trying to convert to bytes")
                        audio_data = bytes(event.data)
                    
                    self.logger.debug(f"Yielding voice audio for {agent_name}: {len(audio_data)} bytes, original type: {type(event.data)}")
                    yield {
                        "type": "voice_audio",
                        "data": audio_data,
                        "agent_name": agent_name,
                        "is_done": False
                    }
                except Exception as audio_error:
                    self.logger.error(f"Error processing voice audio data for {agent_name}: {audio_error}")
                    self.logger.error(f"Audio data type: {type(event.data)}, length: {len(event.data) if hasattr(event.data, '__len__') else 'N/A'}")
                    # Continue without yielding this audio chunk
                    continue
                    
            elif event.type == "voice_stream_event_text":
                # Text response from agent
                text_content = getattr(event, 'text', None) or getattr(event, 'content', None) or getattr(event, 'data', None) or str(event)
                self.logger.debug(f"Voice text event for {agent_name} - content: {text_content}")
                yield {
                    "type": "text_response",
                    "content": text_content,
                    "agent_name": agent_name,
                    "is_done": False
                }
                
            elif hasattr(event, 'final_output') and event.final_output:
                # Final completion
                yield {
                    "type": "completion",
                    "content": event.final_output,
                    "agent_name": agent_name,
                    "is_done": True
                }
    
    async def run_team_voice_stream(self, audio_buffer: np.ndarray, 
                                   debug: bool = False, 
                                   session_id: Optional[str] = None, 
                                   session_context: Optional[Dict[str, Any]] = None, 
                                   max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run team with voice input and streaming audio/text outputs.
        
        Args:
            audio_buffer: NumPy array of audio samples (int16, 24kHz sample rate)
            debug: Whether to show debug info
            session_id: Session ID for conversation persistence
            session_context: Session context data
            max_turns: Maximum number of turns
            
        Yields:
            Dict: Stream outputs including voice_stream_event_audio and text responses
        """
        self.logger.info(f"Starting voice processing with {self.team.orchestrator.name}")
        
        # Initialize MCP manager and connect servers
        mcp_manager = MCPServerManager()
        all_agents = [self.team.orchestrator] + list(self.team.workers.values())
        await mcp_manager.connect_servers(all_agents)
        
        session = None
        try:
            # Create voice pipeline with the orchestrator
            voice_workflow = SingleAgentVoiceWorkflow(self.team.orchestrator)
            voice_pipeline = VoicePipeline(workflow=voice_workflow)
            
            # Create audio input from buffer
            audio_input = AudioInput(buffer=audio_buffer)
            
            # Get session for persistence
            session = self._get_session(session_id, session_context)
            self._log_session_info(session, session_id, "voice team")
            
            # Run the voice pipeline
            result = await voice_pipeline.run(audio_input)
            
            self.logger.info("Starting to process voice streaming events...")
            
            # Stream events from voice pipeline
            async for response in self._process_voice_events(result, self.team.orchestrator.name):
                yield response
            
        except Exception as e:
            self.logger.error(f"Voice processing error: {e}")
            yield {
                "type": "error",
                "content": f"Voice processing failed: {str(e)}",
                "agent_name": self.team.orchestrator.name,
                "is_done": True
            }
            raise e
        finally:
            await self.cleanup_manager.cleanup_all(session, mcp_manager, all_agents)
    
    async def run_single_agent_voice_stream(self, agent_name: str, audio_buffer: np.ndarray, 
                                           debug: bool = False, 
                                           session_id: Optional[str] = None, 
                                           session_context: Optional[Dict[str, Any]] = None, 
                                           max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a specific agent with voice input and streaming audio/text outputs.
        
        Args:
            agent_name: Name of the agent to run
            audio_buffer: NumPy array of audio samples (int16, 24kHz sample rate)
            debug: Whether to show debug info
            session_id: Session ID for conversation persistence
            session_context: Session context data
            max_turns: Maximum number of turns
            
        Yields:
            Dict: Stream outputs including voice_stream_event_audio and text responses
        """
        # Get the target agent
        target_agent = self.team.get_agent(agent_name)
        if not target_agent:
            yield {
                "type": "error",
                "content": f"Agent '{agent_name}' not found in team configuration"
            }
            return
        
        self.logger.info(f"Starting voice processing with agent: {agent_name}")
        
        # Initialize MCP manager
        mcp_manager = MCPServerManager()
        await mcp_manager.connect_servers([target_agent])
        
        session = None
        try:
            # Create voice pipeline with the target agent
            voice_workflow = SingleAgentVoiceWorkflow(target_agent)
            voice_pipeline = VoicePipeline(workflow=voice_workflow)
            
            # Create audio input from buffer
            audio_input = AudioInput(buffer=audio_buffer)
            
            # Get session for persistence
            session = self._get_session(session_id, session_context)
            self._log_session_info(session, session_id, f"voice agent '{agent_name}'")
            
            # Run the voice pipeline
            result = await voice_pipeline.run(audio_input)
            
            self.logger.info(f"Starting to process voice streaming events for agent: {agent_name}")
            
            # Stream events from voice pipeline
            async for response in self._process_voice_events(result, agent_name):
                yield response
            
        except Exception as e:
            self.logger.error(f"Voice processing error for agent {agent_name}: {e}")
            yield {
                "type": "error",
                "content": f"Voice processing failed: {str(e)}",
                "agent_name": agent_name,
                "is_done": True
            }
            raise e
        finally:
            await self.cleanup_manager.cleanup_all(session, mcp_manager, [target_agent])