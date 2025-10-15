from pathlib import Path
import subprocess
from typing import List
import os
import stat
import shutil

from git_boss.git import find_git_executable
from git_boss.config import Config


def _url_to_path(url: str) -> str:
    # HTTPS URLs: https://host/foo/bar.git -> host/foo/bar
    if url.startswith("http://") or url.startswith("https://"):
        # naive parse
        without_scheme = url.split("://", 1)[1]
        # remove trailing .git
        if without_scheme.endswith(".git"):
            without_scheme = without_scheme[: -len(".git")]
        # ensure no leading /
        return without_scheme.lstrip("/")

    # SSH style: git@host:owner/repo.git -> host/owner/repo
    if url.startswith("git@"):
        without_prefix = url[len("git@") :]
        # replace ':' with '/'
        if without_prefix.endswith(".git"):
            without_prefix = without_prefix[: -len('.git')]
        without_prefix = without_prefix.replace(":", "/")
        return without_prefix

    # file:// URLs - use the repository name as folder
    if url.startswith("file://"):
        # get last path component without .git
        try:
            p = Path(url.replace("file://", ""))
            name = p.name
            if name.endswith('.git'):
                name = name[: -len('.git')]
            return name
        except Exception:
            pass

    # Fallback: use the repository basename (strip .git)
    try:
        from pathlib import Path

        p = Path(url)
        name = p.name
        if name.endswith('.git'):
            name = name[: -len('.git')]
        return name
    except Exception:
        # last resort: return raw URL with .git stripped
        if url.endswith(".git"):
            return url[: -len(".git")]
        return url


def run(cfg: Config, cfg_path: str) -> int:
    start = Path(cfg.startingFolder)
    start.mkdir(parents=True, exist_ok=True)

    cloned = 0
    processed: List[str] = []

    for url in cfg.gitProjects:
        processed.append(url)
        rel = _url_to_path(url)
        target = start / rel
        # ensure parent directories exist
        target_parent = target.parent
        target_parent.mkdir(parents=True, exist_ok=True)

        # If already cloned (has .git), skip
        if (target / ".git").exists():
            print(f"Skipped (already cloned): {target}")
            continue

        # If target exists but not a git repo, we still attempt clone into it (git clone will fail)
        try:
            print(f"Cloning {url} -> {target} ...")
            git_exe = find_git_executable()
            res = subprocess.run([git_exe, "clone", url, str(target)], check=False, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"Cloned: {target}")
                cloned += 1
            else:
                print(f"Failed to clone {url}: {res.stderr.strip()}")
        except Exception as exc:
            print(f"Exception while cloning {url}: {exc}")

    print(f"Summary: {cloned} newly cloned out of {len(processed)} projects")

    # Now remove stale cloned project folders: any folder under startingFolder
    # that contains a .git directory but whose relative path is not in the
    # current set of configured projects should be deleted.
    configured_rel_paths = { _url_to_path(u) for u in cfg.gitProjects }
    deleted = 0

    # Walk top-level directories under startingFolder (recursively) and find
    # directories that appear to be cloned repos (contain .git)
    for d in start.rglob("*"):
        if not d.is_dir():
            continue

        if (d / ".git").exists():
            # compute relative path from start
            try:
                rel = d.relative_to(start)
            except Exception:
                print(f"ERROR: could not compute relative path for {d} under {start}; skipping")
                continue

            rel_str = str(rel).replace("\\", "/")
            # If this repo path isn't in configured set, and it is not an
            # ancestor of any configured path, delete it.
            # Example: configured contains 'apple/orange/two'. A cloned repo at
            # 'apple' should NOT be removed because it's an ancestor of a
            # configured project. We only remove when no configured path starts
            # with rel_str + '/'.
            is_configured = rel_str in configured_rel_paths
            is_ancestor_of_configured = any(
                p.startswith(rel_str + "/") for p in configured_rel_paths
            )

            if not is_configured and not is_ancestor_of_configured:
                # safe delete: remove the directory tree
                try:
                    print(f"Removing stale cloned repo: {d}")
                    shutil.rmtree(d, onerror=_remove_readonly)
                    deleted += 1
                except Exception as exc:
                    print(f"ERROR: Failed to remove {d}: {exc}")

    print(f"Deleted {deleted} stale cloned projects")
    return 0


def _remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)
