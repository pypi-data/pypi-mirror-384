from globus_cli.parsing import group


@group(
    "flows",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "update": (".update", "update_command"),
        "validate": (".validate", "validate_command"),
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
        "show": (".show", "show_command"),
        "start": (".start", "start_command"),
        # "run" is a subgroup of commands.
        "run": (".run", "run_command"),
    },
)
def flows_command() -> None:
    """Interact with the Globus Flows service."""
