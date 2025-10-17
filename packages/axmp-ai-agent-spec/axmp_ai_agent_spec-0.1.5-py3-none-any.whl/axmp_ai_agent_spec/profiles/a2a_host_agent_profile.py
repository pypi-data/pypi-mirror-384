"""A profile of an AI agent."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from axmp_ai_agent_spec.profile_base import BaseFlow, BaseNode, BaseProfile
from axmp_ai_agent_spec.profile_node_data import (
    A2ARemoteAgentData,
    AgentData,
    AgentMemoryData,
    ChatbotTriggerData,
    LLMModelData,
    SchedulerTriggerData,
    WebhookTriggerData,
)
from axmp_ai_agent_spec.types import NodeType


class NodeOfA2AHostAgent(BaseNode):
    """Node Entity. This entity is used to store the node of the A2A host agent."""

    data: (
        ChatbotTriggerData
        | WebhookTriggerData
        | SchedulerTriggerData
        | AgentData
        | LLMModelData
        | AgentMemoryData
        | A2ARemoteAgentData
        | None
    ) = None

    @model_validator(mode="after")
    def validate_node_data(self) -> Any:
        """Validate the node data."""
        if self.type is None:
            raise ValueError("Type must be set.")

        if self.data is None:
            return self
        if (
            isinstance(self.data, ChatbotTriggerData)
            or isinstance(self.data, WebhookTriggerData)
            or isinstance(self.data, SchedulerTriggerData)
        ):
            if self.type != NodeType.TRIGGER:
                raise ValueError("Type must be TRIGGER.")
        elif isinstance(self.data, AgentData):
            if self.type != NodeType.AI_AGENT:
                raise ValueError("Type must be AI_AGENT.")
        elif isinstance(self.data, LLMModelData):
            if self.type != NodeType.LLM:
                raise ValueError("Type must be LLM.")
        elif isinstance(self.data, AgentMemoryData):
            if self.type != NodeType.MEMORY:
                raise ValueError("Type must be MEMORY.")
        elif isinstance(self.data, A2ARemoteAgentData):
            if self.type != NodeType.REMOTE_AGENT:
                raise ValueError("Type must be REMOTE_AGENT.")
        return self


class A2AHostAgentFlow(BaseFlow):
    """A flow of an AI agent."""

    nodes: list[NodeOfA2AHostAgent] | None = Field(
        None,
        description="The nodes of the flow.",
    )


class A2AHostAgentProfile(BaseProfile):
    """A profile of an AI agent."""

    # NOTE: Override the nodes of the BaseProfile
    flow: A2AHostAgentFlow | None = None

    @model_validator(mode="after")
    def validate_root_node(self) -> A2AHostAgentProfile:
        """Validate that only AI_AGENT type node can be root node.

        If there is a non-AI_AGENT type node with root_node=True, raise validation error.
        """
        if not self.flow.nodes:
            return self

        root_node_count = 0
        trigger_node_count = 0
        llm_node_count = 0
        memory_node_count = 0

        for node in self.flow.nodes:
            if node.type != NodeType.AI_AGENT and node.root_node:
                raise ValueError(
                    f"Only AI_AGENT type node can be root node. Found {node.type} type node with root_node=True"
                )

            if node.type == NodeType.AI_AGENT and not node.root_node:
                raise ValueError(
                    f"AI_AGENT type node must be root node. Found {node.type} type node with root_node=False"
                )

            if node.type == NodeType.AI_AGENT and node.root_node:
                root_node_count += 1

                if root_node_count > 1:
                    raise ValueError(
                        f"Only one AI_AGENT type node can be root node. Found {root_node_count} AI_AGENT type nodes with root_node=True"
                    )

            if node.type == NodeType.TRIGGER:
                trigger_node_count += 1
                if trigger_node_count > 1:
                    raise ValueError(
                        f"Only one TRIGGER type node can be root node. Found {trigger_node_count} TRIGGER type nodes with root_node=True"
                    )

            if node.type == NodeType.LLM:
                llm_node_count += 1
                if llm_node_count > 1:
                    raise ValueError(
                        f"Only one LLM type node can be root node. Found {llm_node_count} LLM type nodes with root_node=True"
                    )

            if node.type == NodeType.MEMORY:
                memory_node_count += 1
                if memory_node_count > 1:
                    raise ValueError(
                        f"Only one MEMORY type node can be root node. Found {memory_node_count} MEMORY type nodes with root_node=True"
                    )

        return self
