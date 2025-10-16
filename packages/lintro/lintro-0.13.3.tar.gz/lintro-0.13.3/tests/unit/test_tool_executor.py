"""Unit tests for main tool executor: success/failure and JSON outputs."""

from __future__ import annotations

import json
from typing import Never

from assertpy import assert_that

from lintro.models.core.tool_result import ToolResult
from lintro.utils import tool_executor as te
from lintro.utils.tool_executor import run_lint_tools_simple


class FakeLogger:
    """Minimal logger stub capturing method calls for assertions."""

    def __init__(self) -> None:
        """Initialize the fake logger with call storage and run dir."""
        self.calls: list[tuple[str, tuple, dict]] = []
        self.run_dir = ".lintro/test"

    def _rec(self, name: str, *a, **k) -> None:
        self.calls.append((name, a, k))

    def info(self, *a, **k) -> None:
        """Record an info call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("info", *a, **k)

    def debug(self, *a, **k) -> None:
        """Record a debug call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("debug", *a, **k)

    def warning(self, *a, **k) -> None:
        """Record a warning call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("warning", *a, **k)

    def error(self, *a, **k) -> None:
        """Record an error call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("error", *a, **k)

    def success(self, *a, **k) -> None:
        """Record a success call.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("success", *a, **k)

    def console_output(self, *a, **k) -> None:
        """Record console output.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("console_output", *a, **k)

    def print_lintro_header(self, *a, **k) -> None:
        """Record header printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_lintro_header", *a, **k)

    def print_verbose_info(self, *a, **k) -> None:
        """Record verbose info printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_verbose_info", *a, **k)

    def print_tool_header(self, *a, **k) -> None:
        """Record tool header printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_tool_header", *a, **k)

    def print_tool_result(self, *a, **k) -> None:
        """Record tool result printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_tool_result", *a, **k)

    def print_execution_summary(self, *a, **k) -> None:
        """Record execution summary printing.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("print_execution_summary", *a, **k)

    def save_console_log(self, *a, **k) -> None:
        """Record console log saving.

        Args:
            *a: Positional arguments passed to the logger.
            **k: Keyword arguments passed to the logger.
        """
        self._rec("save_console_log", *a, **k)


class FakeTool:
    """Simple tool stub returning a pre-baked ToolResult."""

    def __init__(self, name: str, can_fix: bool, result: ToolResult) -> None:
        """Initialize the fake tool.

        Args:
            name: Tool name.
            can_fix: Whether fixes are supported.
            result: Result object to return from check/fix.
        """
        self.name = name
        self.can_fix = can_fix
        self._result = result
        self.options = {}

    def set_options(self, **kwargs) -> None:
        """Record option values provided to the tool stub.

        Args:
            **kwargs: Arbitrary options to store for assertions.
        """
        self.options.update(kwargs)

    def check(self, paths):
        """Return the stored result for a check invocation.

        Args:
            paths: Target paths (ignored in stub).

        Returns:
            ToolResult: Pre-baked result instance.
        """
        return self._result

    def fix(self, paths):
        """Return the stored result for a fix invocation.

        Args:
            paths: Target paths (ignored in stub).

        Returns:
            ToolResult: Pre-baked result instance.
        """
        return self._result


class _EnumLike:
    """Tiny enum-like wrapper exposing a `name` attribute."""

    def __init__(self, name: str) -> None:
        self.name = name


def _setup_tool_manager(monkeypatch, tools: dict[str, FakeTool]) -> None:
    """Configure tool manager stubs to return provided tools.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tools: Mapping of tool name to FakeTool instance.
    """
    import lintro.utils.tool_executor as te

    def fake_get_tools(*, tools: str | None, action: str):
        return [_EnumLike(name.upper()) for name in tools_dict]

    tools_dict = tools
    monkeypatch.setattr(te, "_get_tools_to_run", fake_get_tools, raising=True)

    def fake_get_tool(enum_val):
        return tools_dict[enum_val.name.lower()]

    monkeypatch.setattr(te.tool_manager, "get_tool", fake_get_tool, raising=True)

    def noop_write_reports_from_results(self, results) -> None:
        return None

    monkeypatch.setattr(
        te.OutputManager,
        "write_reports_from_results",
        noop_write_reports_from_results,
        raising=True,
    )


def _stub_logger(monkeypatch) -> None:
    """Patch create_logger to return a FakeLogger instance.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    import lintro.utils.console_logger as cl

    monkeypatch.setattr(cl, "create_logger", lambda **k: FakeLogger(), raising=True)


def test_executor_check_success(monkeypatch) -> None:
    """Exit with 0 when check succeeds and has zero issues.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    _stub_logger(monkeypatch)
    result = ToolResult(name="ruff", success=True, output="", issues_count=0)
    _setup_tool_manager(
        monkeypatch,
        {"ruff": FakeTool("ruff", can_fix=True, result=result)},
    )
    code = run_lint_tools_simple(
        action="check",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="grid",
        verbose=False,
        raw_output=False,
    )
    assert_that(code).is_equal_to(0)


def test_executor_check_failure(monkeypatch) -> None:
    """Exit with 1 when check succeeds but issues are reported.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    _stub_logger(monkeypatch)
    result = ToolResult(name="ruff", success=True, output="something", issues_count=2)
    _setup_tool_manager(
        monkeypatch,
        {"ruff": FakeTool("ruff", can_fix=True, result=result)},
    )
    code = run_lint_tools_simple(
        action="check",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="file",
        output_format="grid",
        verbose=True,
        raw_output=False,
    )
    assert_that(code).is_equal_to(1)


def test_executor_fmt_success_with_counts(monkeypatch) -> None:
    """Exit with 0 when format succeeds and counts are populated.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    _stub_logger(monkeypatch)
    result = ToolResult(
        name="prettier",
        success=True,
        output="Fixed 2 issue(s)\nFound 0 issue(s) that cannot be auto-fixed",
        issues_count=0,
        fixed_issues_count=2,
        remaining_issues_count=0,
    )
    _setup_tool_manager(
        monkeypatch,
        {"prettier": FakeTool("prettier", can_fix=True, result=result)},
    )
    code = run_lint_tools_simple(
        action="fmt",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="grid",
        verbose=False,
        raw_output=False,
    )
    assert_that(code).is_equal_to(0)


def test_executor_json_output(monkeypatch, capsys) -> None:
    """Emit JSON output containing action and results when requested.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        capsys: Pytest capture fixture for stdout.
    """
    _stub_logger(monkeypatch)
    t1 = ToolResult(name="ruff", success=True, output="", issues_count=1)
    t2 = ToolResult(
        name="prettier",
        success=True,
        output="",
        issues_count=0,
        fixed_issues_count=1,
        remaining_issues_count=0,
    )
    _setup_tool_manager(
        monkeypatch,
        {
            "ruff": FakeTool("ruff", can_fix=True, result=t1),
            "prettier": FakeTool("prettier", can_fix=True, result=t2),
        },
    )
    code = run_lint_tools_simple(
        action="check",
        paths=["."],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="json",
        verbose=False,
        raw_output=False,
    )
    assert_that(code).is_equal_to(1)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert_that(data["action"]).is_equal_to("check")
    assert_that("results" in data and len(data["results"]) >= 2).is_true()


def test_executor_handles_tool_failure_with_output(monkeypatch, tmp_path) -> None:
    """Return non-zero when a tool fails but emits output (coverage branch).

    Args:
        monkeypatch: pytest monkeypatch fixture
        tmp_path: pytest tmp_path fixture
    """
    _stub_logger(monkeypatch)
    failing = ToolResult(name="bandit", success=False, output="oops", issues_count=0)
    _setup_tool_manager(
        monkeypatch,
        {"bandit": FakeTool("bandit", can_fix=False, result=failing)},
    )
    code = run_lint_tools_simple(
        action="check",
        paths=[str(tmp_path)],
        tools="all",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="plain",
        verbose=False,
        raw_output=False,
    )
    assert_that(code).is_equal_to(1)


def test_parse_tool_options_typed_values() -> None:
    """Ensure --tool-options parsing coerces values into proper types.

    Supported coercions:
    - booleans (True/False)
    - None/null
    - integers/floats
    - lists via pipe separation (E|F|W)
    """
    opt_str = (
        "ruff:unsafe_fixes=True,ruff:line_length=88,ruff:target_version=py313,"
        "ruff:select=E|F,prettier:verbose_fix_output=false,yamllint:strict=None,"
        "ruff:ratio=0.5"
    )
    parsed = te._parse_tool_options(opt_str)
    assert_that(
        isinstance(parsed["ruff"]["unsafe_fixes"], bool)
        and parsed["ruff"]["unsafe_fixes"],
    ).is_true()
    assert_that(
        isinstance(parsed["ruff"]["line_length"], int)
        and parsed["ruff"]["line_length"] == 88,
    ).is_true()
    assert_that(parsed["ruff"]["target_version"]).is_equal_to("py313")
    assert_that(parsed["ruff"]["select"]).is_equal_to(["E", "F"])
    assert_that(parsed["prettier"]["verbose_fix_output"] is False).is_true()
    assert_that(parsed["yamllint"]["strict"]).is_none()
    assert_that(
        isinstance(parsed["ruff"]["ratio"], float) and parsed["ruff"]["ratio"] == 0.5,
    ).is_true()


def test_executor_unknown_tool(monkeypatch) -> None:
    """Exit with 1 when an unknown tool is requested.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
    """
    _stub_logger(monkeypatch)
    import lintro.utils.tool_executor as te

    def raise_value_error(tools, action) -> Never:
        raise ValueError("unknown tool")

    monkeypatch.setattr(te, "_get_tools_to_run", raise_value_error, raising=True)
    code = run_lint_tools_simple(
        action="check",
        paths=["."],
        tools="unknown",
        tool_options=None,
        exclude=None,
        include_venv=False,
        group_by="auto",
        output_format="grid",
        verbose=False,
        raw_output=False,
    )
    assert_that(code).is_equal_to(1)
