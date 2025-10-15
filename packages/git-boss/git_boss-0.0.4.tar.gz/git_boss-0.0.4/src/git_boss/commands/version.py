from importlib import metadata
from typing import Optional


def _homepage_from_project_urls(meta) -> Optional[str]:
    try:
        urls = meta.get_all("Project-URL") or []
    except Exception:
        urls = []
    for entry in urls:
        # Expected format: "Homepage, https://github.com/kristof9851/git_boss"
        parts = [p.strip() for p in entry.split(",", 1)]
        if len(parts) == 2:
            label, url = parts
            if label.lower() == "homepage" and url:
                return url
    return None


def run(cfg, cfg_path: str) -> int:
    
    try:
        meta = metadata.metadata("git_boss")

        name = meta.get("Name") or "(unknown)"
        version = meta.get("Version") or "(unknown)"
        description = meta.get("Summary") or "(unknown)"
        homepage = _homepage_from_project_urls(meta) or meta.get("Home-page") or "(unknown)"
    except Exception:
        name = "(unknown)"
        version = "(unknown)"
        description = "(unknown)"
        homepage = "(unknown)"

    print(f"Name: {name}")
    print(f"Version: {version}")
    print(f"Description: {description}")
    print(f"Homepage: {homepage}")

    return 0
