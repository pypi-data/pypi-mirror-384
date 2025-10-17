"""A profile of an AI agent."""

from __future__ import annotations

from enum import Enum


class ProfileType(str, Enum):
    """AgentProfileType Entity. This entity is used to store the type of the agent profile."""

    SINGLE_AGENT = "single-agent"
    A2A_HOST_AGENT = "a2a-host-agent"
    WORKFLOW = "workflow"


class ProfileStatus(str, Enum):
    """ProfileStatus Entity. This entity is used to store the status of the profile."""

    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"


class RuntimeType(str, Enum):
    """AgentRuntimeType Entity. This entity is used to store the type of the agent runtime."""

    WORKSPACE = "workspace"
    STANDALONE = "standalone"


class DeploymentMode(str, Enum):
    """AgeDeploymentMode Entity. This entity is used to store the deployment mode of the agent."""

    # IN_MEMORY_AGENT = "in-memory-agent"
    BACKEND_SERVER = "backend-server"
    A2A_REMOTE_AGENT = "a2a-remote-agent"


class UsageType(str, Enum):
    """UsageType Entity. This entity is used to store the usage type of the agent."""

    PERSONAL = "personal"
    BUSINESS = "business"


class MCPServerType(str, Enum):
    """MCPServerType Entity. This entity is used to store the type of the MCP server."""

    INTERNAL = "internal"
    EXTERNAL = "external"


class NodeType(str, Enum):
    """AgentProfileNodeType Entity. This entity is used to store the type of the node."""

    TRIGGER = "trigger"
    AI_AGENT = "ai-agent"
    LLM = "llm"
    MEMORY = "memory"
    MCP_SERVER = "mcp-server"
    REMOTE_AGENT = "remote-agent"


class TriggerType(str, Enum):
    """TriggerType Entity. This entity is used to store the type of the trigger."""

    # WORKSPACE = "workspace"
    CHATBOT = "chatbot"
    WEBHOOK = "webhook"
    SCHEDULER = "scheduler"
    # TODO: milestone 2
    # A2A_HOST_AGENT = "a2a-host-agent"


class DomainType(str, Enum):
    """DomainType Entity. This entity is used to store the type of the domain."""

    SYSTEM = "system"  ## TODO:Clearly specify the meaning of the system domain
    CUSTOM = "custom"


class AuthenticationType(str, Enum):
    """Authentication Type entity."""

    NONE = "None"
    BASIC = "Basic"
    BEARER = "Bearer"
    API_KEY = "ApiKey"
    IDP = "IdentityProvider"


class TransportType(str, Enum):
    """Transport type for MCP and Gateway."""

    STDIO = "stdio"
    STREAMABLE_HTTP = "streamable-http"


class AgentMemoryType(str, Enum):
    """Chat memory type."""

    POSTGRES = "POSTGRESQL"
    REDIS = "REDIS"
