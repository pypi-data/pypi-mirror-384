"""Unit tests for TriggerServer API endpoints using in-memory testing."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from langchain_triggers import TriggerServer


async def mock_auth_handler(request_body, headers):
    """Mock authentication handler for testing."""
    auth_header = headers.get("authorization", "")
    if not auth_header:
        return None
    # Extract user ID from Bearer token for testing
    token = auth_header.replace("Bearer ", "")
    return {"identity": f"test_user_{token}"}


class TestRegistration(BaseModel):
    """Simple registration model for testing."""

    name: str


async def dummy_trigger_handler(payload, query_params, database, auth_client):
    """Dummy trigger handler for test triggers."""
    return None


# Mock database class
class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self.templates = []
        self.registrations = []
        self.agent_links = []

    async def create_trigger_template(
        self, id, provider, name, description, registration_schema
    ):
        template = {
            "id": id,
            "provider": provider,
            "name": name,
            "description": description,
            "registration_schema": registration_schema,
        }
        self.templates.append(template)
        return template

    async def get_trigger_template(self, id):
        return next((t for t in self.templates if t["id"] == id), None)

    async def get_trigger_templates(self):
        return self.templates

    async def create_trigger_registration(
        self, user_id, template_id, resource, metadata
    ):
        registration = {
            "id": f"reg_{len(self.registrations)}",
            "user_id": user_id,
            "template_id": template_id,
            "resource": resource,
            "metadata": metadata,
            "created_at": "2025-01-01T00:00:00Z",
            "linked_agent_ids": [],
        }
        self.registrations.append(registration)
        return registration

    async def get_user_trigger_registrations_with_agents(self, user_id):
        return [
            {
                **reg,
                "trigger_templates": {"id": reg["template_id"]},
                "linked_agent_ids": reg.get("linked_agent_ids", []),
            }
            for reg in self.registrations
            if reg["user_id"] == user_id
        ]

    async def get_trigger_registration(self, registration_id, user_id=None):
        for reg in self.registrations:
            if reg["id"] == registration_id:
                if user_id is None or reg["user_id"] == user_id:
                    return reg
        return None

    async def find_user_registration_by_resource(
        self, user_id, template_id, resource_data
    ):
        return None  # No duplicates for testing

    async def link_agent_to_trigger(
        self, agent_id, registration_id, created_by, field_selection=None
    ):
        link = {
            "agent_id": agent_id,
            "registration_id": registration_id,
            "created_by": created_by,
            "field_selection": field_selection,
        }
        self.agent_links.append(link)
        # Update registration
        for reg in self.registrations:
            if reg["id"] == registration_id:
                if "linked_agent_ids" not in reg:
                    reg["linked_agent_ids"] = []
                reg["linked_agent_ids"].append(agent_id)
        return True

    async def unlink_agent_from_trigger(self, agent_id, registration_id):
        self.agent_links = [
            link
            for link in self.agent_links
            if not (
                link["agent_id"] == agent_id
                and link["registration_id"] == registration_id
            )
        ]
        # Update registration
        for reg in self.registrations:
            if reg["id"] == registration_id:
                if "linked_agent_ids" in reg and agent_id in reg["linked_agent_ids"]:
                    reg["linked_agent_ids"].remove(agent_id)
        return True

    async def get_agents_for_trigger(self, registration_id):
        return [
            link["agent_id"]
            for link in self.agent_links
            if link["registration_id"] == registration_id
        ]

    async def get_all_registrations(self, template_id):
        return [reg for reg in self.registrations if reg["template_id"] == template_id]


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "LANGGRAPH_API_URL": "http://localhost:8000",
            "LANGCHAIN_API_KEY": "test_api_key",
        },
    ):
        yield


@pytest_asyncio.fixture
async def trigger_server(mock_env):
    """Create a TriggerServer instance for testing."""
    mock_db = MockDatabase()

    # Mock the cron manager to avoid scheduler startup
    with patch("langchain_triggers.app.CronTriggerManager") as mock_cron_class:
        mock_cron_instance = AsyncMock()
        mock_cron_instance.start = AsyncMock()
        mock_cron_instance.shutdown = AsyncMock()
        mock_cron_instance.reload_from_database = AsyncMock()
        mock_cron_class.return_value = mock_cron_instance

        server = TriggerServer(
            auth_handler=mock_auth_handler,
            database=mock_db,
        )
        server.cron_manager = mock_cron_instance

        # Trigger startup event
        await server.app.router.startup()

        yield server

        # Trigger shutdown event
        await server.app.router.shutdown()


@pytest.mark.asyncio
async def test_root_endpoint(trigger_server):
    """Test the root endpoint returns server info."""
    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Triggers Server"
        assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint(trigger_server):
    """Test the health endpoint."""
    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_triggers_endpoint(trigger_server):
    """Test listing trigger templates."""
    # Add a trigger template to the mock database
    await trigger_server.database.create_trigger_template(
        id="test_trigger",
        provider="test",
        name="Test Trigger",
        description="A test trigger",
        registration_schema={"type": "object"},
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get(
            "/v1/triggers", headers={"Authorization": "Bearer token1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "test_trigger"
        assert data["data"][0]["displayName"] == "Test Trigger"


@pytest.mark.asyncio
async def test_list_triggers_requires_auth(trigger_server):
    """Test that listing triggers requires authentication."""
    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # No Authorization header
        response = await client.get("/v1/triggers")

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_registrations_for_user(trigger_server):
    """Test listing registrations for a specific user."""
    # Create a registration
    await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={"test": "value"},
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer token1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["user_id"] == "test_user_token1"
        assert data["data"][0]["template_id"] == "test_trigger"


@pytest.mark.asyncio
async def test_link_agent_to_trigger(trigger_server):
    """Test linking an agent to a trigger registration."""
    # Create a registration first
    reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    registration_id = reg["id"]

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.post(
            f"/v1/triggers/registrations/{registration_id}/agents/agent_123",
            headers={"Authorization": "Bearer token1"},
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["agent_id"] == "agent_123"
        assert data["data"]["registration_id"] == registration_id


@pytest.mark.asyncio
async def test_unlink_agent_from_trigger(trigger_server):
    """Test unlinking an agent from a trigger registration."""
    # Create a registration and link an agent
    reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    registration_id = reg["id"]
    await trigger_server.database.link_agent_to_trigger(
        agent_id="agent_123",
        registration_id=registration_id,
        created_by="test_user_token1",
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.delete(
            f"/v1/triggers/registrations/{registration_id}/agents/agent_123",
            headers={"Authorization": "Bearer token1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_user_isolation(trigger_server):
    """Test that users can only see their own registrations."""
    # Create registrations for two different users
    await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    await trigger_server.database.create_trigger_registration(
        user_id="test_user_token2",
        template_id="test_trigger",
        resource={"url": "https://other.com"},
        metadata={},
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # User 1 should only see their registration
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer token1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["user_id"] == "test_user_token1"

        # User 2 should only see their registration
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer token2"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["user_id"] == "test_user_token2"


@pytest.mark.asyncio
async def test_client_metadata_storage(trigger_server):
    """Test that client-provided metadata is stored as client_metadata."""
    from langchain_triggers import TriggerRegistrationResult, TriggerTemplate

    async def test_registration_handler(user_id, auth_client, registration):
        return TriggerRegistrationResult(metadata={"handler_data": "from_handler"})

    test_trigger = TriggerTemplate(
        id="test_metadata_trigger",
        provider="test",
        name="Test Metadata",
        description="Tests metadata storage",
        registration_model=TestRegistration,
        registration_handler=test_registration_handler,
        trigger_handler=dummy_trigger_handler,
    )
    trigger_server.add_trigger(test_trigger)

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.post(
            "/v1/triggers/registrations",
            headers={"Authorization": "Bearer token1"},
            json={
                "type": "test_metadata_trigger",
                "name": "test",
                "metadata": {"tenant_id": "org-123"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify metadata in API response
        registration_id = data["data"]["id"]
        metadata = data["data"]["metadata"]
        assert metadata["client_metadata"]["tenant_id"] == "org-123"
        assert metadata["handler_data"] == "from_handler"

        # Verify metadata persisted in database
        db_registration = await trigger_server.database.get_trigger_registration(
            registration_id, user_id="test_user_token1"
        )
        assert db_registration is not None
        db_metadata = db_registration["metadata"]
        assert db_metadata["client_metadata"]["tenant_id"] == "org-123"
        assert db_metadata["handler_data"] == "from_handler"


@pytest.mark.asyncio
async def test_handler_cannot_use_client_metadata_key(trigger_server):
    """Test that handlers cannot use the reserved client_metadata key."""
    from langchain_triggers import TriggerRegistrationResult, TriggerTemplate

    async def bad_handler(user_id, auth_client, registration):
        # Handler tries to use reserved key
        return TriggerRegistrationResult(metadata={"client_metadata": "not allowed"})

    test_trigger = TriggerTemplate(
        id="test_bad_handler",
        provider="test",
        name="Test Bad Handler",
        description="Tests validation",
        registration_model=TestRegistration,
        registration_handler=bad_handler,
        trigger_handler=dummy_trigger_handler,
    )
    trigger_server.add_trigger(test_trigger)

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.post(
            "/v1/triggers/registrations",
            headers={"Authorization": "Bearer token1"},
            json={"type": "test_bad_handler", "name": "test"},
        )

        assert response.status_code == 500
        assert "client_metadata" in response.json()["detail"]
