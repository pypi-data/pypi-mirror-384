"""AXMP AI Agent Specification Package.

This package provides a comprehensive specification system for defining AI agent
configurations using a node-based flow architecture. It uses Pydantic for data
validation and modeling to ensure type safety and validation of agent specifications.

The package supports various node types including:
- Trigger nodes (Chatbot, Webhook, Scheduler)
- AI Agent nodes with system prompts and configurations
- LLM nodes for language model configurations
- Memory nodes for different backend storage types
- MCP Server nodes for both internal and external servers

Key Components:
- BaseProfile: Abstract base for agent profiles
- SingleAgentProfile: Concrete implementation for single-agent flows
- A2AHostAgentProfile: Concrete implementation for A2A host agent flows
- WorkflowAgentProfile: Concrete implementation for workflow agent flows
- BaseNode/NodeOfSingleAgent/NodeOfA2AHostAgent/NodeOfWorkflowAgent: Node entities with typed data payloads
- BaseEdge: Edge entities connecting nodes in the flow

Example:
    >>> from axmp_ai_agent_spec import SingleAgentProfile, NodeOfSingleAgent
    >>> from axmp_ai_agent_spec.types import NodeType
    >>>
    >>> # Create a simple agent profile
    >>> profile = SingleAgentProfile(id="my-agent", name="My Agent", nodes=[], edges=[])
"""

from axmp_ai_agent_spec.profile_base import (
    AuthenticationConfig,
    BaseEdge,
    BaseNode,
    BaseProfile,
    EndpointConfig,
)
from axmp_ai_agent_spec.profile_node_data import (
    A2ARemoteAgentData,
    AgentData,
    AgentMemoryData,
    ChatbotTriggerData,
    LLMModelData,
    McpServerData,
    SchedulerTriggerData,
    WebhookTriggerData,
)
from axmp_ai_agent_spec.profiles.a2a_host_agent_profile import (
    A2AHostAgentProfile,
    NodeOfA2AHostAgent,
)
from axmp_ai_agent_spec.profiles.single_agent_profile import (
    NodeOfSingleAgent,
    SingleAgentProfile,
)
from axmp_ai_agent_spec.profiles.workflow_agent_profile import (
    NodeOfWorkflowAgent,
    WorkflowAgentProfile,
)
from axmp_ai_agent_spec.types import (
    AgentMemoryType,
    DomainType,
    MCPServerType,
    NodeType,
    ProfileStatus,
    TriggerType,
)

__version__ = "0.1.0"
__author__ = "Kilsoo Kang"
__email__ = "kilsoo75@gmail.com"

__all__ = [
    # Base classes
    "BaseNode",
    "BaseEdge",
    "BaseProfile",
    "AuthenticationConfig",
    "EndpointConfig",
    # Single agent classes
    "NodeOfSingleAgent",
    "SingleAgentProfile",
    # A2A Host agent classes
    "NodeOfA2AHostAgent",
    "A2AHostAgentProfile",
    # Workflow agent classes
    "NodeOfWorkflowAgent",
    "WorkflowAgentProfile",
    # Node data classes
    "AgentData",
    "ChatbotTriggerData",
    "WebhookTriggerData",
    "SchedulerTriggerData",
    "LLMModelData",
    "AgentMemoryData",
    "McpServerData",
    "A2ARemoteAgentData",
    # Enums and types
    "NodeType",
    "TriggerType",
    "AgentMemoryType",
    "MCPServerType",
    "DomainType",
    "ProfileStatus",
]
