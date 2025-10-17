import click
import sys


@click.group()
def main():
    """
    ghoshell cli main group
    """
    pass


@main.command("help")
def main_help():
    """Print this help message."""
    _get_command_line_as_string()

    assert len(sys.argv) == 2  # This is always true, but let's assert anyway.
    # Pretend user typed 'streamlit --help' instead of 'streamlit help'.
    sys.argv[1] = "--help"
    main(prog_name="main")


def _get_command_line_as_string() -> str | None:
    """Print this help message."""
    import sys
    import subprocess
    parent = click.get_current_context().parent
    if parent is None:
        return None

    cmd_line_as_list = [parent.command_path]
    cmd_line_as_list.extend(sys.argv[1:])
    return subprocess.list2cmdline(cmd_line_as_list)
