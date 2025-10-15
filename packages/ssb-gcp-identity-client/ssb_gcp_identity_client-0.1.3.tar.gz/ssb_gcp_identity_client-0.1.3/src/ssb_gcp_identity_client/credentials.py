from pathlib import Path

from google.auth import identity_pool

STS_TOKEN_URL = "https://sts.googleapis.com/v1/token"  # noqa: S105
SUBJECT_TOKEN_TYPE_JWT = "urn:ietf:params:oauth:token-type:jwt"  # noqa: S105
AUDIENCE_TEMPLATE = "//iam.googleapis.com/projects/{project_number}/locations/global/workloadIdentityPools/{pool_id}/providers/{provider_id}"


def get_federated_credentials(
    project_number: str,
    workload_identity_pool_id: str,
    provider_id: str,
    maskinporten_token_file_path: str,
) -> identity_pool.Credentials:
    """Creates Workload Identity Federation credentials using a Maskinporten token.

    These credentials can be used to authenticate to Google Cloud services
    from environments outside Google Cloud (e.g., on-premise or other clouds)
    via Workload Identity Federation.

    Args:
        project_number: The numeric ID of the Google Cloud project which contains the Workload Identity Pool.
        workload_identity_pool_id: The Workload Identity Pool ID.
        provider_id: The Workload Identity Pool Provider ID.
        maskinporten_token_file_path: Path to a file containing a Maskinporten JWT. Can be relative or absolute; `~` will be expanded.

    Returns:
        `identity_pool.Credentials`: Federated credentials which can be used to create Google Cloud clients.

    Example:
        .. code-block:: python

            from google.cloud import storage
            from ssb_gcp_identity_client import get_federated_credentials

            creds = get_federated_credentials(
                project_number="1234567890",
                workload_identity_pool_id="my-pool",
                provider_id="maskinporten-provider",
                maskinporten_token_file_path="~/maskinporten/jwt.txt"
            )

            # Create a GCS client using these credentials
            client = storage.Client(credentials=creds)

            # List buckets in the project
            for bucket in client.list_buckets():
                print(bucket.name)
    """
    token_file = Path(maskinporten_token_file_path).expanduser().resolve()
    credentials_source = {"file": str(token_file)}

    audience = AUDIENCE_TEMPLATE.format(
        project_number=project_number,
        pool_id=workload_identity_pool_id,
        provider_id=provider_id,
    )

    return identity_pool.Credentials(  # type: ignore[no-untyped-call]
        audience=audience,
        subject_token_type=SUBJECT_TOKEN_TYPE_JWT,
        token_url=STS_TOKEN_URL,
        credential_source=credentials_source,
    )
