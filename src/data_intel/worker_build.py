"""Build the private Python Worker without uploading it or inventing provenance."""

import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

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


def _complete_bundle(outdir: Path) -> bool:
    modules = outdir / "python_modules"
    required = (
        outdir / "index.py",
        modules / "data_intel" / "__init__.py",
        modules / "workers" / "__init__.py",
        modules / "pydantic" / "__init__.py",
        modules / "pydantic_core" / "__init__.py",
    )
    return all(path.is_file() for path in required) and any(
        (modules / "pydantic_core").glob("_pydantic_core*.so")
    )


def _dry_run(revision: str, outdir: Path) -> int:
    install = subprocess.run(
        ["npm", "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
        check=False,
        cwd=WORKER_DIR,
    )
    if install.returncode:
        return install.returncode
    return subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "pywrangler",
            "deploy",
            "--dry-run",
            "--outdir",
            str(outdir),
            "--var",
            f"BUILD_REVISION:{revision}",
        ],
        check=False,
        cwd=WORKER_DIR,
    ).returncode


def main() -> int:
    try:
        revision = _committed_revision()
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"Worker build refused: {error}", file=sys.stderr)
        return 2
    runtime_lock = WORKER_DIR / "pylock.toml"
    try:
        locked_bytes = runtime_lock.read_bytes()
    except OSError:
        print("Worker runtime lock unavailable", file=sys.stderr)
        return 2
    try:
        with TemporaryDirectory(prefix="172x-worker-dry-run-") as directory:
            outdir = Path(directory)
            result = _dry_run(revision, outdir)
            complete = _complete_bundle(outdir) if result == 0 else False
    except OSError:
        print("Worker build tool unavailable", file=sys.stderr)
        return 2
    try:
        if runtime_lock.read_bytes() != locked_bytes:
            print("Worker runtime lock changed during build", file=sys.stderr)
            return 2
    except OSError:
        print("Worker runtime lock unavailable after build", file=sys.stderr)
        return 2
    if result:
        return result
    if not complete:
        print("Worker dry-run bundle missing required Python modules", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
