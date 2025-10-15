from __future__ import annotations

import sys

import rich_click as click

from ._utils import get_project_metadata, run, sync_metadata_module

__all__ = ["build_artifacts"]

PROJECT = get_project_metadata()


def _status(label: str) -> str:
    return click.style(label, fg="green")


def _failure(label: str) -> str:
    return click.style(label, fg="red")


def build_artifacts() -> None:
    """Build Python wheel and sdist artifacts."""

    sync_metadata_module(PROJECT)
    click.echo("[build] Building wheel/sdist via python -m build")
    build_result = run(["python", "-m", "build"], check=False, capture=False)
    click.echo(f"[build] {_status('success') if build_result.code == 0 else _failure('failed')}")
    if build_result.code != 0:
        raise SystemExit(build_result.code)


def main() -> None:  # pragma: no cover
    build_artifacts()


if __name__ == "__main__":  # pragma: no cover
    from .cli import main as cli_main

    cli_main(["build", *sys.argv[1:]])
