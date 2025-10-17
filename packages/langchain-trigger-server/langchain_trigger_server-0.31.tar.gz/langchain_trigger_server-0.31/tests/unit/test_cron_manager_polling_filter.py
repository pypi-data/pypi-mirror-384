"""Unit tests for CronTriggerManager filtering logic (polling vs webhook)."""

from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from langchain_triggers.core import TriggerType
from langchain_triggers.cron_manager import CronTriggerManager
from langchain_triggers.decorators import TriggerTemplate
from langchain_triggers.triggers import cron_trigger


class _DummyRegModel(BaseModel):
    field: str | None = None


async def _dummy_reg_handler(user_id, auth_client, registration):
    from langchain_triggers.core import TriggerRegistrationResult

    return TriggerRegistrationResult()


async def _dummy_trigger_handler(payload, query_params, database, auth_client):
    from langchain_triggers.core import TriggerHandlerResult

    return TriggerHandlerResult(invoke_agent=False, response_body={"ok": True})


class _FakeDB:
    def __init__(self, registrations_by_template):
        self._registrations_by_template = registrations_by_template

    async def get_all_registrations(self, template_id):
        return self._registrations_by_template.get(template_id, [])


class _FakeTriggerServer:
    def __init__(self, triggers, database):
        self.triggers = triggers
        self.database = database
        self.langchain_auth_client = None


@pytest.mark.asyncio
async def test_load_existing_registrations_only_schedules_polling():
    webhook_trigger = TriggerTemplate(
        id="webhook_tmpl",
        provider="test",
        name="Webhook",
        description="webhook",
        registration_model=_DummyRegModel,
        registration_handler=_dummy_reg_handler,
        trigger_handler=_dummy_trigger_handler,
        trigger_type=TriggerType.WEBHOOK,
    )

    polling_trigger = cron_trigger

    # Prepare registrations for both templates
    regs = {
        webhook_trigger.id: [
            {
                "id": "reg_w1",
                "status": "active",
                "template_id": webhook_trigger.id,
                "resource": {},
            }
        ],
        polling_trigger.id: [
            {
                "id": "reg_p1",
                "status": "active",
                "template_id": polling_trigger.id,
                "resource": {"crontab": "* * * * *"},
            },
            {
                "id": "reg_p2",
                "status": "inactive",
                "template_id": polling_trigger.id,
                "resource": {"crontab": "* * * * *"},
            },
        ],
    }

    fake_db = _FakeDB(registrations_by_template=regs)
    fake_server = _FakeTriggerServer(
        triggers=[webhook_trigger, polling_trigger], database=fake_db
    )
    mgr = CronTriggerManager(fake_server)

    mgr._schedule_cron_job = AsyncMock()

    await mgr._load_existing_registrations()

    assert mgr._schedule_cron_job.await_count == 1
    called_with = mgr._schedule_cron_job.await_args.args[0]
    assert called_with["id"] == "reg_p1"


@pytest.mark.asyncio
async def test_on_registration_created_only_for_polling():
    """on_registration_created should call schedule only for polling templates."""
    webhook_trigger = TriggerTemplate(
        id="webhook_tmpl2",
        provider="test",
        name="Webhook2",
        description="webhook",
        registration_model=_DummyRegModel,
        registration_handler=_dummy_reg_handler,
        trigger_handler=_dummy_trigger_handler,
        trigger_type=TriggerType.WEBHOOK,
    )

    polling_trigger = cron_trigger

    fake_db = _FakeDB(registrations_by_template={})
    fake_server = _FakeTriggerServer(
        triggers=[webhook_trigger, polling_trigger], database=fake_db
    )
    mgr = CronTriggerManager(fake_server)
    mgr._schedule_cron_job = AsyncMock()

    await mgr.on_registration_created(
        {"id": "reg_w2", "template_id": webhook_trigger.id, "resource": {}}
    )
    assert mgr._schedule_cron_job.await_count == 0

    await mgr.on_registration_created(
        {
            "id": "reg_p3",
            "template_id": polling_trigger.id,
            "resource": {"crontab": "* * * * *"},
        }
    )
    assert mgr._schedule_cron_job.await_count == 1
