from google.cloud import storage  # type: ignore[import-untyped]

from .credentials import get_federated_credentials


def get_federated_storage_client(
    project_number: str,
    workload_identity_pool_id: str,
    provider_id: str,
    maskinporten_token_file_path: str,
) -> storage.Client:
    """Creates a Google Cloud Storage client using Workload Identity Federation
    with a Maskinporten token.

    Args:
        project_number: The numeric ID of the Google Cloud project which contains the Workload Identity Pool.
        workload_identity_pool_id: The Workload Identity Pool ID.
        provider_id: The Workload Identity Pool Provider ID.
        maskinporten_token_file_path: Path to a file containing a Maskinporten JWT. Can be relative or absolute; `~` will be expanded.

    Returns:
        google.cloud.storage.Client: Storage client authenticated via Workload Identity Federation.

    Example:
        .. code-block:: python

            from ssb_gcp_identity_client import get_federated_storage_client

            client = get_federated_storage_client(
                project_number="1234567890",
                workload_identity_pool_id="my-pool",
                provider_id="maskinporten-provider",
                maskinporten_token_file_path="~/maskinporten/jwt.txt"
            )

            # List buckets in the project
            for bucket in client.list_buckets():
                print(bucket.name)
    """
    creds = get_federated_credentials(
        project_number,
        workload_identity_pool_id,
        provider_id,
        maskinporten_token_file_path,
    )
    return storage.Client(credentials=creds)
