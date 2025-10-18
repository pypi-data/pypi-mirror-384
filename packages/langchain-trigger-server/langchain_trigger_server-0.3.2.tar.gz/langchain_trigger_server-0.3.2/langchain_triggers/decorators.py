"""Trigger system - templates with registration and webhook handlers.

Also supports polling triggers (no HTTP route) via a `poll_handler` that the
framework scheduler can call on a cadence.
"""

from __future__ import annotations

import inspect
from typing import Any, get_type_hints

from langchain_auth.client import Client
from pydantic import BaseModel

from .core import TriggerHandlerResult, TriggerRegistrationResult, TriggerType


class TriggerTemplate:
    """A trigger template with registration handler and main handler."""

    def __init__(
        self,
        id: str,
        provider: str,
        name: str,
        description: str,
        registration_model: type[BaseModel],
        registration_handler,
        trigger_handler=None,
        *,
        trigger_type: TriggerType = TriggerType.WEBHOOK,
        poll_handler: Any | None = None,
        default_crontab: str | None = None,
    ):
        self.id = id
        self.provider = provider
        self.name = name
        self.description = description
        self.registration_model = registration_model
        self.registration_handler = registration_handler
        self.trigger_handler = trigger_handler
        self.trigger_type = trigger_type
        self.poll_handler = poll_handler
        self.default_crontab = default_crontab

        self._validate_handler_signatures()

    def _validate_handler_signatures(self):
        """Validate that all handler functions have the correct signatures."""
        # Expected reg: async def handler(user_id: str, auth_client: Client, registration: RegistrationModel) -> TriggerRegistrationResult
        self._validate_handler(
            "registration_handler",
            self.registration_handler,
            [str, Client, self.registration_model],
            TriggerRegistrationResult,
        )

        if self.trigger_type == TriggerType.WEBHOOK:
            if not self.trigger_handler:
                raise TypeError(
                    f"trigger_handler required for webhook trigger '{self.id}'"
                )
            self._validate_handler(
                "trigger_handler",
                self.trigger_handler,
                [dict[str, Any], dict[str, str], Any, Client],
                TriggerHandlerResult,
            )
        else:
            if not self.poll_handler:
                raise TypeError(
                    f"poll_handler required for polling trigger '{self.id}'"
                )
            self._validate_handler(
                "poll_handler",
                self.poll_handler,
                [dict[str, Any], Any, Client],
                TriggerHandlerResult,
            )

    def _validate_handler(
        self,
        handler_name: str,
        handler_func,
        expected_types: list[type],
        expected_return_type: type = None,
    ):
        """Common validation logic for all handler functions."""
        if not inspect.iscoroutinefunction(handler_func):
            raise TypeError(f"{handler_name} for trigger '{self.id}' must be async")

        sig = inspect.signature(handler_func)
        params = list(sig.parameters.values())
        expected_param_count = len(expected_types)

        if len(params) != expected_param_count:
            raise TypeError(
                f"{handler_name} for trigger '{self.id}' must have {expected_param_count} parameters, got {len(params)}"
            )

        hints = get_type_hints(handler_func)
        param_names = list(sig.parameters.keys())

        # Check each parameter type if type hints are available
        for i, expected_type in enumerate(expected_types):
            if param_names[i] in hints and hints[param_names[i]] != expected_type:
                expected_name = getattr(expected_type, "__name__", str(expected_type))
                raise TypeError(
                    f"{handler_name} for trigger '{self.id}': param {i + 1} should be {expected_name}"
                )

        # Check return type if expected and available
        if expected_return_type and "return" in hints:
            actual_return_type = hints["return"]
            if actual_return_type != expected_return_type:
                expected_name = getattr(
                    expected_return_type, "__name__", str(expected_return_type)
                )
                actual_name = getattr(
                    actual_return_type, "__name__", str(actual_return_type)
                )
                raise TypeError(
                    f"{handler_name} for trigger '{self.id}': return type should be {expected_name}, got {actual_name}"
                )
