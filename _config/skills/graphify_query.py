"""
graphify_query.py — Graphify CLI wrapper skill v2.0

Thin Python wrapper over the upstream `graphify` CLI (safishamsi/graphify, PyPI:
`graphifyy`). v1 of this skill targeted an HTTP MCP server on :7331 that
upstream Graphify does not ship; v2 shells out to the real CLI instead.

Usage (direct CLI):
  python _config/skills/graphify_query.py --query "synthesis stage risk artifacts"
  python _config/skills/graphify_query.py --explain "stage-contract"
  python _config/skills/graphify_query.py --path-from "ingester.py" --path-to "audit_logger.py"

API (imported by agent):
  from _config.skills.graphify_query import query, path, explain

Requires:
  pip install graphifyy   (provides `graphify` on PATH)
  graphify-out/graph.json present (run `graphify update .` first)

Frontmatter-aware helpers (filter by status/stage/risk_tier) were removed in
v2: upstream's default AST extraction does not lift YAML frontmatter onto
graph nodes. Add a separate skill that walks stages/**/*.md directly if
those queries are needed.
"""

import argparse
import os
import shutil
import subprocess
import sys

GRAPHIFY_BIN = os.environ.get("GRAPHIFY_BIN", "graphify")
DEFAULT_GRAPH = "graphify-out/graph.json"
DEFAULT_BUDGET = 2000


class GraphifyError(RuntimeError):
    """Raised when the graphify CLI is missing or returns non-zero."""


def _run(args: list[str]) -> str:
    if shutil.which(GRAPHIFY_BIN) is None:
        raise GraphifyError(
            f"`{GRAPHIFY_BIN}` not on PATH. Install with `pip install graphifyy`."
        )
    result = subprocess.run(
        [GRAPHIFY_BIN, *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise GraphifyError(
            f"graphify {' '.join(args)} failed (exit {result.returncode}): "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def query(question: str, budget: int = DEFAULT_BUDGET, dfs: bool = False,
          graph: str = DEFAULT_GRAPH) -> str:
    """BFS (or DFS) traversal of graph.json for `question`. Returns CLI stdout."""
    args = ["query", question, "--budget", str(budget), "--graph", graph]
    if dfs:
        args.append("--dfs")
    return _run(args)


def path(source: str, target: str, graph: str = DEFAULT_GRAPH) -> str:
    """Shortest path between two node labels in graph.json."""
    return _run(["path", source, target, "--graph", graph])


def explain(concept: str, graph: str = DEFAULT_GRAPH) -> str:
    """Plain-language explanation of a node and its neighbors."""
    return _run(["explain", concept, "--graph", graph])


def main():
    parser = argparse.ArgumentParser(
        description="graphify_query — wrap the upstream `graphify` CLI"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query",   metavar="TEXT",    help="BFS query (graphify query)")
    group.add_argument("--explain", metavar="NODE",    help="Explain a node (graphify explain)")
    group.add_argument("--path-from", metavar="FROM",  help="Path source (use with --path-to)")
    parser.add_argument("--path-to", metavar="TO",     help="Path target")
    parser.add_argument("--budget", type=int, default=DEFAULT_BUDGET)
    parser.add_argument("--dfs",    action="store_true", help="DFS instead of BFS")
    parser.add_argument("--graph",  default=DEFAULT_GRAPH, help="Path to graph.json")
    args = parser.parse_args()

    try:
        if args.query:
            out = query(args.query, args.budget, args.dfs, args.graph)
        elif args.explain:
            out = explain(args.explain, args.graph)
        elif args.path_from:
            if not args.path_to:
                parser.error("--path-from requires --path-to")
            out = path(args.path_from, args.path_to, args.graph)
        else:
            parser.print_help()
            sys.exit(1)
        sys.stdout.write(out)
    except GraphifyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
