from globus_cli.parsing import group


@group(
    "timer",
    lazy_subcommands={
        "create": (".create", "create_command"),
        "delete": (".delete", "delete_command"),
        "list": (".list", "list_command"),
        "pause": (".pause", "pause_command"),
        "resume": (".resume", "resume_command"),
        "show": (".show", "show_command"),
    },
)
def timer_command() -> None:
    """Schedule and manage timers in Globus Timers."""
