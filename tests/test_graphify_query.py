"""
test_graphify_query.py — tests for _config/skills/graphify_query.py (v2)

Mocks subprocess.run so tests don't require the graphify CLI to be installed.
"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

sys_path_insert = __import__("sys").path.insert
sys_path_insert(0, str(Path(__file__).parent.parent / "_config" / "skills"))
import graphify_query  # noqa: E402


def _completed(stdout="", stderr="", returncode=0):
    return subprocess.CompletedProcess(args=[], returncode=returncode,
                                       stdout=stdout, stderr=stderr)


class TestGraphifyQuery:
    def test_query_passes_question_and_flags(self):
        with patch("graphify_query.shutil.which", return_value="/usr/bin/graphify"), \
             patch("graphify_query.subprocess.run",
                   return_value=_completed(stdout="ok")) as m:
            out = graphify_query.query("risk artifacts", budget=500)
        assert out == "ok"
        args = m.call_args.args[0]
        assert args[0] == "graphify"
        assert args[1:3] == ["query", "risk artifacts"]
        assert "--budget" in args and "500" in args
        assert "--graph" in args

    def test_query_dfs_flag(self):
        with patch("graphify_query.shutil.which", return_value="/usr/bin/graphify"), \
             patch("graphify_query.subprocess.run",
                   return_value=_completed(stdout="ok")) as m:
            graphify_query.query("q", dfs=True)
        assert "--dfs" in m.call_args.args[0]

    def test_path_passes_endpoints(self):
        with patch("graphify_query.shutil.which", return_value="/usr/bin/graphify"), \
             patch("graphify_query.subprocess.run",
                   return_value=_completed(stdout="A -> B")) as m:
            out = graphify_query.path("A", "B")
        assert out == "A -> B"
        args = m.call_args.args[0]
        assert args[1:4] == ["path", "A", "B"]

    def test_explain_passes_concept(self):
        with patch("graphify_query.shutil.which", return_value="/usr/bin/graphify"), \
             patch("graphify_query.subprocess.run",
                   return_value=_completed(stdout="explanation")) as m:
            out = graphify_query.explain("stage-contract")
        assert out == "explanation"
        args = m.call_args.args[0]
        assert args[1:3] == ["explain", "stage-contract"]


class TestGraphifyQueryErrors:
    def test_missing_cli_raises(self):
        with patch("graphify_query.shutil.which", return_value=None):
            with pytest.raises(graphify_query.GraphifyError, match="not on PATH"):
                graphify_query.query("anything")

    def test_nonzero_exit_raises(self):
        with patch("graphify_query.shutil.which", return_value="/usr/bin/graphify"), \
             patch("graphify_query.subprocess.run",
                   return_value=_completed(returncode=2, stderr="bad query")):
            with pytest.raises(graphify_query.GraphifyError, match="bad query"):
                graphify_query.query("anything")
