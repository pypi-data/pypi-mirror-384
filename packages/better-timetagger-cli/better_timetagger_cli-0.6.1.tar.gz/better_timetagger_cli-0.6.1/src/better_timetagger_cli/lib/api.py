"""
### API Communication

Functions that handle communication with the TimeTagger API.
"""

import json
from collections.abc import Generator
from datetime import datetime, timedelta
from time import sleep
from typing import Literal, cast

import requests

from .config import get_config
from .output import abort
from .records import merge_by_key, post_process_records
from .types import GetRecordsResponse, GetSettingsResponse, GetUpdatesResponse, PutRecordsResponse, PutSettingsResponse, Record, Settings


def api_request(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    body: list | dict | None = None,
) -> dict:
    """
    Execute an authenticated request to the Timetagger API.

    Args:
        method: The HTTP method to use.
        path: The API endpoint path.
        body: The request body to send. Defaults to None.

    Returns:
        The JSON-decoded response from the API.
    """
    config = get_config()

    try:
        url = config["base_url"].rstrip("/") + "/api/v2/" + path.lstrip("/")
        token = config["api_token"].strip()
        ssl_verify = config["ssl_verify"]

        headers = {"authtoken": token}
        response = requests.request(method.upper(), url, json=body, headers=headers, verify=ssl_verify)

    except Exception as e:
        abort(f"API request failed: {e.__class__.__name__}\n[dim]{e}[/dim]")

    if response.status_code != 200:
        response_text = response.text
        try:
            response_text = json.dumps(response.json(), indent=2)
        except json.JSONDecodeError:  # pragma: no cover
            pass
        abort(f"API request failed with status code: {response.status_code}\n[dim]{response_text}[/dim]")

    return response.json()


def get_records(
    start: int | datetime,
    end: int | datetime,
    *,
    include_partial_match: bool = True,
    tags: list[str] | None = None,
    tags_match: Literal["any", "all"] = "any",
    sort_by: Literal["t1", "t2", "st", "mt", "ds"] = "t2",
    sort_reverse: bool = True,
    hidden: bool = False,
    running: bool = False,
) -> GetRecordsResponse:
    """
    Calls TimeTagger API using `GET /records?timerange={start}-{end}` and returns the response.

    Args:
        start: The start timestamp to get records from.
        end: The end timestamp to get records until.
        include_partial: Whether to include partial matches, i.e. records that are not fully contained in the range. Defaults to True.
        tags: A list of tags to filter records by. Defaults to None.
        tags_match: The mode to match tags. Can be "any" or "all". Defaults to "any".
        sort_by: The field to sort the records by. Can be "t1", "t2", "st", "mt", or "ds". Defaults to "t2".
        sort_reverse: Whether to sort in reverse order. Defaults to True.
        hidden: Whether to include hidden (i.e. deleted) records. Defaults to False.
        running: If True, only return currently running records (i.e. records where t1 == t2). Defaults to False.

    Returns:
        A dictionary containing the records from the API.
    """
    if isinstance(start, datetime):
        start = int(start.timestamp())
    if isinstance(end, datetime):
        end = int(end.timestamp())

    t1 = min(start, end) if include_partial_match else max(start, end)
    t2 = max(start, end) if include_partial_match else min(start, end)
    response = api_request("GET", f"records?timerange={t1}-{t2}")

    response["records"] = post_process_records(
        response["records"],
        tags=tags,
        tags_match=tags_match,
        sort_by=sort_by,
        sort_reverse=sort_reverse,
        hidden=hidden,
        running=running,
    )

    return cast(GetRecordsResponse, response)


def get_running_records(
    *,
    tags: list[str] | None = None,
    tags_match: Literal["any", "all"] = "any",
    sort_by: Literal["t1", "t2", "st", "mt", "ds"] = "t2",
    sort_reverse: bool = True,
    hidden: bool = False,
) -> GetRecordsResponse | GetRecordsResponse:
    """
    Searches for currently running records in the TimeTagger API.

    Depending on the configuration, this will search either all existing records,
    or limit the search to a recent time window to optimize performance.

    Args:
        tags: A list of tags to filter records by. Defaults to None.
        tags_match: The mode to match tags. Can be "any" or "all". Defaults to "any".
        sort_by: The field to sort the records by. Can be "t1", "t2", "st", "mt", or "ds". Defaults to "t2".
        sort_reverse: Whether to sort in reverse order. Defaults to True.
        hidden: Whether to include hidden (i.e. deleted) records. Defaults to False.
        running: If True, only return currently running records (i.e. records where t1 == t2). Defaults to False.

    Returns:
        A dictionary containing the running records from the API.
    """
    config = get_config()

    # search window disabled, search all records for running state
    if config["running_records_search_window"] < 0:
        return get_updates(
            tags=tags,
            tags_match=tags_match,
            sort_by=sort_by,
            sort_reverse=sort_reverse,
            hidden=hidden,
            running=True,
        )

    # search window enabled, search records within the configured time range for running state
    else:
        return get_records(
            start=datetime.now() - timedelta(weeks=config["running_records_search_window"]),
            end=datetime.now() + timedelta(days=1),
            include_partial_match=True,
            tags=tags,
            tags_match=tags_match,
            sort_by=sort_by,
            sort_reverse=sort_reverse,
            hidden=hidden,
            running=True,
        )


def put_records(*records: Record | list[Record]) -> PutRecordsResponse:
    """
    Calls TimeTagger API using `PUT /records` and returns response.

    Args:
        records: A list of records to put.

    Returns:
        A dictionary containing the response from the API.
    """
    records_flattened = []
    for record in records:
        if isinstance(record, list):
            records_flattened.extend(record)
        else:
            records_flattened.append(record)

    response = api_request("PUT", "records", records_flattened)
    return cast(PutRecordsResponse, response)


def get_settings(settings: list[Settings]) -> GetSettingsResponse:
    """
    Calls TimeTagger API using `GET /settings` and returns the response.

    Returns:
        A dictionary containing the settings from the API.
    """
    response = api_request("GET", "settings", settings)
    return cast(GetSettingsResponse, response)


def put_settings(settings: dict) -> PutSettingsResponse:
    """
    Calls TimeTagger API using `PUT /settings` and returns response.

    Args:
        settings: A dictionary containing the settings to put.

    Returns:
        A dictionary containing the response from the API.
    """
    response = api_request("PUT", "settings", settings)
    return cast(PutSettingsResponse, response)


def get_updates(
    since: int | datetime = 0,
    *,
    tags: list[str] | None = None,
    tags_match: Literal["any", "all"] = "any",
    sort_by: Literal["t1", "t2", "st", "mt", "ds"] = "t2",
    sort_reverse: bool = True,
    hidden: bool = False,
    running: bool = False,
) -> GetUpdatesResponse:
    """
    Calls TimeTagger API using `GET /updates?since={since}` and returns the response.

    Args:
        since: The timestamp to get updates since. Defaults to 0. Should typically use the last call's `server_time` value.
        tags: A list of tags to filter records by. Defaults to None.
        tags_match: The mode to match tags. Can be "any" or "all". Defaults to "any".
        sort_by: The field to sort the records by. Can be "t1", "t2", "st", "mt", or "ds". Defaults to "t2".
        sort_reverse: Whether to sort in reverse order. Defaults to True.
        hidden: Whether to include hidden (i.e. deleted) records. Defaults to False.
        running: If True, only return currently running records (i.e. records where t1 == t2). Defaults to False.

    Returns:
        A dictionary containing the updates from the API.
    """
    if isinstance(since, datetime):
        since = int(since.timestamp())

    response = api_request("GET", f"updates?since={since}")

    response["records"] = post_process_records(
        response["records"],
        tags=tags,
        tags_match=tags_match,
        sort_by=sort_by,
        sort_reverse=sort_reverse,
        hidden=hidden,
        running=running,
    )

    return cast(GetUpdatesResponse, response)


def continuous_updates(
    since: int | datetime = 0,
    *,
    delay: int = 5,
    tags: list[str] | None = None,
    tags_match: Literal["any", "all"] = "any",
    sort_by: Literal["t1", "t2", "st", "mt", "ds"] = "t2",
    sort_reverse: bool = True,
    hidden: bool = False,
    running: bool = False,
) -> Generator[GetUpdatesResponse, None]:
    """
    Generator that continually polls TimeTagger API using `GET /updates?since={since}`, using the last call's `server_time` value as the new `since` value.

    This allows continuous monitoring of server updates.

    Args:
        since: The timestamp to get updates since. Defaults to 0. Should typically use the last call's `server_time` value.
        delay: The minimul delay in seconds between requests. Defaults to 2 second.
        tags: A list of tags to filter records by. Defaults to None.
        tags_match: The mode to match tags. Can be "any" or "all". Defaults to "any".
        sort_by: The field to sort the records by. Can be "t1", "t2", "st", "mt", or "ds". Defaults to "t2".
        sort_reverse: Whether to sort in reverse order. Defaults to True.
        hidden: Whether to include hidden (i.e. deleted) records. Defaults to False.
        running: If True, only return currently running records (i.e. records where t1 == t2). Defaults to False.

    Yields:
        A dictionary containing the updates from the API.
    """
    response_cache: GetUpdatesResponse = {}  # type: ignore[typeddict-item]

    while True:
        updates = get_updates(
            response_cache.get("server_time", since),
            tags=tags,
            tags_match=tags_match,
            sort_by=sort_by,
            sort_reverse=sort_reverse,
            hidden=hidden,
            # Must set this to False, otherwise we never notice when a record
            # that's previously been running is stopped. Stopped records are
            # handled explicitly below.
            running=False,
        )

        if updates["reset"]:
            response_cache = updates

        else:
            response_cache["records"] = merge_by_key(
                updates.get("records", []),
                response_cache.get("records", []),
            )
            response_cache["settings"] = merge_by_key(
                updates.get("settings", []),
                response_cache.get("settings", []),
            )
            response_cache["server_time"] = updates.get("server_time", 0)
            response_cache["reset"] = updates.get("reset", 0)

        response_cache["records"] = post_process_records(
            response_cache.get("records", []),
            tags=tags,
            tags_match=tags_match,
            sort_by=sort_by,
            sort_reverse=sort_reverse,
            hidden=hidden,
            # Now that we have all data on records, even ones that became stopped,
            # we can filter for running records accoringly.
            running=running,
        )

        yield response_cache
        sleep(delay)
