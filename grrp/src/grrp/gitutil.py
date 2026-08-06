"""Git, called as a subprocess.

Version control is a substrate, not a dependency to be wrapped.  It supplies
append-only history, content addressing and the transport by which a complete
record is copied and continued elsewhere.  This module is the whole of the
coupling.

Nothing here is required for a conformant record: the files on disk are the
record, and every command works in a directory that is not a git repository.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def available() -> bool:
    return shutil.which("git") is not None


def in_work_tree(path: Path) -> bool:
    if not available():
        return False
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def commit_paths(root: Path, paths: list[Path], message: str) -> bool:
    """Commit exactly the given paths, and nothing else.

    A researcher's working tree is usually dirty with work in progress.
    Committing anything beyond what this tool wrote would be taking a decision
    that is not ours.
    """
    if not paths or not in_work_tree(root):
        return False
    relative = [str(p.relative_to(root)) for p in paths]
    add = subprocess.run(
        ["git", "add", "--", *relative], cwd=root, capture_output=True, text=True
    )
    if add.returncode != 0:
        return False
    commit = subprocess.run(
        ["git", "commit", "-m", message, "--", *relative],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return commit.returncode == 0
