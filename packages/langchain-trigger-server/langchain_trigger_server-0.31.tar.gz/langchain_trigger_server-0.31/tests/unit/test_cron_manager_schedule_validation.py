"""Validation tests for CronTriggerManager._schedule_cron_job."""

import pytest

from langchain_triggers.cron_manager import CronTriggerManager
from langchain_triggers.triggers import cron_trigger


class _FakeTriggerServer:
    def __init__(self, triggers):
        self.triggers = triggers
        self.database = None
        self.langchain_auth_client = None


@pytest.mark.asyncio
async def test_schedule_cron_job_requires_crontab():
    """Missing/empty crontab should raise a clear error."""
    mgr = CronTriggerManager(_FakeTriggerServer([cron_trigger]))

    registration = {
        "id": "reg_missing",
        "template_id": cron_trigger.id,
        "resource": {},
    }

    with pytest.raises(ValueError) as exc:
        await mgr._schedule_cron_job(registration)

    # Message should indicate no schedule was provided
    assert "No schedule provided" in str(exc.value)


@pytest.mark.asyncio
async def test_schedule_cron_job_rejects_invalid_format():
    """Invalid crontab (wrong number of fields) should raise."""
    mgr = CronTriggerManager(_FakeTriggerServer([cron_trigger]))

    registration = {
        "id": "reg_bad_format",
        "template_id": cron_trigger.id,
        "resource": {"crontab": "*"},
    }

    with pytest.raises(ValueError) as exc:
        await mgr._schedule_cron_job(registration)

    assert "expected 5 parts" in str(exc.value)
