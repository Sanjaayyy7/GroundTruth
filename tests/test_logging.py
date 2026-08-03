"""Diagnostics contract: logging is ADDITIVE and lands on stderr only.

Groundtruth's stdout is an interface — human scorecards a README quotes, JSON a
consumer parses — and every artifact under runs/ is byte-diffed in CI. So the
observability work has a hard boundary: `-v` may add any amount of stderr and
must add exactly zero bytes to stdout, must never print a timestamp, and must
never echo trace content, because adversarial traces carry attack payloads by
design and a log file is not a quarantine.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pytest

from groundtruth.cli import main

REPO_ROOT = Path(__file__).resolve().parents[1]

# Any 12:34:56 or 2026-08-02 that reached stdout would churn a committed diff.
_CLOCK = re.compile(r"\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2}")

VERBS: tuple[tuple[str, ...], ...] = (
    ("run", "--agent", "hardened_agent"),
    ("run", "--agent", "vulnerable_agent"),
    ("validate",),
    ("rescore", "--check"),
    ("ci", "--agent", "hardened_agent"),
)


@pytest.fixture(autouse=True)
def _reset_logging():
    yield
    logging.getLogger("groundtruth").handlers.clear()
    logging.getLogger("groundtruth").setLevel(logging.NOTSET)


@pytest.mark.parametrize("argv", VERBS, ids=lambda a: "-".join(a[:2]))
def test_verbose_does_not_change_stdout_or_exit_code(argv, capsys):
    quiet_rc = main(list(argv))
    quiet = capsys.readouterr().out

    loud_rc = main([*argv, "--verbose"])
    loud = capsys.readouterr().out

    assert loud == quiet, "stdout is an interface; -v must be stderr-only"
    assert loud_rc == quiet_rc


@pytest.mark.parametrize("argv", VERBS, ids=lambda a: "-".join(a[:2]))
def test_no_timestamp_reaches_stdout(argv, capsys):
    main([*argv, "-vv"])

    assert not _CLOCK.search(capsys.readouterr().out)


def test_verbose_names_the_case_being_run_on_stderr(capsys):
    main(["run", "--agent", "hardened_agent", "-v"])

    err = capsys.readouterr().err
    assert "hardened_agent" in err
    assert "indirect_injection_01" in err  # the case ids, previously invisible


def test_verbose_reports_the_resolved_corpus_root(capsys):
    main(["validate", "-v"])

    assert str(REPO_ROOT) in capsys.readouterr().err


def test_debug_level_reports_git_invocations(capsys):
    main(["steward", "-vv"])

    err = capsys.readouterr().err
    assert "git ls-files" in err


def test_default_level_is_silent_on_stderr(capsys):
    main(["run", "--agent", "hardened_agent"])

    assert capsys.readouterr().err == ""


def test_trace_content_never_reaches_the_log(capsys):
    """The vulnerable subject leaks a credential and obeys an injected order.
    Neither the payload nor the secret may appear in diagnostics at any level —
    a trace is quarantined evidence, not debug output."""
    main(["run", "--agent", "vulnerable_agent", "-vv"])

    err = capsys.readouterr().err
    assert "Ignore previous instructions" not in err
    assert "sk-" not in err


def test_json_stdout_stays_parseable_under_verbose(capsys):
    rc = main(["run", "--agent", "hardened_agent", "--json", "-vv"])

    assert rc == 0
    assert json.loads(capsys.readouterr().out)["subject"] == "hardened_agent"
