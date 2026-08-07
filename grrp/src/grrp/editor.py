"""Opening the user's editor.

Thirty lines rather than a dependency.  The tool must be readable in an
afternoon by a suspicious reviewer, and an editor launcher is not where to
spend someone's trust.

Nothing here reaches the network, and every command that uses it also accepts
``-m`` and ``--file``, so an environment with no editor at all loses nothing.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import tempfile
from pathlib import Path


def find() -> list[str] | None:
    """The editor to use, as a command and its arguments.

    ``GRRP_EDITOR`` first, so that a choice made for this tool does not disturb
    the one made for git.
    """
    for variable in ("GRRP_EDITOR", "VISUAL", "EDITOR"):
        value = os.environ.get(variable)
        if value:
            return shlex.split(value, posix=os.name != "nt")
    if os.name == "nt":
        return ["notepad"]
    for candidate in ("nano", "vi"):
        from shutil import which

        if which(candidate):
            return [candidate]
    return None


def edit(template: str, suffix: str = ".md") -> str | None:
    """Open ``template`` in an editor and return what came back.

    Returns None where no editor is available or the editor failed, so the
    caller can say something useful rather than raising a traceback.
    """
    command = find()
    if not command:
        return None

    handle, name = tempfile.mkstemp(suffix=suffix, prefix="grrp-")
    path = Path(name)
    try:
        os.close(handle)
        path.write_text(template, encoding="utf-8")
        result = subprocess.run([*command, str(path)])
        if result.returncode != 0:
            return None
        return path.read_text(encoding="utf-8")
    finally:
        path.unlink(missing_ok=True)
