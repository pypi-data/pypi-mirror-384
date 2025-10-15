from typing import Optional
from urllib.parse import urlparse
from pathlib import Path
import sys

from git_boss.config import Config
from git_boss.commands import sync
from git_boss import config


def _is_git_url(url: str) -> bool:
    # Basic checks: http(s) URLs ending with .git or ssh-style git@...:repo.git
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https") and url.endswith(".git"):
        return True
    # file:// URLs pointing to a .git repo path
    if parsed.scheme == "file" and (parsed.path.endswith(".git") or url.endswith(".git")):
        return True
    if url.startswith("git@") and ".git" in url:
        return True
    return False


def run(cfg: Config, url: str, cfg_path: str) -> int:
    if not _is_git_url(url):
        print("Error: provided URL does not look like a git repository URL", file=sys.stderr)
        return 2

    if url in cfg.gitProjects:
        print("URL already present in config")
        return 0

    cfg.gitProjects.append(url)
    try:
        config.save_to_file(cfg, cfg_path)
        print(f"Added {url} to {cfg_path}")
    except Exception as exc:
        print(f"Failed to write config: {exc}", file=sys.stderr)
        return 1

    # After updating the config, automatically run sync
    try:
        return sync.run(cfg, cfg_path)
    except Exception:
        return 0
