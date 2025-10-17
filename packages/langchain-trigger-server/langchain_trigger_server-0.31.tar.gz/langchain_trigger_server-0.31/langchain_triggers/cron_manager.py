"""Dynamic Cron Trigger Manager for scheduled agent execution."""

import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger as APSCronTrigger
from pydantic import BaseModel

from langchain_triggers.core import TriggerHandlerResult, TriggerType

logger = logging.getLogger(__name__)


class CronJobExecution(BaseModel):
    """Model for tracking cron job execution history."""

    registration_id: str
    cron_pattern: str
    scheduled_time: datetime
    actual_start_time: datetime
    completion_time: datetime | None = None
    status: str  # "running", "completed", "failed"
    error_message: str | None = None
    agents_invoked: int = 0


class CronTriggerManager:
    """Manages dynamic cron job scheduling based on database registrations."""

    def __init__(self, trigger_server):
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.trigger_server = trigger_server
        self.active_jobs = {}  # registration_id -> job_id mapping
        self.execution_history = []  # Keep recent execution history
        self.max_history = 1000

    def _is_polling(self, trigger) -> bool:
        ttype = getattr(trigger, "trigger_type", None)
        val = getattr(ttype, "value", ttype)
        try:
            return str(val).lower() == TriggerType.POLLING.value
        except Exception:
            return False

    async def start(self):
        """Start scheduler and load existing cron registrations."""
        try:
            self.scheduler.start()
            logger.info("polling_manager_started timezone=UTC")
            await self._load_existing_registrations()
        except Exception as e:
            logger.error(f"Failed to start CronTriggerManager: {e}")
            raise

    async def shutdown(self):
        """Shutdown scheduler gracefully."""
        try:
            self.scheduler.shutdown(wait=True)
        except Exception as e:
            logger.error(f"Error shutting down CronTriggerManager: {e}")

    async def _load_existing_registrations(self):
        """Load all existing polling registrations from database and schedule them.

        Discovers polling-capable triggers dynamically from registered templates.
        """
        try:
            scheduled_total = 0
            polling_templates = [
                t for t in self.trigger_server.triggers if self._is_polling(t)
            ]
            ids_csv = ",".join([t.id for t in polling_templates]) or ""
            logger.info(
                f"polling_templates_loaded count={len(polling_templates)} ids={ids_csv}"
            )

            for template in polling_templates:
                template_id = template.id
                logger.info(
                    "polling_template "
                    f"template_id={template_id} provider={(template.provider or '').lower()} name={getattr(template, 'name', '')}"
                )
                try:
                    registrations = (
                        await self.trigger_server.database.get_all_registrations(
                            template_id
                        )
                    )
                    logger.info(
                        f"registrations_fetched template_id={template_id} count={len(registrations)}"
                    )
                except Exception as e:
                    logger.error(
                        f"registrations_fetch_err template_id={template_id} error={str(e)}"
                    )
                    continue

                scheduled_for_template = 0
                for registration in registrations:
                    if registration.get("status") == "active":
                        try:
                            await self._schedule_cron_job(registration)
                            scheduled_total += 1
                            scheduled_for_template += 1
                        except Exception as e:
                            logger.error(
                                "registration_schedule_err "
                                f"registration_id={registration.get('id')} template_id={template_id} error={str(e)}"
                            )
                logger.debug(
                    f"registrations_scheduled template_id={template_id} scheduled={scheduled_for_template}"
                )
            logger.debug(f"polling_schedule_complete total_scheduled={scheduled_total}")
        except Exception as e:
            logger.error(f"polling_load_err error={str(e)}")

    async def reload_from_database(self):
        """Reload all cron registrations from database, replacing current schedules."""
        try:
            # Clear all current jobs
            for registration_id in list(self.active_jobs.keys()):
                await self._unschedule_cron_job(registration_id)

            # Reload from database
            await self._load_existing_registrations()

        except Exception as e:
            logger.error(f"Failed to reload cron jobs from database: {e}")
            raise

    async def on_registration_created(self, registration: dict[str, Any]):
        """Called when a new polling registration is created."""
        template_id_raw = registration.get("template_id")
        template_id = str(template_id_raw) if template_id_raw is not None else None
        if template_id is None:
            logger.error(
                "registration_missing_template_id id=%s", registration.get("id")
            )
            return
        tmpl = next(
            (t for t in self.trigger_server.triggers if t.id == template_id), None
        )
        if not tmpl:
            logger.error(
                "registration_template_not_found id=%s template_id=%s",
                registration.get("id"),
                template_id,
            )
            return
        if self._is_polling(tmpl):
            try:
                await self._schedule_cron_job(registration)
            except Exception as e:
                logger.error(
                    f"Failed to schedule new cron job {registration.get('id')}: {e}"
                )
                raise
        else:
            logger.debug(
                "registration_not_polling id=%s template_id=%s trigger_type=%s",
                registration.get("id"),
                template_id,
                tmpl.trigger_type,
            )

    async def on_registration_deleted(self, registration_id: str):
        """Called when a cron registration is deleted."""
        try:
            await self._unschedule_cron_job(registration_id)
        except Exception as e:
            logger.error(f"Failed to unschedule cron job {registration_id}: {e}")

    async def _schedule_cron_job(self, registration: dict[str, Any]):
        """Add a polling job to the scheduler using a 5-field crontab."""
        registration_id = registration["id"]
        resource_data = registration.get("resource", {})
        crontab = (resource_data.get("crontab") or "").strip()
        template_id = registration.get("template_id")
        template_id = str(template_id) if template_id is not None else None
        tmpl = next(
            (t for t in self.trigger_server.triggers if t.id == template_id), None
        )
        if tmpl and not crontab:
            crontab = (getattr(tmpl, "default_crontab", None) or "").strip()

        try:
            if not crontab:
                if template_id is None:
                    raise ValueError(
                        f"No schedule provided for registration {registration_id} (missing template_id)"
                    )
                if tmpl is None:
                    raise ValueError(
                        f"No schedule provided for registration {registration_id} (template '{template_id}' not found)"
                    )
                raise ValueError(
                    f"No schedule provided for registration {registration_id} (no crontab and no default_crontab for template '{template_id}')"
                )

            cron_parts = crontab.split()
            if len(cron_parts) != 5:
                raise ValueError(f"Invalid cron format: {crontab} (expected 5 parts)")
            minute, hour, day, month, day_of_week = cron_parts
            trigger = APSCronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone="UTC",
            )
            job_id = f"cron_{registration_id}"
            logger.info(
                f"schedule_cron registration_id={registration_id} crontab='{crontab}' job_id={job_id}"
            )

            job = self.scheduler.add_job(
                self._execute_cron_job_with_monitoring,
                trigger=trigger,
                args=[registration],
                id=job_id,
                name=f"Polling job for registration {registration_id}",
                max_instances=1,
                replace_existing=True,
            )

            self.active_jobs[registration_id] = job.id

        except Exception as e:
            logger.error(
                f"Failed to schedule polling job for registration {registration_id}: {e}"
            )
            raise

    async def _unschedule_cron_job(self, registration_id: str):
        """Remove a cron job from the scheduler."""
        if registration_id in self.active_jobs:
            job_id = self.active_jobs[registration_id]
            try:
                self.scheduler.remove_job(job_id)
                del self.active_jobs[registration_id]
            except Exception as e:
                logger.error(f"Failed to unschedule cron job {job_id}: {e}")
                raise
        else:
            logger.warning(
                f"Attempted to unschedule non-existent cron job {registration_id}"
            )

    async def _execute_cron_job_with_monitoring(self, registration: dict[str, Any]):
        """Execute a scheduled cron job with full monitoring and error handling."""
        registration_id = registration["id"]
        cron_pattern = registration["resource"]["crontab"]

        execution = CronJobExecution(
            registration_id=str(registration_id),
            cron_pattern=cron_pattern,
            scheduled_time=datetime.utcnow(),
            actual_start_time=datetime.utcnow(),
            status="running",
        )

        try:
            agents_invoked = await self.execute_cron_job(registration)
            execution.status = "completed"
            execution.agents_invoked = agents_invoked
            logger.info(
                f"✓ Cron job {registration_id} completed successfully - invoked {agents_invoked} agent(s)"
            )

        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            logger.error(f"✗ Cron job {registration_id} failed: {e}")

        finally:
            execution.completion_time = datetime.utcnow()
            await self._record_execution(execution)

    async def execute_cron_job(self, registration: dict[str, Any]) -> int:
        """Execute a cron job - invoke agents. Can be called manually or by scheduler."""
        registration_id = registration["id"]
        user_id = registration["user_id"]
        template_id = registration.get("template_id")
        template_id = str(template_id) if template_id is not None else None
        tenant_id = (
            registration.get("metadata", {}).get("client_metadata", {}).get("tenant_id")
        )

        # Get agent links
        agent_links = await self.trigger_server.database.get_agents_for_trigger(
            registration_id
        )

        if not agent_links:
            logger.warning(f"No agents linked to cron job {registration_id}")
            return 0

        tmpl = next(
            (t for t in self.trigger_server.triggers if t.id == template_id), None
        )

        if not tmpl or not self._is_polling(tmpl):
            available_ids = ",".join([t.id for t in self.trigger_server.triggers])
            logger.error(
                "template_not_polling "
                f"template_id={template_id} available_templates={available_ids}"
            )
            return 0

        result: TriggerHandlerResult = await tmpl.poll_handler(
            registration,
            self.trigger_server.database,
            self.trigger_server.langchain_auth_client,
        )

        if not result.invoke_agent:
            logger.info(
                "poll_result "
                f"registration_id={registration_id} "
                f"trigger_id={template_id} "
                f"provider={(tmpl.provider or '').lower()} "
                f"invoke_agent=false messages_count=0"
            )
            return 0

        agents_invoked = 0
        messages = result.agent_messages or []

        logger.info(
            "poll_result "
            f"registration_id={registration_id} "
            f"trigger_id={template_id} "
            f"provider={(tmpl.provider or '').lower()} "
            f"invoke_agent=true messages_count={len(messages)} "
            f"agents_linked={len(agent_links)}"
        )

        for message in messages:
            for agent_link in agent_links:
                agent_id = (
                    agent_link
                    if isinstance(agent_link, str)
                    else agent_link.get("agent_id")
                )
                # Ensure agent_id and user_id are strings for JSON serialization
                agent_id_str = str(agent_id)
                user_id_str = str(user_id)
                tenant_id_str = str(tenant_id)

                current_time = datetime.utcnow()
                current_time_str = current_time.strftime("%A, %B %d, %Y at %H:%M UTC")

                agent_input = {
                    "messages": [
                        {
                            "role": "human",
                            "content": f"ACTION: triggering cron from langchain-trigger-server\nCURRENT TIME: {current_time_str}\n\n{message}",
                        }
                    ]
                }

                try:
                    success = await self.trigger_server._invoke_agent(
                        agent_id=agent_id_str,
                        user_id=user_id_str,
                        tenant_id=tenant_id_str,
                        input_data=agent_input,
                    )
                    if success:
                        logger.info(
                            "invoke_agent_ok "
                            f"registration_id={registration_id} "
                            f"agent_id={agent_id_str}"
                        )
                        agents_invoked += 1
                except Exception as e:
                    logger.error(
                        "invoke_agent_err "
                        f"registration_id={registration_id} "
                        f"agent_id={agent_id_str} "
                        f"error={str(e)}"
                    )

        logger.info(
            "poll_invoke_summary "
            f"registration_id={registration_id} "
            f"agents_invoked={agents_invoked} "
            f"messages_count={len(messages)}"
        )
        return agents_invoked

    async def _record_execution(self, execution: CronJobExecution):
        """Record execution history (in memory for now)."""
        self.execution_history.append(execution)

        # Keep only recent executions
        if len(self.execution_history) > self.max_history:
            self.execution_history = self.execution_history[-self.max_history :]

    def get_active_jobs(self) -> dict[str, str]:
        """Get currently active cron jobs."""
        return self.active_jobs.copy()

    def get_execution_history(self, limit: int = 100) -> list[CronJobExecution]:
        """Get recent execution history."""
        return self.execution_history[-limit:]

    def get_job_status(self) -> dict[str, Any]:
        """Get status information about the cron manager."""
        return {
            "active_jobs": len(self.active_jobs),
            "scheduler_running": self.scheduler.running,
            "total_executions": len(self.execution_history),
            "active_job_ids": list(self.active_jobs.keys()),
        }
