"""Cron-based trigger for scheduled agent execution."""

import logging
from datetime import datetime
from typing import Any

from croniter import croniter
from langchain_auth.client import Client
from pydantic import Field

from langchain_triggers.core import (
    TriggerHandlerResult,
    TriggerRegistrationModel,
    TriggerRegistrationResult,
    TriggerType,
)
from langchain_triggers.decorators import TriggerTemplate

logger = logging.getLogger(__name__)

# Global constant for cron trigger ID (UUID format to match database schema)
CRON_TRIGGER_ID = "c809e66e-0000-4000-8000-000000000001"


class CronRegistration(TriggerRegistrationModel):
    """Registration model for cron triggers - just a crontab pattern."""

    crontab: str = Field(
        ...,
        description="Cron pattern (e.g., '0 9 * * MON-FRI', '*/15 * * * *')",
        examples=["0 9 * * MON-FRI", "*/15 * * * *", "0 2 * * SUN"],
    )


async def cron_registration_handler(
    user_id: str, auth_client: Client, registration: CronRegistration
) -> TriggerRegistrationResult:
    """Handle cron trigger registration - validates cron pattern and prepares for scheduling."""
    logger.info(f"Cron registration request: {registration}")

    cron_pattern = registration.crontab.strip()

    # Validate cron pattern
    try:
        if not croniter.is_valid(cron_pattern):
            return TriggerRegistrationResult(
                create_registration=False,
                response_body={
                    "success": False,
                    "error": "invalid_cron_pattern",
                    "message": f"Invalid cron pattern: '{cron_pattern}'",
                },
                status_code=400,
            )
    except Exception as e:
        return TriggerRegistrationResult(
            create_registration=False,
            response_body={
                "success": False,
                "error": "cron_validation_failed",
                "message": f"Failed to validate cron pattern: {str(e)}",
            },
            status_code=400,
        )

    logger.info(f"Successfully validated cron pattern: {cron_pattern}")
    return TriggerRegistrationResult(
        metadata={
            "cron_pattern": cron_pattern,
            "timezone": "UTC",
            "created_at": datetime.utcnow().isoformat(),
            "validated": True,
        }
    )


async def cron_poll_handler(
    registration: dict[str, Any],
    database,
    auth_client: Client,
) -> TriggerHandlerResult:
    """Polling handler for generic cron.

    Produces a simple time-based message for linked agents.
    """
    current_time = datetime.utcnow()
    current_time_str = current_time.strftime("%A, %B %d, %Y at %H:%M UTC")
    message = (
        "ACTION: triggering cron from langchain-trigger-server\n"
        f"CURRENT TIME: {current_time_str}"
    )
    return TriggerHandlerResult(
        invoke_agent=True,
        agent_messages=[message],
        registration=registration,
    )


cron_trigger = TriggerTemplate(
    id=CRON_TRIGGER_ID,
    name="Cron Scheduler",
    provider="Cron",
    description="Triggers agents on a cron schedule",
    registration_model=CronRegistration,
    registration_handler=cron_registration_handler,
    trigger_type=TriggerType.POLLING,
    poll_handler=cron_poll_handler,
)
