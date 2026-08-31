# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pathlib import Path

import pytest

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.report.validation import (
    resolve_bug_number,
    validate_bug_data,
)


@pytest.fixture
def full_diff():
    """A diff exercising every field bugmon can legitimately modify"""
    return {
        "whiteboard": "[bugmon:bisected,confirmed]",
        "status": "VERIFIED",
        "keywords": {"add": ["regression"], "remove": ["bugmon"]},
        "cf_status_firefox133": "verified",
        "cf_status_firefox_esr128": "affected",
        "comment": {
            "body": "Verified bug as fixed.",
            "is_private": False,
            "is_markdown": True,
        },
        "flags": [
            {
                "is_multiplicable": True,
                "name": "needinfo",
                "requestee": "dev@example.com",
                "status": "?",
            }
        ],
    }


def test_validate_bug_data_accepts_bugmon_diff(full_diff):
    """A diff limited to bugmon's own modifications passes validation"""
    bug_data = {"bug_number": 123456, "diff": full_diff, "trace_available": True}
    result = validate_bug_data(bug_data, 123456)

    assert result == bug_data


def test_validate_bug_data_defaults_trace_available_to_false():
    """A missing trace_available key must not enable trace submission"""
    result = validate_bug_data({"bug_number": 123456, "diff": {}}, 123456)

    assert result["trace_available"] is False


@pytest.mark.parametrize(
    "bug_number",
    [654321, "123456", "123456/../../user", None, True],
)
def test_validate_bug_data_rejects_bug_number_mismatch(bug_number):
    """Bug numbers that do not exactly match the expected int are rejected"""
    bug_data = {"bug_number": bug_number, "diff": {}, "trace_available": False}
    with pytest.raises(BugmonTaskError, match="Bug number mismatch"):
        validate_bug_data(bug_data, 123456)


@pytest.mark.parametrize(
    "diff",
    [
        {"groups": {"remove": ["core-security"]}},
        {"cc": {"add": ["attacker@example.com"]}},
        {"assigned_to": "attacker@example.com"},
        {"resolution": "FIXED"},
        {"status": "RESOLVED"},
        {"keywords": {"add": ["sec-critical"]}},
        {"keywords": {"remove": ["sec-high"]}},
        {"keywords": {"set": ["bugmon"]}},
        {"comment": {"body": "hidden", "is_private": "yes"}},
        {"comment": {"body": 123}},
        {"cf_status_firefox133": "wontfix"},
        {"cf_tracking_firefox133": "+"},
        {"whiteboard": 123},
        "not-a-dict",
    ],
)
def test_validate_bug_data_rejects_unexpected_diff(diff):
    """Fields and values outside bugmon's repertoire are rejected"""
    bug_data = {"bug_number": 123456, "diff": diff, "trace_available": False}
    with pytest.raises(BugmonTaskError):
        validate_bug_data(bug_data, 123456)


def test_validate_bug_data_accepts_private_comments():
    """Private comments are permitted"""
    diff = {"comment": {"body": "sensitive", "is_private": True}}
    bug_data = {"bug_number": 123456, "diff": diff, "trace_available": False}

    assert validate_bug_data(bug_data, 123456) == bug_data


def test_validate_bug_data_rejects_unexpected_top_level_keys():
    """Unknown top-level artifact keys are rejected"""
    bug_data = {"bug_number": 123456, "diff": {}, "extra": True}
    with pytest.raises(BugmonTaskError, match="Malformed processor artifact"):
        validate_bug_data(bug_data, 123456)


def test_validate_bug_data_sanitizes_flags(full_diff):
    """Flag entries other than new needinfo requests are dropped"""
    full_diff["flags"].extend(
        [
            {"name": "approval-mozilla-release", "status": "+"},
            {"id": 12345, "name": "needinfo", "status": "?"},
        ]
    )
    bug_data = {"bug_number": 123456, "diff": full_diff, "trace_available": False}
    result = validate_bug_data(bug_data, 123456)

    assert result["diff"]["flags"] == [
        {
            "is_multiplicable": True,
            "name": "needinfo",
            "requestee": "dev@example.com",
            "status": "?",
        }
    ]


def test_resolve_bug_number_from_value():
    """A bug number from the trusted task definition takes precedence"""
    assert resolve_bug_number(123456, Path("artifact.json")) == 123456


def test_resolve_bug_number_from_artifact_name(tmp_path):
    """The monitor-written artifact filename is used as a fallback"""
    artifact = tmp_path / "processor-result-123456-parent.json"

    assert resolve_bug_number(None, artifact) == 123456


def test_resolve_bug_number_unavailable(tmp_path):
    """An error is raised when no trusted source is available"""
    with pytest.raises(BugmonTaskError, match="expected bug number"):
        resolve_bug_number(None, tmp_path / "artifact.json")
