"""Supabase implementation of trigger database interface."""

import base64
import hashlib
import logging
import os
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from supabase import create_client

from .interface import TriggerDatabaseInterface

logger = logging.getLogger(__name__)


class SupabaseTriggerDatabase(TriggerDatabaseInterface):
    """Supabase implementation of trigger database operations."""

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables are required"
            )

        self.client = create_client(self.supabase_url, self.supabase_key)

        # Get encryption key for API key decryption - required
        self.encryption_key = os.getenv("SECRETS_ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("SECRETS_ENCRYPTION_KEY environment variable is required")

        logger.info("Initialized SupabaseTriggerDatabase")

    def _decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt an encrypted secret using AES-256-GCM to match OAP Node.js implementation."""
        try:
            # Decode the base64 encoded encrypted data
            combined = base64.b64decode(encrypted_secret)

            # Constants from Node.js implementation
            IV_LENGTH = 12  # 96 bits
            TAG_LENGTH = 16  # 128 bits

            # Minimum length check
            if len(combined) < IV_LENGTH + TAG_LENGTH + 1:
                raise ValueError(
                    "Invalid encrypted secret format: too short or malformed"
                )

            # Extract IV, encrypted data, and auth tag
            iv = combined[:IV_LENGTH]
            tag = combined[-TAG_LENGTH:]
            encrypted_data = combined[IV_LENGTH:-TAG_LENGTH]

            # Derive key using SHA-256 hash (same as Node.js deriveKey function)
            key = hashlib.sha256(self.encryption_key.encode()).digest()

            # Create AES-GCM cipher
            cipher = Cipher(
                algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Decrypt the data
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

            return decrypted_data.decode("utf-8")
        except Exception as e:
            logger.error(f"Error decrypting secret: {e}")
            raise ValueError("Failed to decrypt API key")

    # ========== Trigger Templates ==========

    async def create_trigger_template(
        self,
        id: str,
        provider: str,
        name: str,
        description: str = None,
        registration_schema: dict = None,
    ) -> dict[str, Any] | None:
        """Create a new trigger template."""
        try:
            data = {
                "id": id,
                "provider": provider,
                "name": name,
                "description": description,
                "registration_schema": registration_schema or {},
            }

            response = self.client.table("trigger_templates").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            logger.error(f"Error creating trigger template: {e}")
            return None

    async def get_trigger_templates(self) -> list[dict[str, Any]]:
        """Get all available trigger templates."""
        try:
            response = self.client.table("trigger_templates").select("*").execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting trigger templates: {e}")
            return []

    async def get_trigger_template(self, id: str) -> dict[str, Any] | None:
        """Get a specific trigger template by ID."""
        try:
            response = (
                self.client.table("trigger_templates")
                .select("*")
                .eq("id", id)
                .single()
                .execute()
            )
            return response.data if response.data else None
        except Exception as e:
            # Don't log as error if template just doesn't exist (expected on first startup)
            if (
                "no rows returned" in str(e).lower()
                or "multiple (or no) rows returned" in str(e).lower()
            ):
                logger.debug(f"Trigger template {id} not found in database")
            else:
                logger.error(f"Error getting trigger template {id}: {e}")
            return None

    # ========== Trigger Registrations ==========

    async def create_trigger_registration(
        self, user_id: str, template_id: str, resource: dict, metadata: dict = None
    ) -> dict[str, Any] | None:
        """Create a new trigger registration for a user."""
        try:
            # Verify template exists
            template = await self.get_trigger_template(template_id)
            if not template:
                logger.error(f"Template not found for ID: {template_id}")
                return None

            data = {
                "user_id": user_id,
                "template_id": template_id,
                "resource": resource,
                "metadata": metadata or {},
                "status": "active",
            }

            response = self.client.table("trigger_registrations").insert(data).execute()
            return response.data[0] if response.data else None

        except Exception as e:
            logger.exception(f"Error creating trigger registration: {e}")
            return None

    async def get_user_trigger_registrations(
        self, user_id: str
    ) -> list[dict[str, Any]]:
        """Get all trigger registrations for a user."""
        try:
            response = (
                self.client.table("trigger_registrations")
                .select("""
                *,
                trigger_templates(id, name, description)
            """)
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            return response.data or []
        except Exception as e:
            logger.error(f"Error getting user trigger registrations: {e}")
            return []

    async def get_user_trigger_registrations_with_agents(
        self, user_id: str
    ) -> list[dict[str, Any]]:
        """Get all trigger registrations for a user with linked agents in a single query."""
        try:
            response = (
                self.client.table("trigger_registrations")
                .select("""
                *,
                trigger_templates(id, name, description),
                agent_trigger_links(agent_id)
            """)
                .eq("user_id", user_id)
                .order("created_at", desc=True)
                .execute()
            )

            # Process the results to extract linked agent IDs
            if response.data:
                for registration in response.data:
                    # Extract agent IDs from the agent_trigger_links
                    agent_links = registration.get("agent_trigger_links", [])
                    linked_agent_ids = [
                        link.get("agent_id")
                        for link in agent_links
                        if link.get("agent_id")
                    ]
                    registration["linked_agent_ids"] = linked_agent_ids

                    # Clean up the raw agent_trigger_links data as it's no longer needed
                    registration.pop("agent_trigger_links", None)

            return response.data or []
        except Exception as e:
            logger.error(f"Error getting user trigger registrations with agents: {e}")
            return []

    async def get_trigger_registration(
        self, registration_id: str, user_id: str = None
    ) -> dict[str, Any] | None:
        """Get a specific trigger registration."""
        try:
            query = (
                self.client.table("trigger_registrations")
                .select("*")
                .eq("id", registration_id)
            )
            if user_id:
                query = query.eq("user_id", user_id)

            response = query.single().execute()
            return response.data if response.data else None
        except Exception as e:
            logger.error(f"Error getting trigger registration {registration_id}: {e}")
            return None

    async def update_trigger_metadata(
        self, registration_id: str, metadata_updates: dict, user_id: str = None
    ) -> bool:
        """Update metadata for a trigger registration."""
        try:
            # Get current registration to merge metadata
            current = await self.get_trigger_registration(registration_id, user_id)
            if not current:
                return False

            # Merge existing metadata with updates
            current_metadata = current.get("metadata", {})
            updated_metadata = {**current_metadata, **metadata_updates}

            query = (
                self.client.table("trigger_registrations")
                .update({"metadata": updated_metadata, "updated_at": "NOW()"})
                .eq("id", registration_id)
            )

            if user_id:
                query = query.eq("user_id", user_id)

            response = query.execute()
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error updating trigger metadata: {e}")
            return False

    async def delete_trigger_registration(
        self, registration_id: str, user_id: str = None
    ) -> bool:
        """Delete a trigger registration."""
        try:
            query = (
                self.client.table("trigger_registrations")
                .delete()
                .eq("id", registration_id)
            )
            if user_id:
                query = query.eq("user_id", user_id)

            query.execute()
            return True  # Delete operations don't return data

        except Exception as e:
            logger.error(f"Error deleting trigger registration: {e}")
            return False

    async def find_registration_by_resource(
        self, template_id: str, resource_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find trigger registration by matching resource data."""
        try:
            # Build query to match against trigger_registrations with template_id filter
            query = (
                self.client.table("trigger_registrations")
                .select("*, trigger_templates(id, name, description)")
                .eq("template_id", template_id)
            )

            # Add resource field matches
            for field, value in resource_data.items():
                query = query.eq(f"resource->>{field}", value)

            response = query.execute()

            if response.data:
                return response.data[0]  # Return first match
            return None

        except Exception as e:
            logger.error(f"Error finding registration by resource: {e}")
            return None

    async def find_user_registration_by_resource(
        self, user_id: str, template_id: str, resource_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find trigger registration by matching resource data for a specific user."""
        try:
            # Build query to match against trigger_registrations with template_id and user_id filter
            query = (
                self.client.table("trigger_registrations")
                .select("*, trigger_templates(id, name, description)")
                .eq("template_id", template_id)
                .eq("user_id", user_id)
            )

            # Add resource field matches
            for field, value in resource_data.items():
                query = query.eq(f"resource->>{field}", value)

            response = query.execute()

            if response.data:
                return response.data[0]  # Return first match
            return None

        except Exception as e:
            logger.error(f"Error finding user registration by resource: {e}")
            return None

    async def get_all_registrations(self, template_id: str) -> list[dict[str, Any]]:
        """Get all registrations for a specific trigger template."""
        try:
            response = (
                self.client.table("trigger_registrations")
                .select("*, trigger_templates(id, name, description)")
                .eq("template_id", template_id)
                .execute()
            )

            return response.data or []
        except Exception as e:
            logger.error(
                f"Error getting all registrations for template {template_id}: {e}"
            )
            return []

    # ========== Agent-Trigger Links ==========

    async def link_agent_to_trigger(
        self,
        agent_id: str,
        registration_id: str,
        created_by: str,
        field_selection: dict[str, bool] | None = None,
    ) -> bool:
        """Link an agent to a trigger registration with optional field selection."""
        try:
            data = {
                "agent_id": agent_id,
                "registration_id": registration_id,
                "created_by": created_by,
                "field_selection": field_selection,
            }

            response = self.client.table("agent_trigger_links").insert(data).execute()
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error linking agent to trigger: {e}")
            return False

    async def unlink_agent_from_trigger(
        self, agent_id: str, registration_id: str
    ) -> bool:
        """Unlink an agent from a trigger registration."""
        try:
            (
                self.client.table("agent_trigger_links")
                .delete()
                .eq("agent_id", agent_id)
                .eq("registration_id", registration_id)
                .execute()
            )

            return True  # Delete operations don't return data

        except Exception as e:
            logger.error(f"Error unlinking agent from trigger: {e}")
            return False

    async def get_agents_for_trigger(
        self, registration_id: str
    ) -> list[dict[str, Any]]:
        """Get all agent links for a trigger registration with field_selection."""
        try:
            response = (
                self.client.table("agent_trigger_links")
                .select("agent_id, field_selection")
                .eq("registration_id", registration_id)
                .execute()
            )

            return response.data or []

        except Exception as e:
            logger.error(f"Error getting agents for trigger: {e}")
            return []

    async def get_triggers_for_agent(self, agent_id: str) -> list[dict[str, Any]]:
        """Get all trigger registrations linked to an agent."""
        try:
            response = (
                self.client.table("agent_trigger_links")
                .select("""
                registration_id,
                trigger_registrations(
                    *,
                    trigger_templates(id, name, description)
                )
            """)
                .eq("agent_id", agent_id)
                .execute()
            )

            return [row["trigger_registrations"] for row in response.data or []]

        except Exception as e:
            logger.error(f"Error getting triggers for agent: {e}")
            return []

    # ========== Helper Methods ==========

    async def get_user_from_token(self, token: str) -> str | None:
        """Extract user ID from JWT token via Supabase auth."""
        try:
            client = self._create_user_client(token)
            response = client.auth.get_user(token)
            return response.user.id if response.user else None
        except Exception as e:
            logger.error(f"Error getting user from token: {e}")
            return None

    async def get_user_by_email(self, email: str) -> str | None:
        """Get user ID by email from trigger registrations."""
        try:
            response = (
                self.client.table("trigger_registrations")
                .select("user_id")
                .eq("resource->>email", email)
                .limit(1)
                .execute()
            )

            return response.data[0]["user_id"] if response.data else None

        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
