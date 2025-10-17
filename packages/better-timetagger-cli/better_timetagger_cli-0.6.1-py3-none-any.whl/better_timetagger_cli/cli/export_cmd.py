from typing import Literal

import click

from better_timetagger_cli.lib.api import get_records, get_running_records
from better_timetagger_cli.lib.cli import AliasedCommand
from better_timetagger_cli.lib.csv import records_to_csv
from better_timetagger_cli.lib.output import abort, console
from better_timetagger_cli.lib.parsing import parse_start_end, tags_callback
from better_timetagger_cli.lib.records import round_records


@click.command(
    "export",
    aliases=("csv",),
    cls=AliasedCommand,
)
@click.argument(
    "tags",
    type=click.STRING,
    nargs=-1,
    callback=tags_callback,
)
@click.option(
    "-o",
    "--output",
    "file",
    type=click.File("w"),
    help="Output file. If not specified, print the output to stdout.",
)
@click.option(
    "-s",
    "--start",
    type=click.STRING,
    help="Include only records later than this time. Supports natural language.",
)
@click.option(
    "-e",
    "--end",
    type=click.STRING,
    help="Include only records earlier than this time. Supports natural language.",
)
@click.option(
    "-r",
    "--round",
    is_flag=False,
    flag_value=5,
    type=click.IntRange(min=1),
    help="Round record times to a regular interval in minutes. Specify a value to round to that number of minutes (e.g., '--round 10' for 10 minutes). If used as a flag without a value (e.g., '--round'), defaults to 5 minutes.",
)
@click.option(
    "-H",
    "--hidden",
    is_flag=True,
    help="Include only hidden (i.e. removed) records in the output.",
)
@click.option(
    "-R",
    "--running",
    is_flag=True,
    help="Include only running records in the output.",
)
@click.option(
    "-x",
    "--match",
    "tags_match",
    type=click.Choice(["any", "all"]),
    default="any",
    help="Tag matching mode. Include records that match either 'any' or 'all' tags. Default: any.",
)
def export_cmd(
    tags: list[str],
    file: click.File | None,
    start: str | None,
    end: str | None,
    round: int,
    hidden: bool,
    running: bool,
    tags_match: Literal["any", "all"],
) -> None:
    """
    Export records to CSV format.

    If no tags are provided, all tasks within the selected time frame will be included.
    Specify one or more tags to include only matching tasks.
    Tags can be entered without the leading hashtag '#'.

    The parameters '--start' and '--end' support natural language to specify date and time.
    You can use phrases like 'yesterday', 'June 11', '5 minutes ago', or '05/12 3pm'.
    """
    if running and (start or end):
        abort("The '--running' option cannot be used with '--start' or '--end'.")

    start_dt, end_dt = parse_start_end(start, end)

    if not running:
        records = get_records(
            start_dt,
            end_dt,
            tags=tags,
            tags_match=tags_match,
            sort_by="t1",
            sort_reverse=False,
            hidden=hidden,
        )["records"]
    else:
        records = get_running_records(
            tags=tags,
            tags_match=tags_match,
            sort_by="t1",
            sort_reverse=False,
            hidden=hidden,
        )["records"]

    if not records:
        abort("No records found.")

    if round:
        records = round_records(records, round)

    csv = records_to_csv(records)

    click.echo(csv, file=file)  # type: ignore[arg-type]

    if file is not None:
        console.print(f"\n[green]Exported {len(records)} records to '{file.name}'.[/green]\n")
