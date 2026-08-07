from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from grrp.cli import app
from grrp.store import Repo

runner = CliRunner()


def sid(identifier: str, length: int = 10) -> str:
    """An identifier prefix, the way a user would type one at a prompt."""
    return identifier.split(":")[-1][:length]


class Workspace:
    """A grrp record in a temporary directory, driven through the CLI."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def run(self, *args: str, expect_ok: bool = True):
        cwd = os.getcwd()
        os.chdir(self.path)
        try:
            result = runner.invoke(app, list(args))
        finally:
            os.chdir(cwd)
        if expect_ok and result.exit_code != 0:
            raise AssertionError(
                f"grrp {' '.join(args)} exited {result.exit_code}\n"
                f"{result.output}\n{result.exception!r}"
            )
        return result

    @property
    def repo(self) -> Repo:
        return Repo(self.path)


@pytest.fixture()
def workspace(tmp_path: Path) -> Workspace:
    space = Workspace(tmp_path)
    space.run("init")
    return space


@pytest.fixture()
def trajectory(workspace: Workspace) -> tuple[Workspace, str]:
    workspace.run("new", "Is trust a property between individuals?", "--title", "trust")
    return workspace, workspace.repo.trajectory_ids()[0]


@pytest.fixture()
def workspace_key(workspace) -> str:
    """The local name of the acting party's key."""
    return "self"
