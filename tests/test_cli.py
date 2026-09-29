# -*- coding: utf-8 -*-
# Author: Dylan Jones
# Date:   2025-04-21

import sys
from subprocess import run


def test_cli():
    """Check if the CLI is callable."""
    result = run(
        [sys.executable, "-m", "pyrekordbox", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"Command failed with exit code {result.returncode}\n{result.stderr}"
    )
