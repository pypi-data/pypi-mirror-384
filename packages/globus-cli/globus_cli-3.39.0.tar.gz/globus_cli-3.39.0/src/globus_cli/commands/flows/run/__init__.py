from globus_cli.parsing import group


@group(
    "run",
    lazy_subcommands={
        "show": (".show", "show_command"),
        "show-definition": (".show_definition", "show_definition_command"),
        "show-logs": (".show_logs", "show_logs_command"),
        "list": (".list", "list_command"),
        "update": (".update", "update_command"),
        "delete": (".delete", "delete_command"),
        "resume": (".resume", "resume_command"),
        "cancel": (".cancel", "cancel_command"),
    },
)
def run_command() -> None:
    """Interact with a run in the Globus Flows service."""
