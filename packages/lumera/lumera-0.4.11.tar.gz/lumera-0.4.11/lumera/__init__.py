"""
Lumera Agent SDK

This SDK provides helpers for agents running within the Lumera Notebook environment
to interact with the Lumera API and define dynamic user interfaces.
"""

# Import key functions from submodules to make them available at the top level.
from .sdk import (
    CollectionField,
    LumeraAPIError,
    RecordNotUniqueError,
    create_collection,
    create_record,
    delete_collection,
    delete_record,
    get_access_token,
    get_collection,
    get_google_access_token,
    get_record,
    get_record_by_external_id,
    list_collections,
    list_records,
    log_timed,
    run_agent,
    save_to_lumera,
    update_collection,
    update_record,
    upsert_record,
)

# Define what `from lumera import *` imports.
__all__ = [
    "get_access_token",
    "save_to_lumera",
    "get_google_access_token",  # Kept for backwards compatibility
    "log_timed",
    "list_collections",
    "get_collection",
    "create_collection",
    "update_collection",
    "delete_collection",
    "list_records",
    "get_record",
    "get_record_by_external_id",
    "run_agent",
    "create_record",
    "update_record",
    "upsert_record",
    "delete_record",
    "CollectionField",
    "LumeraAPIError",
    "RecordNotUniqueError",
]
