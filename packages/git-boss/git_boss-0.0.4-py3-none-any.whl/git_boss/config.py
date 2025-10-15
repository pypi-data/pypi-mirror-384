"""Configuration loader for git_boss.

Provides a minimal Config dataclass and utilities to load a YAML file and
keep the parsed configuration available to the rest of the package.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
import yaml


@dataclass
class Config:
    startingFolder: str
    gitProjects: List[str]


def create_from_file_path(path: str) -> Config:
    """Load a YAML config file and return a Config instance.

    The YAML must contain:
      startingFolder: <absolute path>
      gitProjects: [list, of, git, urls]
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a mapping at top-level")

    starting = data.get("startingFolder")
    projects = data.get("gitProjects")

    if not isinstance(starting, str):
        raise ValueError("startingFolder must be a string path")

    # Interpret startingFolder. If it's relative, resolve it relative to the
    # directory containing the config file so that bundled defaults can use
    # relative paths (for example `.` meaning the package directory).
    starting_path = Path(starting)
    if not starting_path.is_absolute():
        starting_path = (Path(path).parent / starting_path).resolve()

    # Create the directory if it doesn't exist
    if not starting_path.exists():
        try:
            starting_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # pragma: no cover - permissions/environment dependent
            raise OSError(f"Failed to create startingFolder '{starting}': {exc!s}") from exc
    if not isinstance(projects, list) or not all(isinstance(p, str) for p in projects):
        raise ValueError("gitProjects must be a list of strings")

    return Config(startingFolder=str(starting_path), gitProjects=projects)


def save_to_file(cfg: Config, path: str) -> None:
    """Write a Config instance back to a YAML file at `path`."""
    data = {"startingFolder": cfg.startingFolder, "gitProjects": cfg.gitProjects}
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)
