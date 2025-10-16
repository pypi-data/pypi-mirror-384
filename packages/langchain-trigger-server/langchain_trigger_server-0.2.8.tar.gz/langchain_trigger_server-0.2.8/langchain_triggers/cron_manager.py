"""Dynamic Cron Trigger Manager for scheduled agent execution."""

import logging
from datetime import datetime
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger as APSCronTrigger
from pydantic import BaseModel

from langchain_triggers.triggers.cron_trigger import CRON_TRIGGER_ID

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

    async def start(self):
        """Start scheduler and load existing cron registrations."""
        try:
            self.scheduler.start()
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
        """Load all existing cron registrations from database and schedule them."""
        try:
            registrations = await self.trigger_server.database.get_all_registrations(
                CRON_TRIGGER_ID
            )

            scheduled_count = 0
            for registration in registrations:
                if registration.get("status") == "active":
                    try:
                        await self._schedule_cron_job(registration)
                        scheduled_count += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to schedule existing cron job {registration.get('id')}: {e}"
                        )

        except Exception as e:
            logger.error(f"Failed to load existing cron registrations: {e}")

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
        """Called when a new cron registration is created."""
        if registration.get("trigger_template_id") == CRON_TRIGGER_ID:
            try:
                await self._schedule_cron_job(registration)
            except Exception as e:
                logger.error(
                    f"Failed to schedule new cron job {registration['id']}: {e}"
                )
                raise

    async def on_registration_deleted(self, registration_id: str):
        """Called when a cron registration is deleted."""
        try:
            await self._unschedule_cron_job(registration_id)
        except Exception as e:
            logger.error(f"Failed to unschedule cron job {registration_id}: {e}")

    async def _schedule_cron_job(self, registration: dict[str, Any]):
        """Add a cron job to the scheduler."""
        registration_id = registration["id"]
        resource_data = registration.get("resource", {})
        crontab = resource_data.get("crontab", "")

        if not crontab:
            raise ValueError(
                f"No crontab pattern found in registration {registration_id}"
            )

        try:
            # Parse cron expression
            cron_parts = crontab.strip().split()
            if len(cron_parts) != 5:
                raise ValueError(f"Invalid cron format: {crontab} (expected 5 parts)")

            minute, hour, day, month, day_of_week = cron_parts

            # Create APScheduler cron trigger
            trigger = APSCronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone="UTC",
            )

            # Schedule the job
            job = self.scheduler.add_job(
                self._execute_cron_job_with_monitoring,
                trigger=trigger,
                args=[registration],
                id=f"cron_{registration_id}",
                name=f"Cron job for registration {registration_id}",
                max_instances=1,  # Prevent overlapping executions
                replace_existing=True,
            )

            self.active_jobs[registration_id] = job.id

        except Exception as e:
            logger.error(
                f"Failed to schedule cron job for registration {registration_id}: {e}"
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

        # Get agent links
        agent_links = await self.trigger_server.database.get_agents_for_trigger(
            registration_id
        )

        if not agent_links:
            logger.warning(f"No agents linked to cron job {registration_id}")
            return 0

        agents_invoked = 0
        for agent_link in agent_links:
            agent_id = (
                agent_link
                if isinstance(agent_link, str)
                else agent_link.get("agent_id")
            )
            # Ensure agent_id and user_id are strings for JSON serialization
            agent_id_str = str(agent_id)
            user_id_str = str(user_id)

            current_time = datetime.utcnow()
            current_time_str = current_time.strftime("%A, %B %d, %Y at %H:%M UTC")

            agent_input = {
                "messages": [
                    {
                        "role": "human",
                        "content": f"ACTION: triggering cron from langchain-trigger-server\nCURRENT TIME: {current_time_str}",
                    }
                ]
            }

            try:
                success = await self.trigger_server._invoke_agent(
                    agent_id=agent_id_str,
                    user_id=user_id_str,
                    input_data=agent_input,
                )
                if success:
                    agents_invoked += 1

            except Exception as e:
                logger.error(
                    f"✗ Error invoking agent {agent_id_str} for cron job {registration_id}: {e}"
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
