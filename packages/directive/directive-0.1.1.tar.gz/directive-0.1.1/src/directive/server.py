#!/usr/bin/env -S uv run -q
# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp>=1.2.0"]
# ///
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import sys as _sys
from pathlib import Path as _Path

# Ensure local src/ is importable when running as a script via uv run
_SRC_CANDIDATE = _Path(__file__).resolve().parents[2] / "src"
if _SRC_CANDIDATE.exists() and str(_SRC_CANDIDATE) not in _sys.path:
    _sys.path.insert(0, str(_SRC_CANDIDATE))

from directive.bundles import build_template_bundle, list_directive_files, read_directive_file, get_directive_root
try:
    # Prefer official MCP server when launched as a script (Cursor)
    from mcp.server.fastmcp import FastMCP  # type: ignore
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore
try:  # Python 3.8+
    from importlib.metadata import version as _pkg_version  # type: ignore
except Exception:  # pragma: no cover
    _pkg_version = None  # type: ignore


# Minimal stdio JSON-RPC server (legacy) and FastMCP app (preferred for Cursor).
# Legacy server remains for tests; FastMCP path is used when running this file as a script.


@dataclass
class Request:
    id: Any
    method: str
    params: Dict[str, Any]


def _read_message() -> Optional[Dict[str, Any]]:
    import sys

    # Read headers until blank line; accept multiple headers and case-insensitive names.
    headers: Dict[str, str] = {}
    while True:
        line = sys.stdin.readline()
        if not line:
            return None
        if line in ("\r\n", "\n", ""):
            break
        if ":" not in line:
            # Ignore malformed header lines rather than failing hard
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    length_str = headers.get("content-length")
    if not length_str:
        return None
    try:
        length = int(length_str)
    except Exception:
        return None
    # Basic safety cap (10 MB) to avoid excessive memory usage
    if length < 0 or length > 10 * 1024 * 1024:
        return None

    raw = sys.stdin.read(length)
    if not raw:
        return None
    return json.loads(raw)


def _write_message(payload: Dict[str, Any]) -> None:
    import sys

    data = json.dumps(payload)
    sys.stdout.write(
        f"Content-Length: {len(data)}\r\nContent-Type: application/json\r\n\r\n{data}"
    )
    sys.stdout.flush()


def _error(id_value: Any, code: int, message: str, data: Any = None) -> None:
    err: Dict[str, Any] = {"jsonrpc": "2.0", "id": id_value, "error": {"code": code, "message": message}}
    if data is not None:
        err["error"]["data"] = data
    _write_message(err)


def _result(id_value: Any, result: Any) -> None:
    _write_message({"jsonrpc": "2.0", "id": id_value, "result": result})


# ---- MCP helpers ----

def _tool_descriptors() -> List[Dict[str, Any]]:
    return [
        {
            "name": "directive/files.list",
            "title": "List Directive Files",
            "description": "List all files under the repository’s directive/ directory (context and templates).",
            "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        },
        {
            "name": "directive/files.get",
            "title": "Read Directive File",
            "description": "Read a file under directive/ by path and return its full contents verbatim.",
            "inputSchema": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path under directive/ (e.g., directive/reference/agent_context.md)",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "directive/templates.spec",
            "title": "Spec Template Bundle",
            "description": "Return Agent Operating Procedure, Agent Context, and the Spec template, plus a concise Primer for drafting a new Spec.",
            "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        },
        {
            "name": "directive/templates.impact",
            "title": "Impact Template Bundle",
            "description": "Return Agent Operating Procedure, Agent Context, and the Impact template, plus a concise Primer for drafting an Impact analysis.",
            "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        },
        {
            "name": "directive/templates.tdr",
            "title": "TDR Template Bundle",
            "description": "Return Agent Operating Procedure, Agent Context, and the TDR template, plus a concise Primer for drafting a Technical Design Review.",
            "inputSchema": {"type": "object", "additionalProperties": False, "properties": {}},
        },
    ]


def _wrap_text_content(text: str) -> Dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def serve_stdio(root: Path) -> int:
    # Ensure we consistently resolve the repo root and directive root once.
    repo_root = root.parent
    try:
        directive_root = get_directive_root(repo_root)
    except Exception:
        directive_root = root

    while True:
        msg = _read_message()
        if msg is None:
            break
        id_value = msg.get("id")
        method = msg.get("method")
        params = msg.get("params") or {}

        try:
            # MCP initialize: declare capabilities so clients know tools are available
            if method == "initialize":
                ver = "0.0.0"
                try:
                    if _pkg_version is not None:
                        ver = _pkg_version("directive")  # type: ignore
                except Exception:
                    pass
                _result(
                    id_value,
                    {
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "directive", "version": ver},
                    },
                )

            # MCP tool discovery
            elif method == "tools/list":
                _result(id_value, {"tools": _tool_descriptors()})

            # MCP tool execution
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments") or {}
                if not isinstance(name, str):
                    raise ValueError("name must be a string")

                # Dispatch based on tool name
                if name == "directive/files.list":
                    files = list_directive_files(repo_root)
                    _result(id_value, _wrap_text_content(json.dumps({"files": files})))

                elif name == "directive/files.get":
                    path = arguments.get("path")
                    if not isinstance(path, str):
                        raise ValueError("path must be a string")
                    content = read_directive_file(repo_root, path)
                    _result(id_value, _wrap_text_content(json.dumps({"path": path, "content": content})))

                elif name == "directive/templates.spec":
                    bundle = build_template_bundle("spec_template.md", repo_root)
                    _result(id_value, _wrap_text_content(json.dumps(bundle)))

                elif name == "directive/templates.impact":
                    bundle = build_template_bundle("impact_template.md", repo_root)
                    _result(id_value, _wrap_text_content(json.dumps(bundle)))

                elif name == "directive/templates.tdr":
                    bundle = build_template_bundle("tdr_template.md", repo_root)
                    _result(id_value, _wrap_text_content(json.dumps(bundle)))

                else:
                    _error(id_value, -32601, f"Tool not found: {name}")

            # Back-compat custom methods removed per new naming convention
            else:
                _error(id_value, -32601, f"Method not found: {method}")
        except FileNotFoundError as e:
            _error(id_value, 1001, str(e))
        except Exception as e:  # pragma: no cover
            _error(id_value, -32000, "Server error", {"details": str(e)})

    return 0


# ---- FastMCP (preferred runtime in Cursor) ----
def _build_fastmcp_app() -> Any:
    if FastMCP is None:
        return None
    app = FastMCP("directive")

    @app.tool(name="directive/files.list")
    def directive_files_list() -> str:  # type: ignore
        files = list_directive_files(Path.cwd())
        return json.dumps({"files": files})

    @app.tool(name="directive/files.get")
    def directive_file_get(path: str) -> str:  # type: ignore
        content = read_directive_file(Path.cwd(), path)
        return json.dumps({"path": path, "content": content})

    @app.tool(name="directive/templates.spec")
    def directive_spec_template() -> str:  # type: ignore
        bundle = build_template_bundle("spec_template.md", Path.cwd())
        return json.dumps(bundle)

    @app.tool(name="directive/templates.impact")
    def directive_impact_template() -> str:  # type: ignore
        bundle = build_template_bundle("impact_template.md", Path.cwd())
        return json.dumps(bundle)

    @app.tool(name="directive/templates.tdr")
    def directive_tdr_template() -> str:  # type: ignore
        bundle = build_template_bundle("tdr_template.md", Path.cwd())
        return json.dumps(bundle)

    return app


if __name__ == "__main__":  # pragma: no cover
    app = _build_fastmcp_app()
    if app is None:
        # Fallback to legacy server (should not happen in Cursor execution)
        serve_stdio(root=Path.cwd().joinpath("directive"))
    else:
        app.run("stdio")


