import argparse
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Dict, List, Optional, Tuple

from .bundles import build_template_bundle, list_directive_files, read_directive_file


def _print(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def _err(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def _ask_yes_no(question: str, default_yes: bool = True) -> bool:
    """Ask a yes/no question on the terminal, defaulting to Yes/No.

    If stdin is not a TTY (non-interactive), returns the default.
    """
    try:
        is_tty = sys.stdin.isatty()
    except Exception:
        is_tty = False

    suffix = "(Y/n)" if default_yes else "(y/N)"
    prompt = f"{question} {suffix} "

    if not is_tty:
        _print(f"{question} {suffix} -> defaulting to {'Yes' if default_yes else 'No'} (non-interactive)")
        return default_yes

    while True:
        resp = input(prompt).strip().lower()
        if resp == "":
            return default_yes
        if resp in ("y", "yes"):
            return True
        if resp in ("n", "no"):
            return False
        _print("Please answer 'y' or 'n'.")


def _package_data_root() -> Path:
    try:
        import importlib.resources as resources
    except Exception:  # pragma: no cover
        import importlib_resources as resources  # type: ignore

    # Resolve the path to packaged defaults under directive/data/
    return Path(resources.files("directive")).joinpath("data", "directive")  # type: ignore[attr-defined]


def _copy_tree(src: Path, dst: Path, overwrite: bool = False) -> Tuple[int, int, List[str]]:
    copied = 0
    skipped = 0
    notes: List[str] = []
    for root, dirs, files in os.walk(src):
        rel = Path(root).relative_to(src)
        target_dir = dst.joinpath(rel)
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in files:
            s = Path(root).joinpath(name)
            d = target_dir.joinpath(name)
            if d.exists() and not overwrite:
                skipped += 1
                notes.append(f"skip existing: {d}")
                continue
            shutil.copy2(s, d)
            copied += 1
            notes.append(f"wrote: {d}")
    return copied, skipped, notes


def _ensure_cursor_launcher(repo_root: Path, overwrite: bool = False) -> Tuple[int, int, List[str]]:
    """Create a repo-local launcher script and mcp.json for Cursor.

    Files:
      - .cursor/servers/directive.sh
      - .cursor/mcp.json

    Returns: (created_count, skipped_count, notes)
    """
    created = 0
    skipped = 0
    notes: List[str] = []

    cursor_dir = repo_root.joinpath(".cursor")
    servers_dir = cursor_dir.joinpath("servers")
    servers_dir.mkdir(parents=True, exist_ok=True)

    # Launcher script
    launcher_path = servers_dir.joinpath("directive.sh")
    launcher_body = """#!/usr/bin/env bash
set -euo pipefail
# cd to repo root; fall back to script-relative root
if ROOT=$(git rev-parse --show-toplevel 2>/dev/null); then
  cd "$ROOT"
else
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
  cd "$ROOT"
fi

# Development: prefer local source via uv run (fast with cache) or system Python fallback
if [ -d "$ROOT/src/directive" ]; then
  export PYTHONUNBUFFERED=1
  export PYTHONPATH="${ROOT}/src${PYTHONPATH+:$PYTHONPATH}"
  if command -v uv >/dev/null 2>&1; then
    exec uv run python -u -m directive.cli mcp serve
  else
    exec python3 -u -m directive.cli mcp serve
  fi
fi

# Installed: console script on PATH
if command -v directive >/dev/null 2>&1; then
  exec directive mcp serve
fi

echo "directive launcher not found. Install with: pipx install directive, or develop locally with src/ present." >&2
exit 127
"""
    if launcher_path.exists() and not overwrite:
        skipped += 1
        notes.append(f"skip existing: {launcher_path}")
    else:
        launcher_path.write_text(launcher_body, encoding="utf-8")
        try:
            # Make executable on POSIX
            os.chmod(launcher_path, 0o755)  # type: ignore[attr-defined]
        except Exception:
            pass
        created += 1
        notes.append(f"wrote: {launcher_path}")

    # mcp.json
    mcp_path = cursor_dir.joinpath("mcp.json")
    mcp_obj: Dict[str, Dict] = {
        "mcpServers": {
            "Directive": {
                "type": "stdio",
                "command": "/usr/bin/env",
                "args": ["-S", "uv", "run", "--python", "3.13", "-q", "-m", "directive.cli", "mcp", "serve"],
                "transport": "stdio",
            }
        }
    }
    mcp_body = json.dumps(mcp_obj, indent=2)
    if mcp_path.exists() and not overwrite:
        skipped += 1
        notes.append(f"skip existing: {mcp_path}")
    else:
        mcp_path.write_text(mcp_body + "\n", encoding="utf-8")
        created += 1
        notes.append(f"wrote: {mcp_path}")

    return created, skipped, notes


def _copy_cursor_templates(repo_root: Path, overwrite: bool = False) -> Tuple[int, int, List[str]]:
    """Copy packaged Cursor templates (mcp.json, servers script, rules) into .cursor/.

    Files live under package data at data/directive/cursor/ and maintain structure.
    
    DEPRECATED: This function is kept for reference but no longer used by init/update.
    Use _copy_cursor_rules_only() instead.
    """
    src = _package_data_root().joinpath("cursor")
    dst = repo_root.joinpath(".cursor")
    return _copy_tree(src, dst, overwrite=overwrite)


def _copy_cursor_rules_only(repo_root: Path, overwrite: bool = False) -> Tuple[int, int, List[str]]:
    """Copy only Cursor project rules from package data, not MCP server config.
    
    Copies only the rules/ subdirectory to .cursor/rules/, skipping mcp.json
    and servers/ directory which are not needed for agents to work with directive.
    
    Returns: (copied_count, skipped_count, notes)
    """
    src = _package_data_root().joinpath("cursor", "rules")
    dst = repo_root.joinpath(".cursor", "rules")
    return _copy_tree(src, dst, overwrite=overwrite)


def cmd_init(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    target = repo_root.joinpath("directive")
    if not target.exists():
        target.mkdir(parents=True, exist_ok=True)
    defaults = _package_data_root()
    copied, skipped, notes = _copy_tree(defaults, target, overwrite=False)
    _print(f"Initialized directive/ (copied {copied}, skipped {skipped})")
    if args.verbose:
        for n in notes:
            _print(n)

    # Prompt for Cursor Project Rules only (not MCP server)
    if _ask_yes_no("Add recommended Cursor Project Rules?", default_yes=True):
        c_created, c_skipped, c_notes = _copy_cursor_rules_only(repo_root, overwrite=False)
        _print(f"Created .cursor/rules/ (copied {c_created}, skipped {c_skipped})")
        if args.verbose:
            for n in c_notes:
                _print(n)
    else:
        _print("Skipped Cursor setup per user selection.")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    repo_root = Path.cwd()
    target = repo_root.joinpath("directive")
    if not target.exists():
        _err("No directive/ found. Run 'directive init' first.")
        return 1
    defaults = _package_data_root()
    copied, skipped, notes = _copy_tree(defaults, target, overwrite=False)
    _print(f"Updated directive/ (copied {copied} new files, left {skipped} unchanged)")
    if args.verbose:
        for n in notes:
            _print(n)
    # Note: We no longer update .cursor/ files to avoid modifying user's Cursor config
    # Users can manually update Cursor rules if needed
    return 0


def cmd_mcp_serve(args: argparse.Namespace) -> int:
    try:
        # Prefer FastMCP app when available
        from .server import _build_fastmcp_app, serve_stdio  # type: ignore
        app = _build_fastmcp_app()
        if app is not None:
            app.run("stdio")
            return 0
        # Fallback to legacy stdio server
        return serve_stdio(root=Path.cwd().joinpath("directive"))
    except Exception as exc:  # pragma: no cover
        _err("Failed to start Directive MCP server.")
        _err(str(exc))
        return 1


def cmd_bundle(args: argparse.Namespace) -> int:
    template_name = args.template
    try:
        bundle = build_template_bundle(template_name=template_name, repo_root=Path.cwd())
    except FileNotFoundError as e:
        _err(str(e))
        # Helpful list of available templates
        try:
            files = list_directive_files(Path.cwd())
            available = [f for f in files if "templates" in Path(f).parts]
        except Exception:
            available = []
        _err("Available templates:")
        for p in available:
            _err(f" - {p}")
        _err("Suggestion: run 'directive update' to restore defaults.")
        return 1

    _print(json.dumps(bundle, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="directive", description="Directive CLI")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Initialize directive/ with defaults (non-destructive)")
    p_init.set_defaults(func=cmd_init)

    p_update = sub.add_parser("update", help="Update directive/ with any missing defaults")
    p_update.set_defaults(func=cmd_update)

    p_serve = sub.add_parser("mcp", help="MCP related commands")
    sub_mcp = p_serve.add_subparsers(dest="mcp_command", required=True)
    p_serve_stdio = sub_mcp.add_parser("serve", help="Start MCP server over stdio in current repo")
    p_serve_stdio.set_defaults(func=cmd_mcp_serve)

    p_bundle = sub.add_parser("bundle", help="Print a template bundle (for testing)")
    p_bundle.add_argument("template", choices=["spec_template.md", "impact_template.md", "tdr_template.md"], help="Template file name")
    p_bundle.set_defaults(func=cmd_bundle)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    ns = parser.parse_args(argv)
    return int(ns.func(ns) or 0)


if __name__ == "__main__":
    raise SystemExit(main())


