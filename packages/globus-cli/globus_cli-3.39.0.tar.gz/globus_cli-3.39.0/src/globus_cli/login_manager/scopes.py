from __future__ import annotations

import typing as t

from globus_sdk.scopes import (
    AuthScopes,
    FlowsScopes,
    GCSCollectionScopeBuilder,
    GroupsScopes,
    Scope,
    SearchScopes,
    TimersScopes,
    TransferScopes,
)

from globus_cli.types import ServiceNameLiteral


def compute_timer_scope(
    *, data_access_collection_ids: t.Sequence[str] | None = None
) -> Scope:
    transfer_scope = Scope(TransferScopes.all)
    for cid in data_access_collection_ids or ():
        transfer_scope.add_dependency(
            Scope(GCSCollectionScopeBuilder(cid).data_access, optional=True)
        )

    timer_scope = Scope(TimersScopes.timer)
    timer_scope.add_dependency(transfer_scope)
    return timer_scope


# with no args, this builds
#   timer[transferAP[transfer]]
TIMER_SCOPE_WITH_DEPENDENCIES = compute_timer_scope()


class _ServiceRequirement(t.TypedDict):
    min_contract_version: int
    resource_server: str
    nice_server_name: str
    scopes: list[str | Scope]


class _CLIScopeRequirements(t.Dict[ServiceNameLiteral, _ServiceRequirement]):
    def __init__(self) -> None:
        self["auth"] = {
            "min_contract_version": 0,
            "resource_server": AuthScopes.resource_server,
            "nice_server_name": "Globus Auth",
            "scopes": [
                AuthScopes.openid,
                AuthScopes.profile,
                AuthScopes.email,
                AuthScopes.view_identity_set,
            ],
        }
        self["transfer"] = {
            "min_contract_version": 0,
            "resource_server": TransferScopes.resource_server,
            "nice_server_name": "Globus Transfer",
            "scopes": [
                TransferScopes.all,
            ],
        }
        self["groups"] = {
            "min_contract_version": 0,
            "resource_server": GroupsScopes.resource_server,
            "nice_server_name": "Globus Groups",
            "scopes": [
                GroupsScopes.all,
            ],
        }
        self["search"] = {
            "min_contract_version": 0,
            "resource_server": SearchScopes.resource_server,
            "nice_server_name": "Globus Search",
            "scopes": [
                SearchScopes.all,
            ],
        }
        self["timers"] = {
            "min_contract_version": 2,
            "resource_server": TimersScopes.resource_server,
            "nice_server_name": "Globus Timers",
            "scopes": [
                TIMER_SCOPE_WITH_DEPENDENCIES,
            ],
        }
        self["flows"] = {
            "min_contract_version": 0,
            "resource_server": FlowsScopes.resource_server,
            "nice_server_name": "Globus Flows",
            "scopes": [
                FlowsScopes.manage_flows,
                FlowsScopes.view_flows,
                FlowsScopes.run_status,
                FlowsScopes.run_manage,
            ],
        }

    def resource_servers(self) -> frozenset[str]:
        return frozenset(req["resource_server"] for req in self.values())

    def get_by_resource_server(self, rs_name: str) -> _ServiceRequirement:
        for req in self.values():
            if req["resource_server"] == rs_name:
                return req

        raise LookupError(f"{rs_name} was not a listed service requirement for the CLI")


CLI_SCOPE_REQUIREMENTS = _CLIScopeRequirements()

# the contract version number for the LoginManager's scope behavior
# this will be annotated on every token acquired and stored, in order to see what
# version we were at when we got a token
# it should be the max of the version numbers required by the various different
# services
CURRENT_SCOPE_CONTRACT_VERSION: t.Final[int] = 2
