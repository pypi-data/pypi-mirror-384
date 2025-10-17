"""ssb_gcp_identity_client package.

Provides utilities for creating GCP-clients authenticated to Google Cloud using
Workload Identity Federation with Maskinporten tokens.
"""

from .clients import get_federated_storage_client
from .credentials import get_federated_credentials

__all__ = [
    "get_federated_credentials",
    "get_federated_storage_client",
]
