import click

from better_timetagger_cli.lib.api import get_updates, put_records
from better_timetagger_cli.lib.cli import AliasedCommand
from better_timetagger_cli.lib.output import abort, print_records
from better_timetagger_cli.lib.timestamps import now_timestamp


@click.command(
    "restore",
    aliases=("unhide",),
    cls=AliasedCommand,
)
@click.argument(
    "keys",
    type=click.STRING,
    nargs=-1,
)
def restore_cmd(
    keys: list[str],
) -> None:
    """
    Unhide TimeTagger records.

    Specify one or more record keys to restore.
    To list hidden records and their keys, use 't show --hidden --show-keys'.
    """
    now = now_timestamp()
    if not keys:
        abort("No keys provided. Specify at least one task key to remove.")

    records = get_updates()["records"]
    restored_records = []

    for r in records:
        if r["key"] in keys:
            r["ds"] = r["ds"].replace("HIDDEN ", "").strip()
            r["mt"] = now
            restored_records.append(r)

    put_records(restored_records)
    print_records((restored_records, "green"), show_keys=True)
