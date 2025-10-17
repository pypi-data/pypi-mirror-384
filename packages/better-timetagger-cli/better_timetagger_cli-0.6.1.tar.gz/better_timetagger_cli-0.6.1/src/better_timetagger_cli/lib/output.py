"""
### Output & Console

Utilities for terminal output, formatting, and user interaction.
"""

import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta
from typing import Any, NoReturn

from rich.box import SIMPLE
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from .records import get_tag_stats, get_total_time
from .types import Record

console = Console(highlight=False)
""" Console for default output """

stderr = Console(stderr=True, highlight=False)
""" Console for error output """


def abort(message: str | Group) -> NoReturn:
    """
    Abort the current command with a message.

    Args:
        message: The message to display before aborting.
    """
    style = "red" if isinstance(message, str) else None
    stderr.print(message, style=style)
    exit(1)


def open_in_editor(path: str, editor: str | None = None) -> None:
    """
    Open a file in the system's default editor, or a specified editor.

    Args:
        path: The path to the file to open.
        editor: The name or path of the editor executable. Default to system default.

    See:
        http://stackoverflow.com/a/72796/2271927
        http://superuser.com/questions/38984/linux-equivalent-command-for-open-command-on-mac-windows
    """
    if editor:
        subprocess.call((editor, path))

    elif sys.platform.startswith("darwin"):
        subprocess.call(("open", path))

    elif sys.platform.startswith("win"):
        if " " in path:
            subprocess.call(("start", "", path), shell=True)
        else:
            subprocess.call(("start", path), shell=True)

    elif sys.platform.startswith("linux"):
        try:
            subprocess.call(("xdg-open", path))
        except FileNotFoundError:
            subprocess.call((os.getenv("EDITOR", "nano"), path))

    else:
        stderr.print(f"\nUnsupported platform: {sys.platform}. Please open the file manually.", style="yellow")


def print_records(
    *records: tuple[Iterable[Record] | Record, str] | Iterable[Record] | Record,
    show_index: bool = False,
    show_keys: bool = False,
    record_status: dict[str, str | None] | None = None,
) -> None:
    """
    Display records in a table format using rich.

    Args:
        records: One or more lists of records to display. Optionally, provide along with a style expression as a tuple.
        show_index: If True, show the row index of each record. Useful for row-select prompts.
        show_keys: If True, show the key (unique identifier) of each record.
        record_status: A map of status annotations for each record key.
    """
    output = render_records(
        *records,
        show_index=show_index,
        show_keys=show_keys,
        record_status=record_status,
    )
    console.print(output)


def render_records(
    *records: tuple[Iterable[Record] | Record, str] | Iterable[Record] | Record,
    show_keys: bool = False,
    show_index: bool = False,
    record_status: dict[str, str | None] | None = None,
) -> Table:
    """
    Create a renderable rich object to display records.

    Args:
        records: One or more lists of records to display. Optionally, provide along with a style expression as a tuple.
        show_index: If True, show the row index of each record. Useful for row-select prompts.
        show_keys: If True, show the key (unique identifier) of each record.
        record_status: A map of status annotations for each record key.
    """
    table = Table(box=SIMPLE, min_width=65)

    # extra columns left
    if show_index:
        table.add_column(style="blue", no_wrap=True)
    if show_keys:
        table.add_column("Key", style="blue", no_wrap=True)

    # main columns
    table.add_column(style="cyan", no_wrap=True)
    table.add_column("Started", style="cyan")
    table.add_column("Stopped", style="cyan")
    table.add_column("Duration", style="bold magenta", no_wrap=True, justify="right")
    table.add_column("Description", style="green")

    # extra columns right
    if record_status:
        table.add_column("Status", style="yellow")

    # unpack records and associated styles
    for records_input in records:
        if isinstance(records_input, tuple) and isinstance(records_input[0], list | dict) and isinstance(records_input[1], str):
            _records, _style = records_input
        else:
            _records, _style = records_input, None
        if isinstance(_records, dict):
            _records = (_records,)

        # render records into table rows
        for i, r in enumerate(_records):
            columns: tuple[str, ...] = (
                readable_weekday(r["t1"]),
                readable_date_time(r["t1"]),
                readable_date_time(r["t2"]) if not r["_running"] else "...",
                readable_duration(r["_duration"]),
                highlight_tags_in_description(r["ds"]),
            )
            # extra columns left
            if show_keys:
                columns = (r["key"], *columns)
            if show_index:
                columns = (f"[blue]\\[{i}][/blue]" if i <= 0 else f"[dim]\\[{i}][/dim]", *columns)
            # extra columns right
            if record_status:
                columns = (*columns, f"[yellow]{record_status.get(r['key'], '')}[/yellow]")

            table.add_row(*columns, style=_style)

    return table


def render_summary(
    records: Sequence[Record],
    *,
    start_dt: int | datetime,
    end_dt: int | datetime,
) -> Table:
    """
    Create a rich object to display a summary of the records.

    Args:
        records: List of records to summarize.
        start_dt: Start date and time for the summary.
        end_dt: End date and time for the summary.

    Returns:
        Table: A rich table object containing the summary.
    """
    total = get_total_time(records, start_dt, end_dt)
    tag_stats = get_tag_stats(records)

    records_padding_length = max(len(str(len(records))), 5)

    table = Table(show_header=False, box=SIMPLE)
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="yellow", no_wrap=True)
    table.add_column(style="magenta", no_wrap=True)

    table.add_row(
        "Total:",
        styled_padded(len(records), records_padding_length),
        readable_duration(total),
        style="bold",
    )

    if tag_stats:
        for tag, (count, duration) in tag_stats.items():
            table.add_row(
                f"[green]{tag}:[/green]",
                styled_padded(count, records_padding_length),
                readable_duration(duration),
            )

    return table


def print_records_with_summary(
    records: Sequence[Record],
    *,
    summary: bool | None,
    start_dt: int | datetime,
    end_dt: int | datetime,
    show_index: bool = False,
    show_keys: bool = False,
    record_status: dict[str, str | None] | None = None,
) -> None:
    """
    Display records in a table format using rich.

    Args:
        records: List of records to display.
        summary: Flag to indicate whether to show summary, records or both.
        start_dt: Start date and time for the records.
        end_dt: End date and time for the records.
        show_index: If True, show the row index of each record. Useful for row-select prompts.
        show_keys: If True, show the key (unique identifier) of each record.
        record_status: A map of status annotations for each record key.
    """
    output = render_records_with_summary(
        records,
        summary=summary,
        start_dt=start_dt,
        end_dt=end_dt,
        show_index=show_index,
        show_keys=show_keys,
        record_status=record_status,
    )
    console.print(output)


def render_records_with_summary(
    records: Sequence[Record],
    *,
    summary: bool | None,
    start_dt: int | datetime,
    end_dt: int | datetime,
    show_index: bool = False,
    show_keys: bool = False,
    record_status: dict[str, str | None] | None = None,
) -> Group:
    """
    Render the output for the show command.

    Args:
        records: List of records to display.
        summary: Flag to indicate whether to show summary, records or both.
        start_dt: Start date and time for the records.
        end_dt: End date and time for the records.
        show_index: Flag to indicate whether to show row index.
        show_keys: Flag to indicate whether to show record keys.
        record_status: A map of status annotations for each record key.

    Returns:
        A rich console group containing the rendered output.
    """
    renderables = []

    if summary is not False:
        renderables.append(
            render_summary(
                records,
                start_dt=start_dt,
                end_dt=end_dt,
            )
        )

    if summary is not True:
        renderables.append(
            render_records(
                records,
                show_index=show_index,
                show_keys=show_keys,
                record_status=record_status,
            )
        )

    return Group(*renderables)


def readable_date_time(timestamp: int | float | datetime) -> str:
    """
    Turn a timestamp into a readable string.

    Args:
        timestamp: The timestamp to convert.

    Returns:
        A string representing the timestamp in date and time format.
    """
    from .config import get_config

    config = get_config()

    if isinstance(timestamp, datetime):
        value = timestamp
    else:
        value = datetime.fromtimestamp(timestamp)

    return value.strftime(config["datetime_format"])


def readable_weekday(timestamp: int | float | datetime) -> str:
    """
    Turn a timestamp into a readable string.

    Args:
        timestamp: The timestamp to convert.

    Returns:
        A string representing the timestamp as weekday
    """
    from .config import get_config

    config = get_config()

    if isinstance(timestamp, datetime):
        value = timestamp
    else:
        value = datetime.fromtimestamp(timestamp)

    return value.strftime(config["weekday_format"])


def readable_duration(duration: int | float | timedelta) -> str:
    """
    Turn a duration in seconds into a reabable string.

    Args:
        nsecs: The duration in seconds.

    Returns:
        A string representing the duration in 'HH:MM' format.
    """
    if isinstance(duration, timedelta):
        total_seconds = duration.total_seconds()
    else:
        total_seconds = duration

    hours, remainder = divmod(total_seconds, 60 * 60)
    minutes, _ = divmod(remainder, 60)

    output = ""
    if hours:
        output += f"{hours}h "
    output += f"{minutes:>2}m"

    return output.strip()


def styled_padded(value: Any, width: int = 5, *, style: str = "yellow", padding_style: str = "yellow dim", padding: str = "0") -> Text:
    value_str = str(value)
    len_padding = width - len(value_str)

    if len_padding <= 0:
        return Text(value_str, style=style)
    else:
        text = Text()
        text.append(padding * len_padding, style=padding_style)
        text.append(value_str, style=style)
        return text


def highlight_tags_in_description(description: str, style: str = "underline") -> str:
    """
    Highlight tags (marked by '#') in record descriptions.

    Args:
        description: The description string.

    Returns:
        A Text object with highlighted tags.
    """
    return re.sub(r"#\S+", lambda m: f"[{style}]{m.group(0)}[/{style}]", description.replace("\\", ""))
