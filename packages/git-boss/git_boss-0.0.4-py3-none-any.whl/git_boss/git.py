"""Utilities for locating the git executable."""
from pathlib import Path
import shutil
from typing import Optional


def find_git_executable() -> Optional[str]:
    """Return the path to a git executable or None if not found.

    Preference order:
    - git on PATH (shutil.which)
    - Windows installer default: C:\\Program Files\\Git\\bin\\git.exe
    """
    git_exe = shutil.which("git")
    if git_exe:
        return git_exe

    fallback = Path(r"C:\Program Files\Git\bin\git.exe")
    if fallback.exists():
        return str(fallback)

    raise RuntimeError("git executable not found")
