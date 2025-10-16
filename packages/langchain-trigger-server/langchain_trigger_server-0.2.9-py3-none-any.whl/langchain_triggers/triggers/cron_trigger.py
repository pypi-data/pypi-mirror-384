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


async def cron_trigger_handler(
    payload: dict[str, Any],
    query_params: dict[str, str],
    database,
    auth_client: Client,
) -> TriggerHandlerResult:
    """Cron trigger handler - this should never be called via HTTP."""
    logger.warning("Cron trigger handler called via HTTP - this shouldn't happen")
    return TriggerHandlerResult(
        invoke_agent=False,
        response_body={
            "success": False,
            "message": "Cron triggers are executed by scheduler, not HTTP requests",
        },
    )


cron_trigger = TriggerTemplate(
    id=CRON_TRIGGER_ID,
    name="Cron Scheduler",
    provider="Cron",
    description="Triggers agents on a cron schedule",
    registration_model=CronRegistration,
    registration_handler=cron_registration_handler,
    trigger_handler=cron_trigger_handler,
)
