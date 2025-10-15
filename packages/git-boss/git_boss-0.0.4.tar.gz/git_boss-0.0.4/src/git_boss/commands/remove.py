from typing import Optional

from git_boss.config import Config
from git_boss import config


def run(cfg: Config, url: str, cfg_path: str) -> int:
    if url not in cfg.gitProjects:
        print("URL not present in config")
        return 0

    cfg.gitProjects = [u for u in cfg.gitProjects if u != url]
    try:
        config.save_to_file(cfg, cfg_path)
    except Exception as exc:
        print(f"Failed to write config: {exc}", file="stderr")
        return 1

    print(f"Removed {url} from {cfg_path}")
    return 0
