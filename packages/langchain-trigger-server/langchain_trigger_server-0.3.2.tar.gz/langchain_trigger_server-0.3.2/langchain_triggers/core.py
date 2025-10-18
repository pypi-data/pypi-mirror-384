"""Core types and interfaces for the triggers framework."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    """Type of trigger supported by the framework."""

    WEBHOOK = "webhook"
    POLLING = "polling"


class ProviderAuthInfo(BaseModel):
    """Authentication info for a specific OAuth provider."""

    token: str | None = None
    auth_required: bool = False
    auth_url: str | None = None
    auth_id: str | None = None


class UserAuthInfo(BaseModel):
    """User authentication info containing OAuth tokens or auth requirements."""

    user_id: str
    providers: dict[str, ProviderAuthInfo] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True


class AgentInvocationRequest(BaseModel):
    """Request to invoke an AI agent."""

    assistant_id: str
    user_id: str
    input_data: Any
    thread_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TriggerHandlerResult(BaseModel):
    """Result returned by trigger handlers."""

    invoke_agent: bool = Field(
        default=True, description="Whether to invoke agents for this event"
    )
    agent_messages: list[str] | None = Field(
        default=None,
        description="List of messages to send to agents (one invocation per message)",
    )
    response_body: dict[str, Any] | None = Field(
        default=None, description="Custom HTTP response body (when invoke_agent=False)"
    )
    registration: dict[str, Any] | None = Field(
        default=None, description="Registration data (required when invoke_agent=True)"
    )

    def model_post_init(self, __context) -> None:
        """Validate that required fields are provided based on invoke_agent."""
        if self.invoke_agent and not self.agent_messages:
            raise ValueError("agent_messages is required when invoke_agent=True")
        if self.invoke_agent and not self.registration:
            raise ValueError("registration is required when invoke_agent=True")
        if not self.invoke_agent and not self.response_body:
            raise ValueError("response_body is required when invoke_agent=False")


class TriggerRegistrationResult(BaseModel):
    """Result returned by registration handlers."""

    create_registration: bool = Field(
        default=True,
        description="Whether to create database registration (False = return custom response)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata to store with the registration"
    )
    response_body: dict[str, Any] | None = Field(
        default=None,
        description="Custom HTTP response body (when create_registration=False)",
    )
    status_code: int | None = Field(
        default=None, description="HTTP status code (when create_registration=False)"
    )

    def model_post_init(self, __context) -> None:
        """Validate that required fields are provided based on create_registration."""
        if self.create_registration and not self.metadata:
            self.metadata = {}  # Allow empty metadata for create_registration=True

        if "client_metadata" in self.metadata:
            raise ValueError(
                "The 'client_metadata' key is reserved for client-provided metadata. "
                "Registration handlers must not use this key in their metadata."
            )

        if not self.create_registration and (
            not self.response_body or not self.status_code
        ):
            raise ValueError(
                "Both response_body and status_code are required when create_registration=False"
            )


class TriggerRegistrationModel(BaseModel):
    """Base class for trigger resource models that define how webhooks are matched to registrations."""

    pass
