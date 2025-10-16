import click
import globus_sdk

from globus_cli.login_manager import LoginManager, is_client_login
from globus_cli.parsing import command


def warnecho(msg: str) -> None:
    click.echo(click.style(msg, fg="yellow"), err=True)


_LOGOUT_EPILOG = """\
You are now successfully logged out of the Globus CLI.
You may also want to logout of any browser session you have with Globus:

  https://auth.globus.org/v2/web/logout

Before attempting any further CLI commands, you will have to login again using

  globus login
"""

_CLIENT_LOGOUT_EPILOG = """
You have successfully revoked all CLI tokens for this client identity,
however client identities are always considered logged in as they can request
new tokens at will.

You will need to unset the GLOBUS_CLI_CLIENT_ID and GLOBUS_CLI_CLIENT_SECRET
environment variables if you wish to prevent further use of the Globus CLI
with this client identity, or be able to run globus login for a normal login
flow.
"""


@command(
    "logout",
    short_help="Logout of the Globus CLI.",
    disable_options=["format", "map_http_status"],
)
@click.confirmation_option(
    prompt="Are you sure you want to logout?",
    help='Automatically say "yes" to all prompts',
)
@click.option(
    "--ignore-errors",
    help="Ignore any errors encountered during logout",
    is_flag=True,
    default=False,
)
@click.option("--delete-client", is_flag=True, hidden=True)
@LoginManager.requires_login()
def logout_command(
    login_manager: LoginManager,
    *,
    ignore_errors: bool,
    delete_client: bool,
) -> None:
    """
    Logout of the Globus CLI

    This command both removes all tokens used for authenticating the user from local
    storage and revokes them so that they cannot be used anymore globally.

    If an expected token cannot be found in local storage a warning will be raised
    as it is possible the token still exists and needs to be manually rescinded
    at https://auth.globus.org/consents for security.

    If the GLOBUS_PROFILE environment variable is set, you will log out of the account
    for the profile it's set to, and may still be logged in on other profiles,
    including the default profile. See the docs for details:

    https://docs.globus.org/cli/environment_variables/#profile_switching_with_globus_profile
    """
    # try to get the user's preferred username from userinfo
    # if an API error is raised, they probably are not logged in
    try:
        username = login_manager.get_auth_client().userinfo()["preferred_username"]
    except globus_sdk.AuthAPIError:
        warnecho(
            "Unable to lookup username. You may not be logged in. "
            "Attempting logout anyway...\n"
        )
        username = None
    if is_client_login():
        click.echo(f"Revoking all CLI tokens for {username}")
    else:
        click.echo(
            "Logging out of Globus{}\n".format(" as " + username if username else "")
        )

    # By default, preserve the templated client to avoid revocation of associated
    # consents (which can cause refresh token revocation, causing resources
    # associated with those tokens to become inoperable)
    # If the user has specifically requested a client deletion via hidden option,
    # then try to delete the templated credentialed client
    # ignoring failure by default (maybe creds are already invalidated or the
    # client was deleted)
    # Always skip for client logins, which don't use a templated client
    if delete_client and not is_client_login():
        try:
            login_manager.storage.delete_templated_client()
        except globus_sdk.AuthAPIError:
            if not ignore_errors:
                warnecho(
                    "Failure while deleting internal client. "
                    "Please try logging out again",
                )
                click.get_current_context().exit(1)
            else:
                warnecho(
                    "Warning: Failed to delete internal client. "
                    "Continuing... (--ignore-errors)",
                )

    # Attempt to revoke all tokens in storage; use the internal native client to ensure
    # we have a valid Auth client
    native_client = login_manager.storage.cli_native_client

    for rs, tokendata in login_manager.storage.adapter.get_by_resource_server().items():
        for tok_key in ("access_token", "refresh_token"):
            token = tokendata[tok_key]

            try:
                native_client.oauth2_revoke_token(token)
            # if we network error, revocation failed -- print message and abort so
            # that the user can try again when the network is working
            except globus_sdk.NetworkError:
                if not ignore_errors:
                    warnecho(
                        "Failed to reach Globus to revoke tokens. "
                        "Because we cannot revoke these tokens, cancelling logout",
                    )
                    click.get_current_context().exit(1)
                else:
                    warnecho(
                        "Warning: Failed to reach Globus to revoke tokens. "
                        "Continuing... (--ignore-errors)",
                    )

        login_manager.storage.adapter.remove_tokens_for_resource_server(rs)

    login_manager.storage.remove_well_known_config("auth_user_data")

    if is_client_login():
        click.echo(_CLIENT_LOGOUT_EPILOG)
    else:
        click.echo(_LOGOUT_EPILOG)
