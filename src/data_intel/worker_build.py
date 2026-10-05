"""Build the private Python Worker without uploading it or inventing provenance."""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKER_DIR = REPO_ROOT / "workers" / "tools"


def _run_git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], check=True, capture_output=True, text=True, cwd=REPO_ROOT
    )
    return result.stdout.strip()


def _committed_revision() -> str:
    revision = _run_git("rev-parse", "--verify", "HEAD")
    if re.fullmatch(r"[a-f0-9]{40}", revision) is None:
        raise ValueError("invalid committed revision")
    if _run_git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Worker build requires a clean checkout")
    return revision


def main() -> int:
    try:
        revision = _committed_revision()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"Worker build refused: {error}", file=sys.stderr)
        return 2
    command = [
        "uv",
        "run",
        "--locked",
        "pywrangler",
        "deploy",
        "--dry-run",
        "--var",
        f"BUILD_REVISION:{revision}",
    ]
    try:
        return subprocess.run(command, check=False, cwd=WORKER_DIR).returncode
    except OSError:
        print("Worker build tool unavailable", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
