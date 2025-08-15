# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-04-21

from subprocess import run
from types import SimpleNamespace as Namespace


def shell(command, **kwargs):
    """Execute a shell command capturing output and exit code."""
    completed = run(command, shell=True, capture_output=True, check=False, **kwargs)
    return Namespace(
        exit_code=completed.returncode,
        stdout=completed.stdout.decode(),
        stderr=completed.stderr.decode(),
    )


def test_cli():
    """Check if the CLI is callable."""
    result = shell("python -m pyrekordbox --help")
    # Check if the command was successful
    assert result.exit_code == 0, f"Command failed with exit code {result.exit_code}"
