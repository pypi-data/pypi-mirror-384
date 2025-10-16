from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List


DIRECTIVE_DIRNAME = "directive"


def _normalize_and_validate_path(root: Path, path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        candidate = candidate.relative_to(candidate.anchor)
    full = (root / candidate).resolve()
    if not str(full).startswith(str(root.resolve())):
        raise ValueError("Path escape detected; refusing to read outside directive root")
    return full


def get_directive_root(repo_root: Path | None = None) -> Path:
    base = Path.cwd() if repo_root is None else repo_root
    root = base / DIRECTIVE_DIRNAME
    if not root.exists():
        raise FileNotFoundError("directive/ directory not found. Run 'directive init' to create it.")
    return root


def list_directive_files(repo_root: Path | None = None) -> List[str]:
    root = get_directive_root(repo_root)
    results: List[str] = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            rel = str(Path(dirpath).joinpath(name).relative_to(root).as_posix())
            results.append(f"directive/{rel}")
    results.sort()
    return results


def read_directive_file(repo_root: Path | None, path: str) -> str:
    root = get_directive_root(repo_root)
    # Normalize provided path to a path relative to directive/ root
    if path.startswith("directive/"):
        normalized_path = Path(path).relative_to("directive").as_posix()
    else:
        normalized_path = path
    full = _normalize_and_validate_path(root, normalized_path)
    if not full.exists() or not full.is_file():
        raise FileNotFoundError(f"File not found under directive/: {path}")
    return full.read_text(encoding="utf-8")


def build_template_bundle(template_name: str, repo_root: Path | None = None) -> Dict:
    root = get_directive_root(repo_root)
    aop_path = root / "reference" / "agent_operating_procedure.md"
    ctx_path = root / "reference" / "agent_context.md"
    tmpl_path = root / "reference" / "templates" / template_name

    if not aop_path.exists():
        raise FileNotFoundError("Missing directive/reference/agent_operating_procedure.md. Run 'directive update'.")
    if not ctx_path.exists():
        raise FileNotFoundError("Missing directive/reference/agent_context.md. Run 'directive update'.")
    if not tmpl_path.exists():
        raise FileNotFoundError(
            f"Missing template: directive/reference/templates/{template_name}. Run 'directive update' or choose an existing template."
        )

    aop = aop_path.read_text(encoding="utf-8")
    ctx = ctx_path.read_text(encoding="utf-8")
    tmpl = tmpl_path.read_text(encoding="utf-8")

    return {
        "agentOperatingProcedure": {"path": "directive/reference/agent_operating_procedure.md", "content": aop},
        "agentContext": {"path": "directive/reference/agent_context.md", "content": ctx},
        "template": {"path": f"directive/reference/templates/{template_name}", "content": tmpl},
        "resources": [
            {"path": "directive/reference/agent_operating_procedure.md"},
            {"path": "directive/reference/agent_context.md"},
            {"path": f"directive/reference/templates/{template_name}"},
        ],
    }


