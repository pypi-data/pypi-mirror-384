from __future__ import annotations

import datetime
import email.utils
import typing as t

import click
import globus_sdk
from globus_sdk.scopes import Scope

from .storage import CLIStorage


def do_link_auth_flow(
    storage: CLIStorage,
    scopes: str | t.Sequence[str | Scope],
    *,
    session_params: dict[str, str] | None = None,
) -> bool:
    """
    Prompts the user with a link to authenticate with globus auth
    and authorize the CLI to act on their behalf.
    """
    session_params = session_params or {}

    # get the ConfidentialApp client object
    auth_client = storage.cli_confidential_client

    # start the Confidential App Grant flow
    auth_client.oauth2_start_flow(
        redirect_uri=auth_client.base_url + "v2/web/auth-code",
        refresh_tokens=True,
        requested_scopes=scopes,
    )

    # prompt
    query_params = {"prompt": "login"}
    query_params.update(session_params)
    linkprompt = "Please authenticate with Globus here"
    click.echo(
        "{0}:\n{1}\n{2}\n{1}\n".format(
            linkprompt,
            "-" * len(linkprompt),
            auth_client.oauth2_get_authorize_url(query_params=query_params),
        )
    )

    # come back with auth code
    auth_code = click.prompt("Enter the resulting Authorization Code here").strip()

    # finish auth flow
    exchange_code_and_store(storage, auth_client, auth_code)
    return True


def do_local_server_auth_flow(
    storage: CLIStorage,
    scopes: str | t.Sequence[str | Scope],
    *,
    session_params: dict[str, str] | None = None,
) -> bool:
    """
    Starts a local http server, opens a browser to have the user authenticate,
    and gets the code redirected to the server (no copy and pasting required)
    """
    import webbrowser

    from .local_server import LocalServerError, start_local_server

    session_params = session_params or {}

    # start local server and create matching redirect_uri
    with start_local_server(listen=("127.0.0.1", 0)) as server:
        _, port = server.socket.getsockname()
        redirect_uri = f"http://localhost:{port}"

        # get the ConfidentialApp client object and start a flow
        auth_client = storage.cli_confidential_client
        auth_client.oauth2_start_flow(
            refresh_tokens=True,
            redirect_uri=redirect_uri,
            requested_scopes=scopes,
        )
        query_params = {"prompt": "login"}
        query_params.update(session_params)
        url = auth_client.oauth2_get_authorize_url(query_params=query_params)

        # open web-browser for user to log in, get auth code
        webbrowser.open(url, new=1)
        auth_code = server.wait_for_code()

    if isinstance(auth_code, LocalServerError):
        click.echo(f"Authorization failed: {auth_code}", err=True)
        click.get_current_context().exit(1)
    elif isinstance(auth_code, BaseException):
        click.echo(
            f"Authorization failed with unexpected error:\n{auth_code}",
            err=True,
        )
        click.get_current_context().exit(1)

    # finish auth flow and return true
    exchange_code_and_store(storage, auth_client, auth_code)
    return True


def exchange_code_and_store(
    storage: CLIStorage,
    auth_client: globus_sdk.ConfidentialAppAuthClient | globus_sdk.NativeAppAuthClient,
    auth_code: str,
) -> None:
    """
    Finishes auth flow after code is gotten from command line or local server.
    Exchanges code for tokens and stores them.

    A user may have a different identity this time than what they previously logged in
    as, so to secure incremental auth flows, if the new tokens don't match the previous
    identity we revoke them and instruct the user to logout before continuing.
    """
    import jwt.exceptions

    tkn = auth_client.oauth2_exchange_code_for_tokens(auth_code)

    # use a leeway of 300s
    #
    # valuable inputs to this number:
    # - expected clock drift per day (6s for a bad clock)
    # - Windows time sync interval (64s)
    # - Windows' stated goal of meeting the Kerberos 5 clock skew requirement (5m)
    # - ntp panic threshold (1000s of drift)
    # - the knowledge that VM clocks typically run slower and may skew significantly
    #
    # NTP panic is probably extreme -- if the system is in that state, we should
    # probably not consider the clock to be okay
    #
    # Windows sync interval of 64s led us to use 64s as the leeway in the past, but
    # we still saw at least one user run into this, which made us consider increasing it
    #
    # The Kerberos 5 requirement is therefore a winning choice. It's another authn
    # system's decision about un/acceptable skew, and therefore a good outside boundary
    # for what's likely to be seen in the wild on "normal" systems.
    try:
        sub_new = tkn.decode_id_token(jwt_params={"leeway": 300})["sub"]
    except jwt.exceptions.ImmatureSignatureError:
        # when an error is encountered, check for significant clock skew vs the
        # response's "Date" header
        response_delta = _response_clock_delta(tkn)
        if response_delta:
            click.echo(
                "WARNING: The server response dated itself "
                f"{response_delta:.2f} seconds out of sync with the local clock. "
                "This may indicate a clock skew problem.",
                err=True,
            )
        raise
    auth_user_data = storage.read_well_known_config("auth_user_data")
    if auth_user_data and sub_new != auth_user_data.get("sub"):
        try:
            for tokens in tkn.by_resource_server.values():
                auth_client.oauth2_revoke_token(tokens["access_token"])
                auth_client.oauth2_revoke_token(tokens["refresh_token"])
        finally:
            click.echo(
                "Authorization failed: tried to login with an account that didn't "
                "match existing credentials. If you meant to do this, first `globus "
                "logout`, then try again. ",
                err=True,
            )
        click.get_current_context().exit(1)
    if not auth_user_data:
        storage.store_well_known_config("auth_user_data", {"sub": sub_new})
    storage.store(tkn)


def _response_clock_delta(response: globus_sdk.GlobusHTTPResponse) -> float | None:
    """
    Get the "Date" header from a GlobusHTTPResponse, parse it as a datetime, and then
    compare that against the current time. Return the delta in seconds.

    If the "Date" cannot be parsed or isn't present, return None.

    This uses `email.utils` to parse the date, which is the stdlib's available RFC 2822
    parser.
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc)

    response_date_str = response.headers.get("Date")
    if not response_date_str:  # not present
        return None

    try:
        response_date = email.utils.parsedate_to_datetime(response_date_str)
    except (ValueError, TypeError):  # failed to parse
        return None

    return abs((now - response_date).total_seconds())
