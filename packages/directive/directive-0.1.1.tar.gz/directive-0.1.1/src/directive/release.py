import argparse
import re
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def run_git_command(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        fail(f"git {' '.join(args)} failed with exit code {exc.returncode}")


def run_command(*args: str, capture_output: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            list(args),
            check=True,
            text=True,
            capture_output=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        if exc.stdout:
            print(exc.stdout)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise


def ensure_clean_working_tree(strict_lock: bool = False) -> None:
    """Ensure the working tree is clean before releasing.

    By default, ignore changes to 'uv.lock' because running this script via
    'uv run' may cause transient lockfile updates prior to process launch.
    Use --strict-lock to enforce a fully clean tree including 'uv.lock'.
    """
    proc = run_git_command("status", "--porcelain", capture_output=True)
    dirty: list[str] = []
    for line in (proc.stdout or "").splitlines():
        # Format: 'XY <path>' where XY are status codes
        path = line[3:] if len(line) > 3 else line
        if not strict_lock and path == "uv.lock":
            continue
        dirty.append(line)
    if dirty:
        print("\n".join(dirty))
        fail("Working tree is dirty. Commit or stash changes before running release.")


def parse_version(version_str: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version_str.strip())
    if not match:
        fail(f"Malformed version: '{version_str}'. Expected format X.Y.Z")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def bump_version(current: str, bump_type: str) -> str:
    major, minor, patch = parse_version(current)
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        fail("bump_type must be one of: major, minor, patch")
    return f"{major}.{minor}.{patch}"


def read_current_version(pyproject_path: Path) -> str:
    if not pyproject_path.exists():
        fail(f"pyproject.toml not found at {pyproject_path}")
    in_project = False
    version_value: str | None = None
    for line in pyproject_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
            continue
        if in_project:
            m = re.match(r"version\s*=\s*\"([^\"]+)\"", stripped)
            if m:
                version_value = m.group(1)
                break
    if not version_value:
        fail("Could not find project.version in pyproject.toml")
    return version_value


def write_new_version(pyproject_path: Path, new_version: str) -> None:
    lines = pyproject_path.read_text(encoding="utf-8").splitlines()
    in_project = False
    replaced = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_project = stripped == "[project]"
        elif in_project:
            if re.match(r"version\s*=\s*\"([^\"]+)\"", stripped):
                indent = line[: len(line) - len(line.lstrip())]
                lines[i] = f"{indent}version = \"{new_version}\""
                replaced = True
                break
    if not replaced:
        fail("project.version not found for update in pyproject.toml")
    pyproject_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_repo_slug() -> str | None:
    # Examples:
    #  - git@github.com:owner/repo.git
    #  - https://github.com/owner/repo.git
    proc = run_git_command("config", "--get", "remote.origin.url", capture_output=True)
    url = (proc.stdout or "").strip()
    if not url:
        return None
    if url.startswith("git@github.com:"):
        slug = url.split(":", 1)[1]
    elif url.startswith("https://github.com/"):
        slug = url.split("https://github.com/", 1)[1]
    else:
        return None
    if slug.endswith(".git"):
        slug = slug[:-4]
    return slug if "/" in slug else None


def open_pull_request(new_version: str, branch_name: str) -> None:
    title = f"chore(release): v{new_version}"
    body = (
        f"Automated release PR for v{new_version}.\n\n"
        "- Bumps project.version in pyproject.toml\n"
        "- Merging this PR to main will trigger the PyPI publish workflow"
    )
    # Try GitHub CLI if available
    try:
        run_command(
            "gh",
            "pr",
            "create",
            "--base",
            "main",
            "--head",
            branch_name,
            "--title",
            title,
            "--body",
            body,
            capture_output=False,
        )
        print("Opened GitHub PR via gh CLI")
        return
    except Exception:
        pass

    # Fallback: print URL to create PR
    slug = get_repo_slug()
    if slug:
        url = f"https://github.com/{slug}/compare/main...{branch_name}?expand=1&title={title}"
        print(f"Open a PR: {url}")
    else:
        print("Could not determine repo slug to open PR URL.")


def update_base_branch(base_branch: str) -> None:
    """Checkout the base branch and fast-forward to origin."""
    # Fetch latest refs
    run_git_command("fetch", "origin", "--prune")
    # Checkout the base branch (create local if missing)
    try:
        run_git_command("rev-parse", "--verify", base_branch, capture_output=True)
        run_git_command("checkout", base_branch)
    except SystemExit:
        # Local branch missing; create tracking from origin
        run_git_command("checkout", "-b", base_branch, f"origin/{base_branch}")
    # Fast-forward only
    run_git_command("pull", "--ff-only", "origin", base_branch)


def create_and_push_release_branch(new_version: str) -> None:
    branch_name = f"release/v{new_version}"
    # Create and switch to new branch BEFORE committing, so base branch stays untouched
    run_git_command("checkout", "-b", branch_name)
    run_git_command("add", "pyproject.toml")
    run_git_command("commit", "-m", f"chore(release): v{new_version}")
    # Push and set upstream
    run_git_command("push", "-u", "origin", branch_name)
    print(f"Pushed {branch_name} to origin")
    open_pull_request(new_version, branch_name)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Bump version and create a release branch")
    parser.add_argument("bump", choices=["major", "minor", "patch"], help="Type of version bump")
    parser.add_argument("--base-branch", "-b", default="main", help="Base branch to cut release from (default: main)")
    parser.add_argument(
        "--strict-lock",
        action="store_true",
        help="Fail if uv.lock is modified (default: ignore uv.lock changes)",
    )
    args = parser.parse_args(argv)

    # Ensure inside a git repo
    try:
        run_git_command("rev-parse", "--is-inside-work-tree", capture_output=True)
    except SystemExit:
        raise

    ensure_clean_working_tree(strict_lock=args.strict_lock)
    # Ensure we are up to date with the base branch before editing files
    update_base_branch(args.base_branch)

    pyproject_path = Path("pyproject.toml")
    current_version = read_current_version(pyproject_path)
    next_version = bump_version(current_version, args.bump)

    if next_version == current_version:
        fail("Next version equals current version; nothing to do.")

    print(f"Current version: {current_version}\nNext version: {next_version}")
    write_new_version(pyproject_path, next_version)

    create_and_push_release_branch(next_version)


if __name__ == "__main__":
    main()


