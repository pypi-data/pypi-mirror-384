from typing import List

from git_boss.config import Config


def run(cfg: Config, pattern: str, cfg_path: str) -> int:
    projects: List[str] = cfg.gitProjects or []
    matched = [p for p in projects if pattern in p]
    if not matched:
        return 0

    for p in matched:
        print(p)

    return 0
