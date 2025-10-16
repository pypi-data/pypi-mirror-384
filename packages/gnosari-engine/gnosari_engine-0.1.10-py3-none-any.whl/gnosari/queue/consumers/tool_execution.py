"""Tool execution message and consumer for async tool processing."""

import uuid
import asyncio
import importlib
import logging
from typing import Dict, Any, Optional
from pydantic import Field
from ..base import BaseMessage, BaseConsumer
from ..app import celery_app
from ...tools.interfaces import AsyncTool

# Set up logger for this module
logger = logging.getLogger(__name__)


class ToolExecutionMessage(BaseMessage):
    """Message for async tool execution."""
    
    task_id: str = Field(description="Unique task identifier")
    tool_name: str = Field(description="Name of the tool to execute")
    tool_module: str = Field(description="Module path of the tool class")
    tool_class: str = Field(description="Class name of the tool")
    tool_init_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for tool initialization")
    tool_args: str = Field(description="JSON string of tool execution arguments")
    context_data: Dict[str, Any] = Field(default_factory=dict, description="Execution context data")
    agent_id: Optional[str] = Field(default=None, description="ID of the agent that requested the tool")
    session_id: Optional[str] = Field(default=None, description="Session ID for the tool execution")
    team_data: Optional[Dict[str, Any]] = Field(default=None, description="Serialized team data for delegation tools")
    
    @classmethod
    def create(cls, 
               task_id: str,
               tool_name: str,
               tool_module: str,
               tool_class: str,
               tool_args: str,
               tool_init_args: Dict[str, Any] = None,
               context_data: Dict[str, Any] = None,
               agent_id: str = None,
               session_id: str = None,
               team_data: Dict[str, Any] = None) -> "ToolExecutionMessage":
        """Create a new tool execution message.
        
        Args:
            task_id: Unique task identifier
            tool_name: Name of the tool to execute
            tool_module: Module path of the tool class
            tool_class: Class name of the tool
            tool_args: JSON string of tool execution arguments
            tool_init_args: Arguments for tool initialization
            context_data: Execution context data
            agent_id: ID of the agent that requested the tool
            session_id: Session ID for the tool execution
            team_data: Serialized team data for delegation tools
            
        Returns:
            ToolExecutionMessage: New message instance
        """
        return cls(
            message_id=str(uuid.uuid4()),
            task_id=task_id,
            tool_name=tool_name,
            tool_module=tool_module,
            tool_class=tool_class,
            tool_init_args=tool_init_args or {},
            tool_args=tool_args,
            context_data=context_data or {},
            agent_id=agent_id,
            session_id=session_id,
            team_data=team_data
        )


class ToolExecutionConsumer(BaseConsumer):
    """Consumer for processing async tool execution messages.
    
    This consumer processes tools that implement the AsyncTool interface
    and support queue-based async execution.
    """
    
    def __init__(self):
        """Initialize tool execution consumer."""
        super().__init__()
        self.tool_registry = None
        self.team = None
        self.team_executor = None
    
    def set_dependencies(self, tool_registry=None, team=None, team_executor=None):
        """Set dependencies for tool execution.
        
        Args:
            tool_registry: Tool registry for resolving tool instances
            team: Team instance for tool dependencies
            team_executor: Team executor for tool dependencies
        """
        self.tool_registry = tool_registry
        self.team = team
        self.team_executor = team_executor
    
    async def process(self, message: ToolExecutionMessage) -> Dict[str, Any]:
        """Process a tool execution message.
        
        Args:
            message: The tool execution message to process
            
        Returns:
            Dict[str, Any]: Tool execution result
        """
        logger.info(f"🔧 Processing async tool execution: {message.tool_name}")
        logger.info(f"   Task ID: {message.task_id}")
        logger.info(f"   Agent: {message.agent_id or 'Unknown'}")
        logger.info(f"   Session: {message.session_id or 'Unknown'}")
        logger.debug(f"   Module: {message.tool_module}")
        logger.debug(f"   Class: {message.tool_class}")
        logger.debug(f"   Tool Args: {message.tool_args}")
        logger.debug(f"   Init Args: {message.tool_init_args}")
        logger.debug(f"   Context Data: {message.context_data}")
        
        try:
            logger.debug(f"Creating tool instance for {message.tool_name}")
            # Get tool instance dynamically from message configuration
            tool_instance = await self._create_tool_instance(message)
            
            if not tool_instance:
                error_msg = f"Failed to create tool instance '{message.tool_name}' from {message.tool_module}.{message.tool_class}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.debug(f"Successfully created tool instance: {type(tool_instance)}")
            
            # Create context for tool execution
            logger.debug("Creating RunContextWrapper for tool execution")
            context_wrapper = self._create_context_wrapper(message)
            
            # Execute the tool
            logger.debug(f"Executing tool {message.tool_name} with args: {message.tool_args}")
            result = await self._execute_tool(tool_instance, context_wrapper, message.tool_args)
            logger.info(f"✅ Tool {message.tool_name} executed successfully")
            logger.debug(f"Tool result: {str(result)[:200]}...")
            
            return {
                "task_id": message.task_id,
                "tool_name": message.tool_name,
                "status": "success",
                "result": result,
                "agent_id": message.agent_id,
                "session_id": message.session_id,
                "context_data": message.context_data,
                "processed_at": message.created_at.isoformat()
            }
            
        except Exception as e:
            error_result = f"Tool execution failed: {str(e)}"
            logger.error(f"❌ Tool execution error for {message.tool_name}: {error_result}")
            logger.debug(f"Full exception details:", exc_info=True)
            
            return {
                "task_id": message.task_id,
                "tool_name": message.tool_name,
                "status": "error",
                "error": error_result,
                "agent_id": message.agent_id,
                "session_id": message.session_id,
                "context_data": message.context_data,
                "processed_at": message.created_at.isoformat()
            }
    
    async def _create_tool_instance(self, message: ToolExecutionMessage) -> Any:
        """Create tool instance dynamically from message configuration.
        
        Args:
            message: Tool execution message containing configuration
            
        Returns:
            Tool instance or None if creation failed
        """
        try:
            logger.debug(f"Importing module: {message.tool_module}")
            # Import the module
            module = importlib.import_module(message.tool_module)
            logger.debug(f"Successfully imported module: {message.tool_module}")
            
            # Get the tool class
            logger.debug(f"Getting class {message.tool_class} from module")
            tool_class = getattr(module, message.tool_class)
            logger.debug(f"Successfully got class: {tool_class}")
            
            # Create tool instance with initialization arguments
            # If team_data is available, add it to init_args for tools that need it
            init_args = message.tool_init_args.copy() if message.tool_init_args else {}
            
            # For delegation tools, don't pass team_config as init arg since it's handled separately
            # The tool will be initialized without team_config and then dependencies will be set
            
            if init_args:
                logger.debug(f"Creating tool instance with init args: {init_args}")
                tool_instance = tool_class(**init_args)
            else:
                logger.debug("Creating tool instance with no init args")
                tool_instance = tool_class()
            
            logger.debug(f"Created tool instance: {type(tool_instance)}")
            
            
            # Get the FunctionTool from the tool instance
            if hasattr(tool_instance, 'get_tool'):
                logger.debug("Getting tool via get_tool() method")
                return tool_instance.get_tool()
            elif hasattr(tool_instance, 'tool'):
                logger.debug("Getting tool via .tool attribute")
                return tool_instance.tool
            else:
                logger.debug("Using tool instance directly")
                # Assume it's already a FunctionTool
                return tool_instance
            
        except ImportError as e:
            error_msg = f"Failed to import module {message.tool_module}: {e}"
            logger.error(error_msg)
            return None
        except AttributeError as e:
            error_msg = f"Failed to get class {message.tool_class} from {message.tool_module}: {e}"
            logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Failed to create tool instance {message.tool_name}: {e}"
            logger.error(error_msg)
            logger.debug("Full exception details:", exc_info=True)
            return None
    
    # Removed _reconstruct_team_dependencies method - delegation tools now build teams on demand from context
    
    def _create_context_wrapper(self, message: ToolExecutionMessage):
        """Create a RunContextWrapper from pre-serialized context data.
        
        Args:
            message: Tool execution message
            
        Returns:
            RunContextWrapper with TeamContext if available
        """
        from agents import RunContextWrapper
        from ...engine.runners.team_runner import TeamContext
        
        # All tools should use consistent context_wrapper approach
        if 'context_wrapper' not in message.context_data:
            logger.error(f"Tool '{message.tool_name}' requires context_wrapper in context_data but none found")
            raise ValueError(f"Missing required context_wrapper for tool '{message.tool_name}'")
        
        logger.debug(f"Using pre-serialized RunContextWrapper from context_data for {message.tool_name}")
        wrapper_data = message.context_data['context_wrapper']
        
        # Reconstruct TeamContext from serialized data
        team_context = TeamContext(
            original_config=wrapper_data['context']['original_config'],
            team=wrapper_data['context'].get('team'),  # Will be None, that's fine
            session_id=wrapper_data['context']['session_id'],
            session_context=wrapper_data['context']['session_context']
        )
        
        # Create RunContextWrapper
        context_wrapper = RunContextWrapper(context=team_context)
        
        # Set additional attributes if the wrapper supports them
        if hasattr(context_wrapper, 'agent_id'):
            context_wrapper.agent_id = wrapper_data.get('agent_id')
        if hasattr(context_wrapper, 'session_id'):
            context_wrapper.session_id = wrapper_data.get('session_id')
        
        logger.debug(f"Reconstructed RunContextWrapper with agent_id={wrapper_data.get('agent_id')}, session_id={wrapper_data.get('session_id')}")
        return context_wrapper
    
    async def _execute_tool(self, tool_instance: Any, context: Any, args: str) -> str:
        """Execute the tool with given arguments.
        
        Args:
            tool_instance: Tool instance to execute (FunctionTool with on_invoke_tool method)
            context: Execution context (RunContextWrapper)
            args: Tool arguments as JSON string
            
        Returns:
            Tool execution result
        """
        logger.debug(f"Executing tool: {type(tool_instance)}")
        
        try:
            # All tools use FunctionTool interface with on_invoke_tool method
            logger.debug("Executing FunctionTool with on_invoke_tool method")
            result = await asyncio.wait_for(
                tool_instance.on_invoke_tool(context, args),
                timeout=600.0  # 10 minute timeout for tool execution
            )
            return result
                
        except asyncio.TimeoutError:
            logger.error("Tool execution timed out after 10 minutes")
            raise ValueError("Tool execution timed out after 10 minutes")
        except asyncio.CancelledError:
            logger.warning("Tool execution was cancelled")
            # Don't re-raise - let the cleanup happen gracefully
            return "❌ Tool execution was cancelled"
    
    def on_success(self, result: Dict[str, Any], message: ToolExecutionMessage) -> None:
        """Called when tool execution succeeds."""
        logger.info(f"✅ Successfully executed tool {message.tool_name} (Task: {message.task_id})")
        logger.debug(f"Success result: {result}")
    
    def on_failure(self, exc: Exception, message: ToolExecutionMessage) -> None:
        """Called when tool execution fails."""
        logger.error(f"❌ Failed to execute tool {message.tool_name} (Task: {message.task_id}): {exc}")
        logger.debug("Failure exception details:", exc_info=True)
    
    def should_retry(self, exc: Exception, message: ToolExecutionMessage) -> bool:
        """Determine if a failed tool execution should be retried."""
        # Don't retry certain types of errors
        if isinstance(exc, (ValueError, ImportError, AttributeError)):
            logger.warning(f"Not retrying {message.tool_name} due to {type(exc).__name__}: {exc}")
            return False
        
        should_retry = message.retry_count < message.max_retries
        if should_retry:
            logger.warning(f"Retrying {message.tool_name} (attempt {message.retry_count + 1}/{message.max_retries})")
        else:
            logger.error(f"Max retries reached for {message.tool_name} ({message.max_retries} attempts)")
        
        return should_retry


@celery_app.task(bind=True)
def process_tool_execution_task(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task for processing tool execution messages.
    
    Args:
        self: Celery task instance
        message_data: Serialized tool execution message data
        
    Returns:
        Dict[str, Any]: Tool execution result
    """
    logger.info(f"🚀 Starting Celery task for tool execution")
    logger.debug(f"Task ID: {self.request.id}")
    logger.debug(f"Message data keys: {list(message_data.keys()) if message_data else 'None'}")
    
    consumer = ToolExecutionConsumer()
    
    # Try to set up dependencies if available
    # This would be better injected, but for now we'll handle missing dependencies gracefully
    try:
        logger.debug("Attempting to import tool_manager registry")
        from ...tools.registry import tool_registry
        # tool_registry is the global instance - no need to create a new one
        logger.debug("Tool registry imported successfully")
    except ImportError as e:
        logger.warning(f"Could not import tool registry: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error importing tool registry: {e}")
    
    try:
        logger.debug("Creating ToolExecutionMessage from data")
        message = ToolExecutionMessage.from_dict(message_data)
        logger.info(f"Processing tool: {message.tool_name} (Task: {message.task_id})")
    except Exception as e:
        logger.error(f"Failed to create message from data: {e}")
        logger.debug(f"Message data: {message_data}")
        raise
    
    try:
        logger.debug("Starting async event loop for tool execution")
        # Run async process method with proper cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run with a timeout to prevent hanging
            result = loop.run_until_complete(
                asyncio.wait_for(consumer.process(message), timeout=900.0)  # 15 minute timeout
            )
            logger.debug("Async tool execution completed")
            
            consumer.on_success(result, message)
            logger.info(f"🎉 Celery task completed successfully for {message.tool_name}")
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Tool execution timed out after 15 minutes for {message.tool_name}")
            error_result = {
                "task_id": message.task_id,
                "tool_name": message.tool_name,
                "status": "error",
                "error": "Tool execution timed out after 15 minutes",
                "agent_id": message.agent_id,
                "session_id": message.session_id,
                "context_data": message.context_data,
                "processed_at": message.created_at.isoformat()
            }
            return error_result
            
        finally:
            # Ensure proper cleanup of the event loop and any pending tasks
            try:
                # Cancel all remaining tasks
                pending_tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                if pending_tasks:
                    logger.debug(f"Cancelling {len(pending_tasks)} pending tasks")
                    for task in pending_tasks:
                        task.cancel()
                    
                    # Wait a bit for tasks to cancel gracefully
                    try:
                        loop.run_until_complete(asyncio.wait_for(
                            asyncio.gather(*pending_tasks, return_exceptions=True),
                            timeout=5.0
                        ))
                    except asyncio.TimeoutError:
                        logger.warning("Some tasks didn't cancel within timeout")
                
                # Close the loop properly
                loop.close()
                logger.debug("Event loop closed properly")
                
            except Exception as cleanup_error:
                logger.warning(f"Error during event loop cleanup: {cleanup_error}")
                # Force close the loop if needed
                if not loop.is_closed():
                    loop.close()
    except Exception as exc:
        logger.error(f"🔥 Celery task failed for {message.tool_name}: {exc}")
        consumer.on_failure(exc, message)
        
        if consumer.should_retry(exc, message):
            message.retry_count += 1
            retry_countdown = 2 ** message.retry_count
            logger.warning(f"⏰ Retrying task in {retry_countdown} seconds (attempt {message.retry_count}/{message.max_retries})")
            # Retry with exponential backoff
            raise self.retry(
                countdown=retry_countdown,
                max_retries=message.max_retries
            )
        logger.error(f"💀 Task failed permanently for {message.tool_name}")
        raise


def send_tool_execution_message(task_id: str,
                               tool_name: str,
                               tool_module: str,
                               tool_class: str,
                               tool_args: str,
                               tool_init_args: Dict[str, Any] = None,
                               context_data: Dict[str, Any] = None,
                               agent_id: str = None,
                               session_id: str = None,
                               team_data: Dict[str, Any] = None,
                               priority: int = 5) -> str:
    """Send a tool execution message to the queue.
    
    Args:
        task_id: Unique task identifier
        tool_name: Name of the tool to execute
        tool_module: Module path of the tool class
        tool_class: Class name of the tool
        tool_args: JSON string of tool execution arguments
        tool_init_args: Arguments for tool initialization
        context_data: Execution context data
        agent_id: ID of the agent that requested the tool
        session_id: Session ID for the tool execution
        team_data: Serialized team data for delegation tools
        priority: Task priority (1-10, lower is higher priority)
        
    Returns:
        str: Message ID
    """
    logger.info(f"📤 Sending tool execution message to queue")
    logger.info(f"   Tool: {tool_name}")
    logger.info(f"   Task ID: {task_id}")
    logger.info(f"   Agent: {agent_id or 'Unknown'}")
    logger.info(f"   Session: {session_id or 'Unknown'}")
    logger.debug(f"   Module: {tool_module}")
    logger.debug(f"   Class: {tool_class}")
    logger.debug(f"   Priority: {priority}")
    logger.debug(f"   Args: {tool_args}")
    logger.debug(f"   Init Args: {tool_init_args}")
    logger.debug(f"   Context: {context_data}")
    
    try:
        message = ToolExecutionMessage.create(
            task_id=task_id,
            tool_name=tool_name,
            tool_module=tool_module,
            tool_class=tool_class,
            tool_args=tool_args,
            tool_init_args=tool_init_args,
            context_data=context_data,
            agent_id=agent_id,
            session_id=session_id,
            team_data=team_data
        )
        
        # Set priority on message
        message.priority = priority
        logger.debug(f"Created message with ID: {message.message_id}")
        
        # Send to queue with priority
        logger.debug(f"Sending message to Celery queue with priority {priority}")
        
        # Debug: Try to serialize the message to identify circular references
        message_dict = message.to_dict()
        logger.debug(f"Message created successfully {message_dict}")
        
        try:
            import json
            # Attempt to serialize to identify circular references
            json_str = json.dumps(message_dict)
            logger.debug(f"Message serialization test passed, size: {len(json_str)} chars")
        except Exception as json_error:
            import json  # Ensure json is available for error handling
            logger.error(f"❌ JSON serialization test failed: {json_error}")
            logger.debug("Analyzing message structure for circular references...")
            
            # Debug each field separately
            for field_name, field_value in message_dict.items():
                try:
                    json.dumps(field_value)
                    logger.debug(f"✅ Field '{field_name}' serializes OK")
                except Exception as field_error:
                    logger.error(f"❌ Field '{field_name}' has circular reference: {field_error}")
                    logger.debug(f"Field '{field_name}' type: {type(field_value)}")
                    if isinstance(field_value, dict):
                        logger.debug(f"Field '{field_name}' keys: {list(field_value.keys())}")
            
            # Re-raise the original error
            raise json_error
        
        process_tool_execution_task.apply_async(
            args=[message_dict],
            priority=priority
        )
        
        logger.info(f"✅ Message sent to queue successfully (ID: {message.message_id})")
        return message.message_id
        
    except Exception as e:
        logger.error(f"❌ Failed to send tool execution message: {e}")
        logger.debug("Exception details:", exc_info=True)
        raise