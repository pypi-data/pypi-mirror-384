"""FastAPI application for trigger server."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from langchain_auth.client import Client
from langgraph_sdk import get_client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .auth.slack_hmac import (
    SlackSignatureVerificationError,
    extract_slack_headers,
    get_slack_signing_secret,
    verify_slack_signature,
)
from .cron_manager import CronTriggerManager
from .database import TriggerDatabaseInterface, create_database
from .decorators import TriggerTemplate
from .triggers.cron_trigger import CRON_TRIGGER_ID

logger = logging.getLogger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for API endpoints."""

    def __init__(self, app, auth_handler: Callable):
        super().__init__(app)
        self.auth_handler = auth_handler

    async def dispatch(self, request: Request, call_next):
        # Skip auth for webhooks, health/root endpoints, and OPTIONS requests
        if (
            request.url.path.startswith("/v1/triggers/webhooks/")
            or request.url.path in ["/", "/health"]
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        try:
            # Run mandatory custom authentication
            identity = await self.auth_handler({}, dict(request.headers))

            if not identity or not identity.get("identity"):
                return Response(
                    content='{"detail": "Authentication required"}',
                    status_code=401,
                    media_type="application/json",
                )

            # Store identity in request state for endpoints to access
            request.state.current_user = identity

        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return Response(
                content='{"detail": "Authentication failed"}',
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)


def get_current_user(request: Request) -> dict[str, Any]:
    """FastAPI dependency to get the current authenticated user."""
    if not hasattr(request.state, "current_user"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.current_user


class TriggerServer:
    """FastAPI application for trigger webhooks."""

    def __init__(
        self,
        auth_handler: Callable,
        database: TriggerDatabaseInterface | None = None,
        database_type: str | None = "supabase",
        **database_kwargs: Any,
    ):
        # Configure uvicorn logging to use consistent formatting
        self._configure_uvicorn_logging()

        self.app = FastAPI(
            title="Triggers Server",
            description="Event-driven triggers framework",
            version="0.1.0",
        )

        # Configure database: allow either instance injection or factory creation
        # Defaults to Supabase for backward compatibility
        if database and database_type != "supabase":
            raise ValueError("Provide either 'database' or 'database_type', not both")
        if database is not None:
            self.database = database
        else:
            self.database = create_database(database_type, **database_kwargs)
        self.auth_handler = auth_handler

        # LangGraph configuration
        self.langgraph_api_url = os.getenv("LANGGRAPH_API_URL")
        self.langsmith_api_key = os.getenv("LANGCHAIN_API_KEY")
        self.trigger_server_auth_api_url = os.getenv("TRIGGER_SERVER_HOST_API_URL")

        if not self.langgraph_api_url:
            raise ValueError("LANGGRAPH_API_URL environment variable is required")

        self.langgraph_api_url = self.langgraph_api_url.rstrip("/")

        # Initialize LangGraph SDK client
        self.langgraph_client = get_client(
            url=self.langgraph_api_url, api_key=self.langsmith_api_key
        )
        logger.info(
            f"✓ LangGraph client initialized with URL: {self.langgraph_api_url}"
        )
        if self.langsmith_api_key:
            logger.info("✓ LangGraph client initialized with API key.")
        else:
            logger.warning("⚠ LangGraph client initialized without API key")

        # Initialize LangChain auth client
        langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
        if langchain_api_key:
            self.langchain_auth_client = Client(
                api_key=langchain_api_key, api_url=self.trigger_server_auth_api_url
            )
            logger.info("✓ LangChain auth client initialized")
        else:
            self.langchain_auth_client = None
            logger.warning(
                "LANGCHAIN_API_KEY not found - OAuth token injection disabled"
            )

        self.triggers: list[TriggerTemplate] = []

        # Initialize CronTriggerManager
        self.cron_manager = CronTriggerManager(self)

        # Setup authentication middleware
        self.app.add_middleware(AuthenticationMiddleware, auth_handler=auth_handler)

        # Setup routes
        self._setup_routes()

        # Add startup and shutdown events
        @self.app.on_event("startup")
        async def startup_event():
            await self.ensure_trigger_templates()
            await self.cron_manager.start()

        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.cron_manager.shutdown()

    def _configure_uvicorn_logging(self) -> None:
        """Configure uvicorn loggers to use consistent formatting for production deployments."""
        formatter = logging.Formatter("%(levelname)s: %(name)s - %(message)s")

        # Configure uvicorn access logger
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_access_logger.handlers.clear()
        access_handler = logging.StreamHandler()
        access_handler.setFormatter(formatter)
        uvicorn_access_logger.addHandler(access_handler)

        # Configure uvicorn error logger
        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        uvicorn_error_logger.handlers.clear()
        error_handler = logging.StreamHandler()
        error_handler.setFormatter(formatter)
        uvicorn_error_logger.addHandler(error_handler)

        # Configure uvicorn main logger
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.handlers.clear()
        main_handler = logging.StreamHandler()
        main_handler.setFormatter(formatter)
        uvicorn_logger.addHandler(main_handler)

    def add_trigger(self, trigger: TriggerTemplate) -> None:
        """Add a trigger template to the app."""
        # Check for duplicate IDs
        if any(t.id == trigger.id for t in self.triggers):
            raise ValueError(f"Trigger with id '{trigger.id}' already exists")

        self.triggers.append(trigger)

        if trigger.trigger_handler:

            async def handler_endpoint(request: Request) -> dict[str, Any]:
                return await self._handle_request(trigger, request)

            handler_path = f"/v1/triggers/webhooks/{trigger.id}"
            self.app.post(handler_path)(handler_endpoint)
            logger.info(f"Added handler route: POST {handler_path}")

        logger.info(
            f"Registered trigger template in memory: {trigger.name} ({trigger.id})"
        )

    async def ensure_trigger_templates(self) -> None:
        """Ensure all registered trigger templates exist in the database."""
        for trigger in self.triggers:
            existing = await self.database.get_trigger_template(trigger.id)
            if not existing:
                logger.info(
                    f"Creating new trigger template in database: {trigger.name} ({trigger.id})"
                )
                await self.database.create_trigger_template(
                    id=trigger.id,
                    provider=trigger.provider,
                    name=trigger.name,
                    description=trigger.description,
                    registration_schema=trigger.registration_model.model_json_schema(),
                )
                logger.info(
                    f"✓ Successfully created trigger template: {trigger.name} ({trigger.id})"
                )
            else:
                logger.info(
                    f"✓ Trigger template already exists in database: {trigger.name} ({trigger.id})"
                )

    def add_triggers(self, triggers: list[TriggerTemplate]) -> None:
        """Add multiple triggers."""
        for trigger in triggers:
            self.add_trigger(trigger)

    def _setup_routes(self) -> None:
        """Setup built-in API routes."""

        @self.app.get("/")
        async def root() -> dict[str, str]:
            return {"message": "Triggers Server", "version": "0.1.0"}

        @self.app.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "healthy"}

        @self.app.get("/v1/triggers")
        async def api_list_triggers() -> dict[str, Any]:
            """List available trigger templates."""
            templates = await self.database.get_trigger_templates()
            trigger_list = []
            for template in templates:
                trigger_list.append(
                    {
                        "id": template["id"],
                        "provider": template["provider"],
                        "displayName": template["name"],
                        "description": template["description"],
                        "path": "/v1/triggers/registrations",
                        "method": "POST",
                        "payloadSchema": template.get("registration_schema", {}),
                    }
                )

            return {"success": True, "data": trigger_list}

        @self.app.get("/v1/triggers/registrations")
        async def api_list_registrations(
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """List user's trigger registrations (user-scoped)."""
            try:
                user_id = current_user["identity"]

                # Get user's trigger registrations with linked agents in a single query
                user_registrations = (
                    await self.database.get_user_trigger_registrations_with_agents(
                        user_id
                    )
                )

                # Format response to match expected structure
                registrations = []
                for reg in user_registrations:
                    registrations.append(
                        {
                            "id": reg["id"],
                            "user_id": reg["user_id"],
                            "template_id": reg.get("trigger_templates", {}).get("id"),
                            "resource": reg["resource"],
                            "linked_agent_ids": reg.get("linked_agent_ids", []),
                            "created_at": reg["created_at"],
                        }
                    )

                return {"success": True, "data": registrations}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error listing registrations: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/triggers/registrations")
        async def api_create_registration(
            request: Request, current_user: dict[str, Any] = Depends(get_current_user)
        ) -> dict[str, Any]:
            """Create a new trigger registration."""
            try:
                payload = await request.json()
                logger.info(f"Registration payload received: {payload}")

                user_id = current_user["identity"]
                trigger_id = payload.get("type")
                if not trigger_id:
                    raise HTTPException(
                        status_code=400, detail="Missing required field: type"
                    )

                trigger = next((t for t in self.triggers if t.id == trigger_id), None)
                if not trigger:
                    raise HTTPException(
                        status_code=400, detail=f"Unknown trigger type: {trigger_id}"
                    )

                # Parse payload into registration model first
                try:
                    registration_instance = trigger.registration_model(**payload)
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid payload for trigger: {str(e)}"
                    )

                # Check for duplicate registration based on resource data within this user's scope
                resource_dict = registration_instance.model_dump()
                existing_registration = (
                    await self.database.find_user_registration_by_resource(
                        user_id=user_id,
                        template_id=trigger.id,
                        resource_data=resource_dict,
                    )
                )

                if existing_registration:
                    raise HTTPException(
                        status_code=400,
                        detail=f"You already have a registration with this configuration for trigger type '{trigger.id}'. Registration ID: {existing_registration.get('id')}",
                    )
                result = await trigger.registration_handler(
                    user_id, self.langchain_auth_client, registration_instance
                )

                # Check if handler requested to skip registration (e.g., for OAuth or URL verification)
                if not result.create_registration:
                    logger.info(
                        "Registration handler requested to skip database creation"
                    )
                    import json

                    from fastapi import Response

                    return Response(
                        content=json.dumps(result.response_body),
                        status_code=result.status_code,
                        media_type="application/json",
                    )

                resource_dict = registration_instance.model_dump()

                registration = await self.database.create_trigger_registration(
                    user_id=user_id,
                    template_id=trigger.id,
                    resource=resource_dict,
                    metadata=result.metadata,
                )

                if not registration:
                    raise HTTPException(
                        status_code=500, detail="Failed to create trigger registration"
                    )

                # Reload cron manager to pick up any new cron registrations
                await self.cron_manager.reload_from_database()

                # Return registration result
                return {
                    "success": True,
                    "data": registration,
                    "metadata": result.metadata,
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.exception(f"Error creating trigger registration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/v1/triggers/registrations/{registration_id}/agents")
        async def api_list_registration_agents(
            registration_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """List agents linked to this registration."""
            try:
                user_id = current_user["identity"]

                # Get the specific trigger registration
                trigger = await self.database.get_trigger_registration(
                    registration_id, user_id
                )
                if not trigger:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Return the linked agent IDs
                return {
                    "success": True,
                    "data": trigger.get("linked_assistant_ids", []),
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting registration agents: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/triggers/registrations/{registration_id}/agents/{agent_id}")
        async def api_add_agent_to_trigger(
            registration_id: str,
            agent_id: str,
            request: Request,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Add an agent to a trigger registration."""
            try:
                # Parse request body for field selection
                try:
                    body = await request.json()
                    field_selection = body.get("field_selection")
                except:
                    field_selection = None

                user_id = current_user["identity"]

                # Verify the trigger registration exists and belongs to the user
                registration = await self.database.get_trigger_registration(
                    registration_id, user_id
                )
                if not registration:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Link the agent to the trigger
                success = await self.database.link_agent_to_trigger(
                    agent_id=agent_id,
                    registration_id=registration_id,
                    created_by=user_id,
                    field_selection=field_selection,
                )

                if not success:
                    raise HTTPException(
                        status_code=500, detail="Failed to link agent to trigger"
                    )

                return {
                    "success": True,
                    "message": f"Successfully linked agent {agent_id} to trigger {registration_id}",
                    "data": {"registration_id": registration_id, "agent_id": agent_id},
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error linking agent to trigger: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete(
            "/v1/triggers/registrations/{registration_id}/agents/{agent_id}"
        )
        async def api_remove_agent_from_trigger(
            registration_id: str,
            agent_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Remove an agent from a trigger registration."""
            try:
                user_id = current_user["identity"]

                # Verify the trigger registration exists and belongs to the user
                registration = await self.database.get_trigger_registration(
                    registration_id, user_id
                )
                if not registration:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Unlink the agent from the trigger
                success = await self.database.unlink_agent_from_trigger(
                    agent_id=agent_id, registration_id=registration_id
                )

                if not success:
                    raise HTTPException(
                        status_code=500, detail="Failed to unlink agent from trigger"
                    )

                return {
                    "success": True,
                    "message": f"Successfully unlinked agent {agent_id} from trigger {registration_id}",
                    "data": {"registration_id": registration_id, "agent_id": agent_id},
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error unlinking agent from trigger: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/triggers/registrations/{registration_id}/execute")
        async def api_execute_trigger_now(
            registration_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Manually execute a cron trigger registration immediately."""
            try:
                user_id = current_user["identity"]

                # Verify the trigger registration exists and belongs to the user
                registration = await self.database.get_trigger_registration(
                    registration_id, user_id
                )
                if not registration:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Get the template to check if it's a cron trigger
                template_id = registration.get("template_id")
                if template_id != CRON_TRIGGER_ID:
                    raise HTTPException(
                        status_code=400,
                        detail="Manual execution is only supported for cron triggers",
                    )

                # Execute the cron trigger using the cron manager
                agents_invoked = await self.cron_manager.execute_cron_job(registration)

                return {
                    "success": True,
                    "message": f"Manually executed cron trigger {registration_id}",
                    "agents_invoked": agents_invoked,
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error executing trigger: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _handle_request(
        self, trigger: TriggerTemplate, request: Request
    ) -> dict[str, Any]:
        """Handle an incoming request with a handler function."""
        try:
            if request.method == "POST":
                if request.headers.get("content-type", "").startswith(
                    "application/json"
                ):
                    # Read body once for both auth and parsing
                    body_bytes = await request.body()
                    body_str = body_bytes.decode("utf-8")

                    if self._is_slack_trigger(trigger):
                        await self._verify_slack_webhook_auth_with_body(
                            request, body_str
                        )

                    import json

                    payload = json.loads(body_str)

                    if (
                        payload.get("type") == "url_verification"
                        and "challenge" in payload
                    ):
                        logger.info("Responding to Slack URL verification challenge")
                        return {"challenge": payload["challenge"]}
                else:
                    # Handle form data or other content types
                    body = await request.body()
                    payload = {"raw_body": body.decode("utf-8") if body else ""}
            else:
                payload = dict(request.query_params)

            query_params = dict(request.query_params)
            result = await trigger.trigger_handler(
                payload, query_params, self.database, self.langchain_auth_client
            )
            if not result.invoke_agent:
                return result.response_body

            registration_id = result.registration["id"]
            agent_links = await self.database.get_agents_for_trigger(registration_id)

            agents_invoked = 0
            # Iterate through each message and invoke agents for each
            for message in result.agent_messages:
                for agent_link in agent_links:
                    agent_id = (
                        agent_link
                        if isinstance(agent_link, str)
                        else agent_link.get("agent_id")
                    )
                    # Ensure agent_id and user_id are strings for JSON serialization
                    agent_id_str = str(agent_id)
                    user_id_str = str(result.registration["user_id"])

                    agent_input = {"messages": [{"role": "human", "content": message}]}

                    try:
                        success = await self._invoke_agent(
                            agent_id=agent_id_str,
                            user_id=user_id_str,
                            input_data=agent_input,
                        )
                        if success:
                            agents_invoked += 1
                    except Exception as e:
                        logger.error(
                            f"Error invoking agent {agent_id_str}: {e}", exc_info=True
                        )
            logger.info(
                f"Processed trigger handler with {len(result.agent_messages)} messages, invoked {agents_invoked} agents"
            )

            return {"success": True, "agents_invoked": agents_invoked}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in trigger handler: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Trigger processing failed: {str(e)}"
            )

    async def _invoke_agent(
        self,
        agent_id: str,
        user_id: str,
        input_data: dict[str, Any],
    ) -> bool:
        """Invoke LangGraph agent using the SDK."""
        # Ensure user_id is a string for JSON serialization
        user_id_str = str(user_id)
        logger.info(f"Invoking LangGraph agent {agent_id} for user {user_id_str}")

        try:
            headers = {
                "x-auth-scheme": "agent-builder-trigger",
                "x-user-id": user_id_str,
            }

            # Note: API key is already set in client initialization, no need to add to headers
            if not self.langsmith_api_key:
                logger.warning(
                    "No LANGSMITH_API_KEY available - authentication may fail"
                )

            thread = await self.langgraph_client.threads.create(
                metadata={
                    "triggered_by": "langchain-triggers",
                    "user_id": user_id_str,
                },
                headers=headers,
            )
            logger.info(f"Created thread {thread['thread_id']} for agent {agent_id}")

            run = await self.langgraph_client.runs.create(
                thread_id=thread["thread_id"],
                assistant_id=agent_id,
                input=input_data,
                metadata={
                    "triggered_by": "langchain-triggers",
                    "user_id": user_id_str,
                },
                headers=headers,
            )

            logger.info(
                f"Successfully invoked agent {agent_id}, run_id: {run['run_id']}, thread_id: {run['thread_id']}"
            )
            return True

        except Exception as e:
            # Handle 404s (agent not found) as warnings, not errors
            if (
                hasattr(e, "response")
                and getattr(e.response, "status_code", None) == 404
            ):
                logger.warning(
                    f"Agent {agent_id} not found (404) - agent may have been deleted or moved"
                )
                return False
            else:
                logger.error(f"Error invoking agent {agent_id}: {e}")
                raise

    def _is_slack_trigger(self, trigger: TriggerTemplate) -> bool:
        """Check if a trigger is from Slack and requires HMAC signature verification."""
        return trigger.provider.lower() == "slack" or "slack" in trigger.id.lower()

    async def _verify_slack_webhook_auth(self, request: Request) -> None:
        """Verify Slack HMAC signature for webhook requests.

        Slack uses HMAC-SHA256 signatures to verify webhook authenticity.
        The signature is computed from the timestamp, body, and signing secret.

        Args:
            request: The FastAPI request object

        Raises:
            HTTPException: If authentication fails
        """
        try:
            signing_secret = get_slack_signing_secret()
            if not signing_secret:
                logger.error("SLACK_SIGNING_SECRET environment variable not set")
                raise HTTPException(
                    status_code=500,
                    detail="Slack signing secret not configured on server",
                )

            headers_dict = dict(request.headers)
            signature, timestamp = extract_slack_headers(headers_dict)

            if not signature:
                logger.error("Missing X-Slack-Signature header")
                raise HTTPException(
                    status_code=401,
                    detail="Missing X-Slack-Signature header. Slack webhooks require signature verification.",
                )

            if not timestamp:
                logger.error("Missing X-Slack-Request-Timestamp header")
                raise HTTPException(
                    status_code=401,
                    detail="Missing X-Slack-Request-Timestamp header. Slack webhooks require timestamp.",
                )

            body = await request.body()
            body_str = body.decode("utf-8")

            try:
                verify_slack_signature(
                    signing_secret=signing_secret,
                    timestamp=timestamp,
                    body=body_str,
                    signature=signature,
                )
                logger.info(
                    f"Successfully verified Slack webhook signature. Timestamp: {timestamp}"
                )
            except SlackSignatureVerificationError as e:
                logger.error(f"Slack signature verification failed: {e}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Slack signature verification failed: {str(e)}",
                )

            # Store verification info in request state
            request.state.slack_verified = True
            request.state.slack_timestamp = timestamp

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Slack webhook authentication: {e}")
            raise HTTPException(
                status_code=500, detail=f"Authentication error: {str(e)}"
            )

    async def _verify_slack_webhook_auth_with_body(
        self, request: Request, body_str: str
    ) -> None:
        """Verify Slack HMAC signature for webhook requests using pre-read body.

        Slack uses HMAC-SHA256 signatures to verify webhook authenticity.
        The signature is computed from the timestamp, body, and signing secret.

        Args:
            request: The FastAPI request object
            body_str: The request body as a string (already read)

        Raises:
            HTTPException: If authentication fails
        """
        try:
            signing_secret = get_slack_signing_secret()
            if not signing_secret:
                logger.error("SLACK_SIGNING_SECRET environment variable not set")
                raise HTTPException(
                    status_code=500,
                    detail="Slack signing secret not configured on server",
                )

            headers_dict = dict(request.headers)
            signature, timestamp = extract_slack_headers(headers_dict)

            if not signature:
                logger.error("Missing X-Slack-Signature header")
                raise HTTPException(
                    status_code=401,
                    detail="Missing X-Slack-Signature header. Slack webhooks require signature verification.",
                )

            if not timestamp:
                logger.error("Missing X-Slack-Request-Timestamp header")
                raise HTTPException(
                    status_code=401,
                    detail="Missing X-Slack-Request-Timestamp header. Slack webhooks require timestamp.",
                )

            try:
                verify_slack_signature(
                    signing_secret=signing_secret,
                    timestamp=timestamp,
                    body=body_str,
                    signature=signature,
                )
                logger.info(
                    f"Successfully verified Slack webhook signature. Timestamp: {timestamp}"
                )
            except SlackSignatureVerificationError as e:
                logger.error(f"Slack signature verification failed: {e}")
                raise HTTPException(
                    status_code=401,
                    detail=f"Slack signature verification failed: {str(e)}",
                )

            # Store verification info in request state
            request.state.slack_verified = True
            request.state.slack_timestamp = timestamp

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Slack webhook authentication: {e}")
            raise HTTPException(
                status_code=500, detail=f"Authentication error: {str(e)}"
            )

    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app
