from __future__ import annotations

import json
import os
import sys
from typing import Any

import grpc
from rich.console import Console

console = Console(soft_wrap=True)
err_console = Console(stderr=True, soft_wrap=True)


def print_grpc_error(error: grpc.RpcError) -> None:
    """TODO: remove me"""
    if error.code() == grpc.StatusCode.UNAUTHENTICATED:
        is_access_token = os.environ["ACCESS_TOKEN"]
        if is_access_token is not None and is_access_token == "true":
            err_console.print(f":boom: [bold red]Authentication failed[/bold red]: {error.details()}")
            err_console.print("Please login again")
        else:
            err_console.print(":boom: [bold red]Authentication failed[/bold red]")
            err_console.print("Failed to verify api-key")
    else:
        err_console.print(f":boom: [bold red]Unexpected error, status code[/bold red]: {error.code()}")
        err_console.print(error.details())
    sys.exit(1)


def print_newline() -> None:
    """TODO: remove me"""
    console.print("\n")


def print_url(url: str) -> None:
    console.print(url, style="bold")


def print_unformatted(message: Any) -> None:
    """TODO: remove me"""
    console.print(message)


def print_unformatted_to_stderr(message: Any) -> None:
    """TODO: remove me"""
    err_console.print(message)


def print_success(message: str | None = None) -> None:
    """
    Print a success message to stdout

    TODO: use stderr instead.
    """
    msg = "[bold green]Success![/bold green]"
    if message:
        msg += f" {message}"
    console.print(msg)


def print_generic_error(message: str | None = None) -> None:
    """
    Print a failure message to stderr

    TODO: rename to print_failure
    """
    msg = ":boom: [bold red]Failed[/bold red]"
    if message:
        msg += f": {message}"
    err_console.print(msg)


def print_generic_message(message: str) -> None:
    """
    Print a message to the user.

    TODO: rename to print_message
    TODO: use stderr instead.
    """
    console.print(f"[bold]{message}[/bold]")


def print_hint(message: str) -> None:
    """
    Print a hint to stderr.

    Useful when nudging the user to a suitable solution.
    """
    err_console.print(f":point_right: [bold]{message}[/bold]")


def print_result(result: Any, default: Any = None) -> None:
    """
    Print a result to stdout

    TODO: Decide on how to handle output. In broker lib (to_json)?
    """
    console.print(json.dumps(result, indent=2, default=default))
