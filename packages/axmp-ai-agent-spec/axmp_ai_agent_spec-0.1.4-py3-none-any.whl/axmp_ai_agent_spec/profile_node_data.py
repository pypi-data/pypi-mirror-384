"""A profile of an AI agent."""

from __future__ import annotations

import re
from typing import Any

from croniter import croniter
from pydantic import BaseModel, Field, field_validator

from axmp_ai_agent_spec.types import (
    AgentMemoryType,
    TriggerType,
)


class ChatbotTriggerData(BaseModel):
    """Chatbot Trigger Node Data entity."""

    type: TriggerType = Field(
        default=TriggerType.CHATBOT, description="The type of the trigger node."
    )
    init_message: str | None = Field(
        None,
        description="The init message of the trigger node.",
        min_length=1,
        max_length=2000,
    )


class WebhookTriggerData(BaseModel):
    """Webhook Trigger Node Data entity."""

    type: TriggerType = Field(
        default=TriggerType.WEBHOOK, description="The type of the trigger node."
    )


class SchedulerTriggerData(BaseModel):
    """Scheduler Trigger Node Data entity."""

    type: TriggerType = Field(
        default=TriggerType.SCHEDULER, description="The type of the trigger node."
    )
    cron_expression: str = Field(
        ...,
        description="The cron expression of the trigger node.",
        min_length=1,
        max_length=255,
    )
    timezone: str | None = Field(
        None,
        description="The timezone of the trigger node.",
        min_length=1,
        max_length=255,
    )

    @field_validator("cron_expression")
    @classmethod
    def validate_cron_expression(cls, value: str) -> str:
        """Validate that the cron expression is valid using croniter.

        Args:
            value: The cron expression to validate.

        Returns:
            The validated cron expression.

        Raises:
            ValueError: If the cron expression is invalid.
        """
        try:
            croniter(value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid cron expression: {value}") from e
        return value


class AgentData(BaseModel):
    """Agent Node Data entity."""

    name: str = Field(
        ...,
        description="The name of the agent node.",
        min_length=1,
        max_length=255,
        pattern=r"^[a-zA-Z0-9 _-]+$",
    )
    system_prompt: str | None = Field(
        None,
        description="The system prompt of the agent node.",
        min_length=0,
        # NOTE: No max length for system prompt
        # max_length=2000,
    )

    @field_validator("system_prompt")
    @classmethod
    def validate_system_prompt_content(cls, value: str | None) -> str | None:
        """Validate system prompt content for potentially dangerous patterns.

        Args:
            value: The system prompt content to validate.

        Returns:
            The validated system prompt content.

        Raises:
            ValueError: If the system prompt contains potentially dangerous content.
        """
        if value is None or value == "":
            return value

        # Patterns that could indicate potentially dangerous content
        dangerous_patterns = [
            # Code injection attempts - use with parentheses
            r"(?i)\b(?:exec|eval|compile|__import__|getattr|setattr|delattr|globals|locals|vars|dir)\s*\(",
            # File system operations - more specific patterns
            r"(?i)\b(?:os\.system|subprocess\.(?:run|call|check_output|popen)|shutil\.(?:rmtree|move|copy))\s*\(",
            r'(?i)\bopen\s*\(\s*["\'][^"\']*["\'][^)]*["\']w["\']',  # open() with write mode
            # Network operations with method calls
            r"(?i)\b(?:requests\.(?:get|post|put|delete)|urllib\.request\.urlopen|socket\.socket)\s*\(",
            # System commands
            r'(?i)\b(?:system|shell|bash|cmd|powershell)\s*\([^)]*["\'][^"\']*["\'][^)]*\)',
            # Database operations - actual SQL commands
            r"(?i)\b(?:select\s+.*\s+from|insert\s+into|update\s+.*\s+set|delete\s+from|drop\s+table|create\s+table)\s+",
            # Credential assignments - actual assignments
            r'(?i)\b(?:password|passwd|secret|token|key|credential|api_key|access_key)\s*[:=]\s*["\'][a-zA-Z0-9_-]{3,}["\']',
            # Script tags and HTML/JS injection
            r"(?i)<\s*script\b[^>]*>.*</script>",
            r'(?i)\bon(?:click|load|error|focus|blur)\s*=\s*["\'][^"\']*["\']',
            # Environment variables access with brackets
            r'(?i)\b(?:getenv\s*\(\s*["\']|os\.environ\s*\[\s*["\'])[^"\']+["\']\s*[\]\)]',
            # Process manipulation with parentheses
            r"(?i)\b(?:kill|signal|fork|spawn)\s*\([^)]*\)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value):
                raise ValueError(
                    f"System prompt contains potentially dangerous content. "
                    f"Pattern matched: {pattern}"
                )

        return value


class LLMModelData(BaseModel):
    """LLM Node Data entity."""

    provider: str = Field(
        ..., description="The provider of the LLM node.", min_length=1, max_length=255
    )
    base_url: str | None = Field(
        None,
        description="The base url of the LLM node.",
        min_length=1,
        max_length=255,
    )
    default_model_id: str | None = Field(
        None,
        description="The default model of the LLM node.",
        min_length=1,
        max_length=255,
    )
    temperature: float = Field(
        None,
        description="The temperature of the LLM node.",
        ge=0,
        le=1,
    )
    max_tokens: int = Field(
        5000,
        description="The max tokens of the LLM node.",
        ge=5000,
        # NOTE: TBD max length for max tokens
        le=1000000,
    )
    api_key: str = Field(
        ...,
        description="The API key of the LLM node.",
        min_length=1,
        max_length=255,
    )


class AgentMemoryData(BaseModel):
    """Agent Memory Data entity."""

    memory_type: AgentMemoryType = Field(
        ..., description="The type of the memory node."
    )
    db_uri: str = Field(..., description="The DB URI of the memory node.")


class McpServerData(BaseModel):
    """MCP Server entity."""

    config: dict[str, Any] = Field(
        ...,
        description="The config of the external MCP server node.",
    )


class A2ARemoteAgentData(BaseModel):
    """Remote Agent Node Data entity."""

    name: str = Field(
        ...,
        description="The name of the remote agent node.",
        min_length=1,
        max_length=255,
    )
    agent_card_url: str = Field(
        ...,
        description="The agent card url of the remote agent node.",
        min_length=1,
        max_length=255,
    )
    # TODO: Add the data for the remote agent node
