"""
OpenAI Knowledge Query Tool - Using OpenAI Agents SDK FunctionTool class
"""

import logging
import asyncio
from typing import Any
from pydantic import BaseModel, Field
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import SyncTool


class KnowledgeQueryArgs(BaseModel):
    """Arguments for the knowledge query tool."""
    query: str = Field(..., description="The search query to find relevant information in the knowledge base")
    knowledge_name: str = Field(..., description="The name of the knowledge base to query")


class KnowledgeQueryTool(SyncTool):
    """Configurable Knowledge Query Tool that can be used in YAML configurations."""
    
    def __init__(self, knowledge_manager=None):
        """Initialize the knowledge query tool.
        
        Args:
            knowledge_manager: Knowledge manager instance
        """
        # Call parent constructor first
        super().__init__(
            name="knowledge_query",
            description="Query a knowledge base for relevant information",
            input_schema=KnowledgeQueryArgs
        )
        
        self.knowledge_manager = knowledge_manager
        
        # Setup logger
        self.logger = logging.getLogger(__name__)
        
        # Create the FunctionTool
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=KnowledgeQueryArgs.model_json_schema(),
            on_invoke_tool=self._run_knowledge_query
        )
    
    def set_knowledge_manager(self, knowledge_manager):
        """Set the knowledge manager reference."""
        self.knowledge_manager = knowledge_manager
        
    async def _run_knowledge_query(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """
        Query a knowledge base for relevant information.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing KnowledgeQueryArgs
            
        Returns:
            Knowledge query result as string
        """
        parsed_args = None
        try:
            # Parse arguments
            parsed_args = KnowledgeQueryArgs.model_validate_json(args)
            
            if not self.knowledge_manager:
                return "Error: Knowledge manager not available"
            
            self.logger.info(f"🔍 KNOWLEDGE QUERY STARTED - Query: '{parsed_args.query}' | Knowledge Base: '{parsed_args.knowledge_name}'")
            
            # Check if knowledge base exists
            try:
                available_bases = self.knowledge_manager.list_knowledge_bases()
                if not isinstance(available_bases, list):
                    self.logger.error(f"list_knowledge_bases() returned {type(available_bases)} instead of list")
                    available_bases = []
            except Exception as e:
                self.logger.error(f"Error getting knowledge bases: {e}")
                available_bases = []
            
            if parsed_args.knowledge_name not in available_bases:
                available_bases_str = ', '.join(available_bases) if available_bases else 'None'
                return f"Error: Knowledge base '{parsed_args.knowledge_name}' not found. Available bases: {available_bases_str}"
            
            # Perform the query (async method)
            results = await self.knowledge_manager.query_knowledge_base(
                parsed_args.knowledge_name, 
                parsed_args.query
            )
            
            # Extract content from results
            if results:
                result = "\n\n".join([kr.content for kr in results])
            else:
                result = "No relevant information found."
            
            # Log successful result
            result_preview = result[:400] + "..." if len(result) > 400 else result
            self.logger.info(f"✅ KNOWLEDGE QUERY SUCCESSFUL - Retrieved {len(result)} characters")
            self.logger.info(f"📄 Result preview: {result_preview}")
            
            return result
            
        except Exception as e:
            knowledge_name = parsed_args.knowledge_name if parsed_args else 'unknown'
            error_msg = f"Failed to query knowledge base '{knowledge_name}': {str(e)}"
            self.logger.error(f"❌ KNOWLEDGE QUERY FAILED - {error_msg}")
            return error_msg
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance.
        
        Returns:
            FunctionTool instance
        """
        return self.tool


# No global variables needed - use direct instantiation or tool_manager for dynamic loading
