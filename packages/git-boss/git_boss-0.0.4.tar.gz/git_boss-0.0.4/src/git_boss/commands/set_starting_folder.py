from pathlib import Path
from typing import Optional

from git_boss import config
from git_boss.config import Config


def run(cfg: Config, path: str, cfg_path: str) -> int:
    new_path = Path(path)
    if not new_path.is_absolute():
        print("Error: path must be an absolute path", file="stderr")
        return 2

    cfg.startingFolder = str(new_path)
    try:
        config.save_to_file(cfg, cfg_path)
    except Exception as exc:
        print(f"Failed to write config: {exc}", file="stderr")
        return 1

    print(f"Updated startingFolder in {cfg_path}")
    return 0
