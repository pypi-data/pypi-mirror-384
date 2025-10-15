"""A profile of an AI agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from axmp_ai_agent_spec.types import (
    AuthenticationType,
    DeploymentMode,
    DomainType,
    NodeType,
    RuntimeType,
)


class OpenIDConnectProvider(BaseModel):
    """OpenID Connect Provider Config entity."""

    issuer: str = Field(
        ..., description="The issuer of the OpenID Connect provider config."
    )
    client_id: str = Field(
        ..., description="The client id of the OpenID Connect provider config."
    )
    client_secret: str = Field(
        ..., description="The client secret of the OpenID Connect provider config."
    )
    redirect_uri: str = Field(
        ..., description="The redirect uri of the OpenID Connect provider config."
    )
    scope: str = Field(
        "openid profile email",
        description="The scope of the OpenID Connect provider config.",
    )
    algorithm: str = Field(
        "RS256", description="The algorithm of the OpenID Connect provider config."
    )
    jwks_uri: str = Field(
        ..., description="The jwks uri of the OpenID Connect provider config."
    )
    authorization_endpoint: str = Field(
        ...,
        description="The authorization endpoint of the OpenID Connect provider config.",
    )
    token_endpoint: str = Field(
        ..., description="The token endpoint of the OpenID Connect provider config."
    )
    userinfo_endpoint: str = Field(
        ..., description="The userinfo endpoint of the OpenID Connect provider config."
    )
    introspection_endpoint: str | None = Field(
        None,
        description="The introspection endpoint of the OpenID Connect provider config.",
    )
    end_session_endpoint: str | None = Field(
        None,
        description="The end session endpoint of the OpenID Connect provider config.",
    )
    registration_endpoint: str | None = Field(
        None,
        description="The registration endpoint of the OpenID Connect provider config.",
    )
    grant_types: str = Field(
        "authorization_code",
        description="The grant types of the OpenID Connect provider config.",
    )
    response_types: str = Field(
        "code", description="The response types of the OpenID Connect provider config."
    )
    subject_types: str = Field(
        "public", description="The subject types of the OpenID Connect provider config."
    )


class AuthenticationConfig(BaseModel):
    """Authentication Config entity."""

    type: AuthenticationType = AuthenticationType.NONE
    identity_provider: OpenIDConnectProvider | None = Field(
        None,
        description="The identity provider of the authentication config.",
    )
    username: str | None = Field(
        None,
        description="The username of the authentication config.",
        min_length=1,
        max_length=255,
    )
    password: str | None = Field(
        None,
        description="The password of the authentication config.",
        min_length=1,
        max_length=255,
    )
    api_key_name: str | None = Field(
        None,
        description="The api key name of the authentication config.",
        min_length=1,
        max_length=255,
    )
    api_key_value: str | None = Field(
        None,
        description="The api key value of the authentication config.",
        min_length=1,
        max_length=1024,
    )
    bearer_token: str | None = Field(
        None,
        description="The bearer token of the authentication config.",
        min_length=1,
        max_length=4096,
    )


class EndpointConfig(BaseModel):
    """Endpoint Config entity."""

    domain_type: DomainType = Field(
        DomainType.SYSTEM, description="The type of the domain."
    )
    sub_domain_name: str | None = Field(
        None,
        description="The sub domain name of the domain.",
        min_length=1,
        max_length=30,
    )
    full_domain_name: str | None = Field(
        None,
        description="The name of the domain.",
        min_length=1,
        max_length=255,
    )
    tls_secret: str | None = Field(
        None,
        description="The TLS secret of the endpoint config.",
        min_length=1,
        max_length=255,
    )
    webhook_path: str | None = Field(
        None,
        description="The webhook path of the endpoint config.",
        min_length=1,
        max_length=255,
    )


class BaseNode(BaseModel):
    """Node Entity. This entity is used to store the node of the reactflow."""

    id: str | None = Field(
        None,
        description="The id of the node.",
    )
    type: NodeType | None = Field(
        None,
        description="The type of the node.",
    )
    root_node: bool = Field(
        False,
        description="Whether the node is a root node.",
    )
    data: Any | None = Field(
        None,
        description="The data of the node.",
    )
    """
    The data should be defined in the subclass.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )


class BaseEdge(BaseModel):
    """Edge Entity. This entity is used to store the edge of the reactflow."""

    id: str | None = Field(
        None,
        description="The id of the edge.",
    )
    type: str | None = Field(
        None,
        description="The type of the edge.",
    )
    source: str | None = Field(
        None,
        description="The source of the edge.",
    )
    target: str | None = Field(
        None,
        description="The target of the edge.",
    )


class BaseFlow(BaseModel):
    """A flow of an AI agent."""

    nodes: list[BaseNode] | None = Field(
        None,
        description="The nodes of the profile.",
    )
    edges: list[BaseEdge] | None = Field(
        None,
        description="The edges of the profile.",
    )


class BaseProfile(ABC, BaseModel):
    """A profile of an AI agent."""

    id: str | None = Field(
        None,
        description="The id of the profile.",
    )
    version: int | None = Field(
        None,
        description="The version of the agent profile.",
    )
    name: str | None = Field(
        None,
        description="The name of the profile.",
    )
    system_name: str | None = Field(
        None,
        description="The system name of the agent profile.",
    )
    runtime_type: RuntimeType | None = Field(
        None,
        description="The runtime type of the agent profile.",
    )
    deployment_mode: DeploymentMode | None = Field(
        None,
        description="The deployment mode of the agent profile.",
    )
    auth_config: AuthenticationConfig | None = Field(
        None,
        description="The authentication config of the agent profile.",
    )
    endpoint_config: EndpointConfig | None = Field(
        None,
        description="The endpoint config of the agent profile.",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        extra="forbid",
    )

    @abstractmethod
    def validate_root_node(self) -> BaseProfile:
        """Validate the root node of the profile."""
        pass
