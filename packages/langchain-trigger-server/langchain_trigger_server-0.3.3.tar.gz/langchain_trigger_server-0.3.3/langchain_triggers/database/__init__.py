"""Database module for trigger operations."""

from .interface import TriggerDatabaseInterface
from .supabase import SupabaseTriggerDatabase


def create_database(database_type: str, **kwargs) -> TriggerDatabaseInterface:
    """Factory function to create database implementation."""

    if database_type == "supabase":
        return SupabaseTriggerDatabase(**kwargs)
    else:
        raise ValueError(f"Unknown database type: {database_type}")


__all__ = ["TriggerDatabaseInterface", "SupabaseTriggerDatabase", "create_database"]
