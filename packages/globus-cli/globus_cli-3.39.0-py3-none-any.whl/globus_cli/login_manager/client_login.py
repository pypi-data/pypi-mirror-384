"""
Logic for using client identities with the Globus CLI
"""

from __future__ import annotations

import os

import globus_sdk


def _get_client_creds_from_env() -> tuple[str | None, str | None]:
    client_id = os.getenv("GLOBUS_CLI_CLIENT_ID")
    client_secret = os.getenv("GLOBUS_CLI_CLIENT_SECRET")
    return client_id, client_secret


def is_client_login() -> bool:
    """
    Return True if the correct env variables have been set to use a
    client identity with the Globus CLI
    """
    client_id, client_secret = _get_client_creds_from_env()

    if bool(client_id) ^ bool(client_secret):
        raise ValueError(
            "Both GLOBUS_CLI_CLIENT_ID and GLOBUS_CLI_CLIENT_SECRET must "
            "be set to use a client identity. Either set both environment "
            "variables, or unset them to use a normal login."
        )

    else:
        return bool(client_id) and bool(client_secret)


def get_client_login() -> globus_sdk.ConfidentialAppAuthClient:
    """
    Return the ConfidentialAppAuthClient for the client identity
    logged into the CLI
    """
    if not is_client_login():
        raise ValueError("No client is logged in")

    client_id, client_secret = _get_client_creds_from_env()

    return globus_sdk.ConfidentialAppAuthClient(
        client_id=str(client_id),
        client_secret=str(client_secret),
    )
