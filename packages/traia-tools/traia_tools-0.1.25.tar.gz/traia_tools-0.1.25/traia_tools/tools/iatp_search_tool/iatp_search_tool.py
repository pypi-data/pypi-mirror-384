"""
CrewAI Tools for IATP Registry Search

Custom CrewAI tools that provide intelligent discovery and search capabilities 
for utility agents in the Inter Agent Transfer Protocol (IATP) ecosystem. These 
tools enable AI agents to find, search, and list available utility agents from 
the MongoDB registry using text search, semantic search, and filtering capabilities.

The tools support queries like 'find trading agents', 'list all active agents', 
or 'search for sentiment analysis tools'. They return detailed agent information 
including capabilities, endpoints, descriptions, and metadata to help agents 
discover and connect to the right utility services for their tasks.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

# CrewAI imports
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# IATP Registry imports from PyPI package
from traia_iatp.registry.iatp_search_api import (
    find_utility_agent,
    list_utility_agents, 
    search_utility_agents,
    UtilityAgentInfo
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('iatp_search_tool')

# Get environment settings
ENV = os.getenv("ENV", "test").lower()
logger.info(f"IATP Search Tools initialized with ENV={ENV}")


def utility_agent_to_dict(agent: UtilityAgentInfo) -> Dict[str, Any]:
    """
    Convert UtilityAgentInfo to dictionary for JSON serialization.
    
    Args:
        agent: UtilityAgentInfo object
        
    Returns:
        Dictionary representation of the utility agent
    """
    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "description": agent.description,
        "base_url": agent.base_url,
        "capabilities": agent.capabilities,
        "tags": agent.tags,
        "is_active": agent.is_active,
        "metadata": agent.metadata,
        "skills": agent.skills,
        "endpoints": agent.endpoints
    }


class KeywordSearchInput(BaseModel):
    """Input schema for keyword search tool."""
    query: str = Field(
        description="Search query text to find utility agents (e.g., 'trading agents', 'sentiment analysis', 'hyperliquid')"
    )


class KeywordSearchTool(BaseTool):
    """
    Tool for searching utility agents using keyword search.
    
    This performs text search across agent names, descriptions, tags, capabilities, 
    and skills to find the most relevant utility agent.
    """
    
    name: str = "search_utility_agents_keyword"
    description: str = (
        "Search for utility agents using keyword search. This performs text search "
        "across agent names, descriptions, tags, capabilities, and skills to find "
        "the most relevant utility agent. Use this when you need to find agents "
        "by specific terms or keywords."
    )
    args_schema: type[BaseModel] = KeywordSearchInput
    
    def _run(self, query: str) -> str:
        """Execute keyword search for utility agents."""
        try:
            logger.info(f"Performing keyword search for utility agents with query: {query}")
            
            # Use find_utility_agent with query parameter for text search
            agent = find_utility_agent(query=query)
            
            if agent:
                result = {
                    "status": "success",
                    "message": "Found utility agent matching query",
                    "indications": "if you are tasked with assigning a utility agent to a CrewAI agent, use the agent id",
                    "agent": utility_agent_to_dict(agent),
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "status": "success", 
                    "message": "No utility agent found matching query",
                    "agent": None,
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Keyword search completed: {result['status']}")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            error_result = {
                "status": "error",
                "message": f"Failed to search utility agents: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            return str(error_result)


class CapabilitiesTagsSearchInput(BaseModel):
    """Input schema for capabilities and tags search tool."""
    capabilities: Optional[List[str]] = Field(
        default=None,
        description="List of specific capabilities to search for (e.g., ['trading', 'api_calls'])"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="List of tags to search for (e.g., ['defi', 'hyperliquid', 'trading'])"
    )


class CapabilitiesTagsSearchTool(BaseTool):
    """
    Tool for searching utility agents by specific capabilities or tags.
    
    This allows precise filtering to find agents with exact capabilities 
    or categorization tags.
    """
    
    name: str = "search_utility_agents_capabilities_tags"
    description: str = (
        "Search for utility agents by specific capabilities or tags. This allows "
        "precise filtering to find agents with exact capabilities or categorization "
        "tags. Use this when you know the specific capabilities or categories you need."
    )
    args_schema: type[BaseModel] = CapabilitiesTagsSearchInput
    
    def _run(self, capabilities: Optional[List[str]] = None, tags: Optional[List[str]] = None) -> str:
        """Execute capabilities/tags search for utility agents."""
        try:
            if not capabilities and not tags:
                error_result = {
                    "status": "error",
                    "message": "At least one capability or tag must be provided",
                    "timestamp": datetime.now().isoformat()
                }
                return str(error_result)
            
            logger.info(f"Searching utility agents by capabilities: {capabilities}, tags: {tags}")
            
            # Use the first capability or tag for find_utility_agent
            capability = capabilities[0] if capabilities else None
            tag = tags[0] if tags else None
            
            agent = find_utility_agent(capability=capability, tag=tag)
            
            if agent:
                result = {
                    "status": "success",
                    "message": "Found utility agent matching criteria",
                    "indications": "if you are tasked with assigning a utility agent to a CrewAI agent, use the agent id",
                    "agent": utility_agent_to_dict(agent),
                    "search_criteria": {
                        "capabilities": capabilities,
                        "tags": tags
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                result = {
                    "status": "success",
                    "message": "No utility agent found matching criteria",
                    "agent": None,
                    "search_criteria": {
                        "capabilities": capabilities,
                        "tags": tags
                    },
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"Capabilities/tags search completed: {result['status']}")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in capabilities/tags search: {str(e)}")
            error_result = {
                "status": "error",
                "message": f"Failed to search utility agents by capabilities/tags: {str(e)}",
                "search_criteria": {
                    "capabilities": capabilities,
                    "tags": tags
                },
                "timestamp": datetime.now().isoformat()
            }
            return str(error_result)


class VectorSearchInput(BaseModel):
    """Input schema for vector search tool."""
    query: str = Field(
        description="Semantic search query (e.g., 'I need to execute cryptocurrency trades', 'find agents for market sentiment analysis')"
    )
    limit: int = Field(
        default=3,
        description="Maximum number of agents to return (default: 3, max: 3)"
    )


class VectorSearchTool(BaseTool):
    """
    Tool for searching utility agents using semantic vector search.
    
    This performs intelligent semantic matching to find agents based on meaning 
    and context, not just exact keyword matches.
    """
    
    name: str = "search_utility_agents_vector"
    description: str = (
        "Search for utility agents using semantic vector search. This performs "
        "intelligent semantic matching to find agents based on meaning and context, "
        "not just exact keyword matches. Use this when you need conceptual or "
        "semantic understanding of agent capabilities."
    )
    args_schema: type[BaseModel] = VectorSearchInput
    
    def _run(self, query: str, limit: int = 3) -> str:
        """Execute vector search for utility agents."""
        try:
            # Enforce maximum limit of 3
            if limit > 3:
                limit = 3
            
            logger.info(f"Performing vector search for utility agents with query: {query}, limit: {limit}")
            
            # Use search_utility_agents for vector/semantic search
            # Note: This is an async function, so we need to run it in an event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                agents = loop.run_until_complete(search_utility_agents(query=query, limit=limit))
            finally:
                loop.close()
            
            result = {
                "status": "success",
                "message": f"Found {len(agents)} utility agents using vector search",
                "indications": "if you are tasked with assigning a utility agent to a CrewAI agent, use the agent id",
                "agents": [utility_agent_to_dict(agent) for agent in agents],
                "query": query,
                "limit": limit,
                "count": len(agents),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Vector search completed: found {len(agents)} agents")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error in vector search: {str(e)}")
            error_result = {
                "status": "error",
                "message": f"Failed to perform vector search: {str(e)}",
                "query": query,
                "limit": limit,
                "timestamp": datetime.now().isoformat()
            }
            return str(error_result)


class ListAgentsInput(BaseModel):
    """Input schema for list agents tool."""
    limit: int = Field(
        default=10,
        description="Maximum number of agents to return (default: 10, max: 10)"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Optional list of tags to filter by (e.g., ['trading', 'defi'])"
    )
    capabilities: Optional[List[str]] = Field(
        default=None,
        description="Optional list of capabilities to filter by (e.g., ['api_calls', 'data_analysis'])"
    )
    active_only: bool = Field(
        default=True,
        description="Only return active agents (default: True)"
    )


class ListAgentsTool(BaseTool):
    """
    Tool for listing available utility agents from the IATP registry.
    
    This provides a comprehensive view of all available agents with optional filtering.
    """
    
    name: str = "list_utility_agents_registry"
    description: str = (
        "List available utility agents from the IATP registry. This provides "
        "a comprehensive view of all available agents with optional filtering. "
        "Use this when you want to see what agents are available or need to "
        "browse the registry."
    )
    args_schema: type[BaseModel] = ListAgentsInput
    
    def _run(
        self, 
        limit: int = 10, 
        tags: Optional[List[str]] = None, 
        capabilities: Optional[List[str]] = None, 
        active_only: bool = True
    ) -> str:
        """Execute list agents operation."""
        try:
            # Enforce maximum limit of 10
            if limit > 10:
                limit = 10
            
            logger.info(f"Listing utility agents: limit={limit}, tags={tags}, capabilities={capabilities}, active_only={active_only}")
            
            # Use list_utility_agents to get the list
            agents = list_utility_agents(
                limit=limit,
                tags=tags,
                capabilities=capabilities,
                active_only=active_only
            )
            
            result = {
                "status": "success",
                "message": f"Retrieved {len(agents)} utility agents from registry",
                "agents": [utility_agent_to_dict(agent) for agent in agents],
                "filters": {
                    "limit": limit,
                    "tags": tags,
                    "capabilities": capabilities,
                    "active_only": active_only
                },
                "count": len(agents),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"List agents completed: found {len(agents)} agents")
            return str(result)
            
        except Exception as e:
            logger.error(f"Error listing utility agents: {str(e)}")
            error_result = {
                "status": "error",
                "message": f"Failed to list utility agents: {str(e)}",
                "filters": {
                    "limit": limit,
                    "tags": tags,
                    "capabilities": capabilities,
                    "active_only": active_only
                },
                "timestamp": datetime.now().isoformat()
            }
            return str(error_result)


# Export all tools for easy import
def get_iatp_search_tools() -> List[BaseTool]:
    """
    Get all IATP registry search tools for use in CrewAI agents.
    
    Returns:
        List of configured IATP registry search tools
    """
    return [
        ListAgentsTool(),
        KeywordSearchTool(),
        CapabilitiesTagsSearchTool(),
        VectorSearchTool(),
    ]


# Individual tool exports for selective import
def get_keyword_search_tool() -> KeywordSearchTool:
    """Get the keyword search tool."""
    return KeywordSearchTool()


def get_vector_search_tool() -> VectorSearchTool:
    """Get the vector search tool."""
    return VectorSearchTool()


def get_capabilities_tags_search_tool() -> CapabilitiesTagsSearchTool:
    """Get the capabilities/tags search tool."""
    return CapabilitiesTagsSearchTool()


def get_list_agents_tool() -> ListAgentsTool:
    """Get the list agents tool."""
    return ListAgentsTool()


if __name__ == "__main__":
    """Test the IATP registry search tools."""
    print("🚀 Testing IATP Registry Search CrewAI Tools")
    print("=" * 60)
    
    # Check authentication setup
    cert_file = os.getenv("MONGODB_X509_CERT_FILE")
    if cert_file:
        print(f"✅ Using X.509 certificate: {cert_file}")
    else:
        print("❌ No MongoDB certificate configured")
        print("Please set MONGODB_X509_CERT_FILE environment variable to your certificate path")
        print("Example: export MONGODB_X509_CERT_FILE=/path/to/configs/mongodb/X509-cert-8436927887052476235.pem")
        exit(1)
    
    print()
    
    # Test each tool
    tools = get_iatp_search_tools()
    
    for tool in tools:
        print(f"🔧 Testing {tool.name}")
        print(f"   Description: {tool.description}")
        
        try:
            if tool.name == "search_utility_agents_keyword":
                result = tool._run(query="trading")
                print(f"   ✅ Test passed: {result[:100]}...")
                
            elif tool.name == "search_utility_agents_capabilities_tags":
                result = tool._run(capabilities=["trading"], tags=["defi"])
                print(f"   ✅ Test passed: {result[:100]}...")
                
            elif tool.name == "search_utility_agents_vector":
                result = tool._run(query="I need cryptocurrency trading tools", limit=2)
                print(f"   ✅ Test passed: {result[:100]}...")
                
            elif tool.name == "list_utility_agents_registry":
                result = tool._run(limit=3, active_only=True)
                print(f"   ✅ Test passed: {result[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Test failed: {str(e)}")
        
        print()
    
    print("🎉 All tests completed!")
    print("\nTo use these tools in your CrewAI agents:")
    print("```python")
    print("from traia_tools import get_iatp_search_tools")
    print()
    print("tools = get_iatp_search_tools()")
    print("agent = Agent(tools=tools, ...)")
    print("```")
