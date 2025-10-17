"""A profile of an AI agent."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from axmp_ai_agent_spec.profile_base import BaseFlow, BaseNode, BaseProfile
from axmp_ai_agent_spec.profile_node_data import (
    AgentData,
    AgentMemoryData,
    ChatbotTriggerData,
    LLMModelData,
    McpServerData,
    SchedulerTriggerData,
    WebhookTriggerData,
)
from axmp_ai_agent_spec.types import NodeType


class NodeOfWorkflowAgent(BaseNode):
    """Node Entity. This entity is used to store the node of the workflow agent."""

    data: (
        ChatbotTriggerData
        | WebhookTriggerData
        | SchedulerTriggerData
        | AgentData
        | LLMModelData
        | AgentMemoryData
        | McpServerData
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
        elif isinstance(self.data, McpServerData):
            if self.type != NodeType.MCP_SERVER:
                raise ValueError("Type must be MCP_SERVER.")
        return self


class WorkflowAgentFlow(BaseFlow):
    """A flow of an AI agent."""

    nodes: list[NodeOfWorkflowAgent] | None = Field(
        None,
        description="The nodes of the flow.",
    )


class WorkflowAgentProfile(BaseProfile):
    """A profile of an AI agent."""

    # NOTE: Override the nodes of the BaseProfile
    flow: WorkflowAgentFlow | None = None

    @model_validator(mode="after")
    def validate_root_node(self) -> WorkflowAgentProfile:
        """Validate that only AI_AGENT type node can be root node.

        If there is a non-AI_AGENT type node with root_node=True, raise validation error.
        """
        if not self.flow.nodes:
            return self

        root_node_count = 0
        for node in self.flow.nodes:
            if node.type != NodeType.AI_AGENT and node.root_node:
                raise ValueError(
                    f"Only AI_AGENT type node can be root node. Found {node.type} type node with root_node=True"
                )

            # NOTE: for the multi-agent flow, the AI_AGENT type node can be root node or not
            # if node.type == AgentProfileNodeType.AI_AGENT and not node.root_node:
            #     raise ValueError(
            #         f"AI_AGENT type node must be root node. Found {node.type} type node with root_node=False"
            #     )

            # if node.type == AgentProfileNodeType.AI_AGENT and node.root_node:
            #     root_node_count += 1

            if node.root_node:
                root_node_count += 1

        if root_node_count > 1:
            raise ValueError(
                f"Only one AI_AGENT type node can be root node. Found {root_node_count} AI_AGENT type nodes with root_node=True"
            )

        return self
