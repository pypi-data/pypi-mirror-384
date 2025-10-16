from __future__ import annotations

import uuid

import click

from globus_cli.constants import ExplicitNullType
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import ENDPOINT_PLUS_REQPATH, command, endpointish_params
from globus_cli.parsing.shared_options import activity_notifications_option
from globus_cli.termio import Field, display

from ._common import deprecated_verify_option


@command("guest", short_help="Create a new Guest Collection on GCP.")
@endpointish_params.create(
    name="collection",
    keyword_style="string",
    skip=("user_message", "user_message_link", "public"),
)
@click.argument("HOST_GCP_PATH", type=ENDPOINT_PLUS_REQPATH)
@deprecated_verify_option
@activity_notifications_option("GCP")
@LoginManager.requires_login("transfer")
def guest_command(
    login_manager: LoginManager,
    *,
    display_name: str,
    host_gcp_path: tuple[uuid.UUID, str],
    contact_email: str | None | ExplicitNullType,
    contact_info: str | None | ExplicitNullType,
    default_directory: str | None | ExplicitNullType,
    department: str | None | ExplicitNullType,
    description: str | None | ExplicitNullType,
    force_encryption: bool | None,
    info_link: str | None | ExplicitNullType,
    keywords: str | None,
    organization: str | None | ExplicitNullType,
    verify: dict[str, bool],
    disable_verify: bool | None,
    activity_notifications: dict[str, list[str]] | None | ExplicitNullType,
) -> None:
    """
    Create a new Guest Collection on a Globus Connect Personal Endpoint

    The host ID and a path to the root for the Guest Collection are required.
    """
    from globus_cli.services.transfer import assemble_generic_doc

    if disable_verify is not None:
        verify["disable_verify"] = disable_verify

    transfer_client = login_manager.get_transfer_client()

    # build the endpoint document to submit
    host_endpoint_id, host_path = host_gcp_path
    ep_doc = assemble_generic_doc(
        "shared_endpoint",
        host_endpoint=host_endpoint_id,
        host_path=host_path,
        display_name=display_name,
        description=description,
        info_link=info_link,
        contact_info=contact_info,
        contact_email=contact_email,
        organization=organization,
        department=department,
        keywords=keywords,
        default_directory=default_directory,
        force_encryption=force_encryption,
        guest_collection_activity_notification_policy=activity_notifications,
        **verify,
    )

    res = transfer_client.create_shared_endpoint(ep_doc)

    # output
    display(
        res,
        fields=[Field("Message", "message"), Field("Collection ID", "id")],
        text_mode=display.RECORD,
    )
