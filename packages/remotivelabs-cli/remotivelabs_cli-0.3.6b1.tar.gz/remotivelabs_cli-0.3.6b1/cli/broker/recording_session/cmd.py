from __future__ import annotations

import datetime
from dataclasses import asdict, is_dataclass
from enum import Enum
from functools import partial
from typing import Any, AsyncIterator, Optional

import typer
from asyncer import syncify
from remotivelabs.broker.auth import ApiKeyAuth, NoAuth
from remotivelabs.broker.recording_session import RecordingSessionClient, RecordingSessionPlaybackStatus

from cli.broker.defaults import DEFAULT_GRPC_URL
from cli.broker.recording_session.client import RecursiveFilesListingClient
from cli.broker.recording_session.time import time_offset_to_us
from cli.typer import typer_utils
from cli.utils.console import print_generic_error, print_result

app = typer_utils.create_typer(
    help="""
Manage playback of recording sessions

All offsets are in microseconds (μs)
"""
)


def _int_or_none(offset: Optional[str | int]) -> Optional[int]:
    return offset if offset is None else int(offset)


def _print_offset_help(cmd: str) -> str:
    return f"""
    Offsets can be specified in minutes (1:15min), seconds(10s), millis(10000ms) or micros(10000000us), default without suffix is micros.
    Samples offsets
    {cmd} 1.15min, 10s, 10000ms, 10000000us, 10000000,
    """


def _custom_types(o: Any) -> Any:
    if isinstance(o, Enum):
        return o.name
    if is_dataclass(type(o)):
        return asdict(o)
    if isinstance(o, datetime.datetime):
        return o.isoformat(timespec="seconds")
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


@app.command()
@partial(syncify, raise_sync_error=False)
async def list_files(
    path: str = typer.Argument("/", help="Optional subdirectory to list files in, defaults to /"),
    recursive: bool = typer.Option(False, help="List subdirectories recursively"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    """
    List files on broker.
    """
    try:
        if recursive:
            file_listing_client = RecursiveFilesListingClient(broker_url=url, api_key=api_key)
            print_result(
                await file_listing_client.list_all_files(path, file_types=None),  # Expose file-types in next version
                default=_custom_types,
            )
        else:
            client = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth())
            print_result(await client.list_recording_files(path), default=_custom_types)
    except Exception as e:
        print_generic_error(str(e))


@app.command(
    help=f"""
Starts playing the recording at current offset or from specified offset
{_print_offset_help("--offset")}
"""
)
@partial(syncify, raise_sync_error=False)
async def play(  # noqa: PLR0913
    path: str = typer.Argument(..., help="Path to the recording session", envvar="REMOTIVE_RECORDING_SESSION_PATH"),
    offset: str = typer.Option(None, callback=time_offset_to_us, help="Offset to play from"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    try:
        client = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth())
        print_result(await client.get_session(path=path).play(offset=_int_or_none(offset)), default=_custom_types)

    except Exception as e:
        print_generic_error(str(e))


@app.command(
    help=f"""
Repeat RecordingSession in specific interval or complete recording
To remove existing repeat config, use --clear flag.
{_print_offset_help("--startOffset/--endOffset")}
"""
)
@partial(syncify, raise_sync_error=False)
async def repeat(  # noqa: PLR0913
    path: str = typer.Argument(..., help="Path to the recording session", envvar="REMOTIVE_RECORDING_SESSION_PATH"),
    start_offset: str = typer.Option(0, callback=time_offset_to_us, help="Repeat start offset, defaults to start"),
    end_offset: str = typer.Option(None, callback=time_offset_to_us, help="Repeat end offset, defaults to end"),
    clear: bool = typer.Option(False, help="Clear repeat"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    """ """
    try:
        session = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth()).get_session(path)
        if clear:
            print_result(await session.set_repeat(start_offset=None, end_offset=None), _custom_types)
        else:
            print_result(
                await session.set_repeat(start_offset=int(start_offset), end_offset=_int_or_none(end_offset)),
                _custom_types,
            )

    except Exception as e:
        print_generic_error(str(e))


@app.command(
    help=f"""
    Pause the recording at current offset or specified offset
    {_print_offset_help("--offset")}
    """
)
@partial(syncify, raise_sync_error=False)
async def pause(
    path: str = typer.Argument(..., help="Path to the recording session", envvar="REMOTIVE_RECORDING_SESSION_PATH"),
    offset: str = typer.Option(None, callback=time_offset_to_us, help="Offset to play from"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    try:
        session = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth()).get_session(path)
        print_result(await session.pause(offset=_int_or_none(offset)), default=_custom_types)
    except Exception as e:
        print_generic_error(str(e))


@app.command(
    help=f"""
    Seek to specified offset
    {_print_offset_help("--offset")}
    """
)
@partial(syncify, raise_sync_error=False)
async def seek(
    path: str = typer.Argument(..., help="Path to the recording session", envvar="REMOTIVE_RECORDING_SESSION_PATH"),
    offset: str = typer.Option(..., callback=time_offset_to_us, help="Offset to seek to"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    try:
        session = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth()).get_session(path)
        print_result(await session.seek(offset=int(offset)), default=_custom_types)
    except Exception as e:
        print_generic_error(str(e))


@app.command()
@partial(syncify, raise_sync_error=False)
async def open(  # noqa: PLR0913
    path: str = typer.Argument(..., help="Path to the recording session", envvar="REMOTIVE_RECORDING_SESSION_PATH"),
    force: bool = typer.Option(False, help="Force close and re-open recording session if exists"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    """
    Open a recording session.
    """
    try:
        session = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth()).get_session(path)
        print_result(await session.open(force_reopen=force), default=_custom_types)
    except Exception as e:
        print_generic_error(str(e))


@app.command()
@partial(syncify, raise_sync_error=False)
async def close(
    path: str = typer.Argument(..., help="Path to the recording session", envvar="REMOTIVE_RECORDING_SESSION_PATH"),
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    """
    Close a recording session.
    """

    try:
        session = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth()).get_session(path)
        print_result(await session.close(), default=_custom_types)
    except Exception as e:
        print_generic_error(str(e))


@app.command()
@partial(syncify, raise_sync_error=False)
async def status(
    url: str = typer.Option(DEFAULT_GRPC_URL, help="Broker URL", envvar="REMOTIVE_BROKER_URL"),
    api_key: str = typer.Option("offline", help="Cloud Broker API-KEY or access token", envvar="REMOTIVE_BROKER_API_KEY"),
) -> None:
    """
    Get the status of a recording session.
    """
    try:
        client = RecordingSessionClient(url, auth=ApiKeyAuth(api_key) if api_key is not None else NoAuth())

        async def _async_playback_stream() -> None:
            stream: AsyncIterator[list[RecordingSessionPlaybackStatus]] = client.playback_status()
            async for f in stream:
                print_result(f, default=_custom_types)

        await _async_playback_stream()
    except Exception as e:
        print_generic_error(str(e))
