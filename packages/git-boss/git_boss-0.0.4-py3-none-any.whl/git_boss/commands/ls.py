from typing import List

from git_boss.config import Config


def run(cfg: Config, cfg_path: str) -> int:
    print(f"Starting folder:")
    if getattr(cfg, "startingFolder", None):
        print(f"- {cfg.startingFolder}")
    else:
        print("- (Not set)")

    print()
    
    print("Git projects: ")
    projects: List[str] = cfg.gitProjects or []
    if projects:
        for p in projects:
            print(f"- {p}")
    else:
        print("- (No git projects configured)")

    return 0
