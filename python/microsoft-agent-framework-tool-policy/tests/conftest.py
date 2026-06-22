"""Treat a fully-skipped suite as success rather than a CI failure.

These smokes require ``agent_framework`` (the ``live`` extra). Its pre-release
dependency tree has no Linux wheels — e.g. ``github-copilot-sdk`` ships
macOS-only — so CI's ``uv sync --extra dev`` cannot install it, and the module
``importorskip``s. pytest then collects no tests and exits ``5`` ("no tests
collected"), which CI reports as a failure. Coerce that one case to success so
the optional smoke skips cleanly; when ``agent_framework`` IS installed the
tests run and report normally.
"""

from __future__ import annotations

import pytest


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    if exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = pytest.ExitCode.OK
