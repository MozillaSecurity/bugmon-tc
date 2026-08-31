# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..common import BugmonTaskError

LOG = logging.getLogger(__name__)

# The processor artifact is produced by the processor task, which executes
# arbitrary testcases.  Its contents must be limited to the fields and
# values bugmon can legitimately produce before being applied with the
# privileged Bugzilla API key.
ARTIFACT_KEYS = frozenset({"bug_number", "diff", "trace_available"})
ALLOWED_STATUSES = frozenset({"REOPENED", "VERIFIED"})
KEYWORD_ACTIONS = frozenset({"add", "remove"})
KEYWORD_ADDS = frozenset({"pernosco", "regression"})
KEYWORD_REMOVES = frozenset({"bugmon", "pernosco-wanted"})
CF_STATUS_PATTERN = re.compile(r"^cf_status_firefox(?:\d+|_esr\d+)$")
CF_STATUS_VALUES = frozenset({"affected", "verified"})
COMMENT_KEYS = frozenset({"body", "is_private", "is_markdown"})
# Inverse of ProcessorTask.dest in monitor/tasks.py
PROCESSOR_ARTIFACT_PATTERN = re.compile(r"^processor-result-(\d+)-")


def resolve_bug_number(bug_number: Optional[int], artifact_path: Path) -> int:
    """Determine the bug number this reporter task was created for.

    :param bug_number: Bug number from the --bug-number arg or BUG_NUMBER env
    :param artifact_path: Path to the processor artifact
    :raises BugmonTaskError: If the expected bug number cannot be determined
    """
    if bug_number is not None:
        return bug_number

    # Fallback for tasks created before BUG_NUMBER was added to the reporter env
    match = PROCESSOR_ARTIFACT_PATTERN.match(artifact_path.name)
    if match is not None:
        LOG.warning("BUG_NUMBER not set; using the artifact name to identify the bug")
        return int(match.group(1))

    raise BugmonTaskError("Unable to determine the expected bug number!")


def _validate_keywords(value: Any) -> None:
    """Verify that keyword changes are limited to those bugmon performs

    :param value: The keywords entry from the bug diff
    :raises BugmonTaskError: If the keyword changes are not recognized
    """
    if not isinstance(value, dict) or not value or not set(value) <= KEYWORD_ACTIONS:
        raise BugmonTaskError(f"Unexpected keyword modification: {value!r}")

    for action, allowed in (("add", KEYWORD_ADDS), ("remove", KEYWORD_REMOVES)):
        entries = value.get(action, [])
        if (
            not isinstance(entries, list)
            or not all(isinstance(entry, str) for entry in entries)
            or not set(entries) <= allowed
        ):
            raise BugmonTaskError(f"Unexpected keyword {action}: {entries!r}")


def _validate_comment(value: Any) -> None:
    """Verify that the comment matches the shape bugmon produces

    :param value: The comment entry from the bug diff
    :raises BugmonTaskError: If the comment is not recognized
    """
    if not isinstance(value, dict) or not set(value) <= COMMENT_KEYS:
        raise BugmonTaskError(f"Unexpected comment format: {value!r}")
    if not isinstance(value.get("body"), str):
        raise BugmonTaskError("Invalid comment body!")
    for key in ("is_private", "is_markdown"):
        if not isinstance(value.get(key, False), bool):
            raise BugmonTaskError(f"Invalid comment {key}!")


def _sanitize_flags(value: Any) -> List[Dict[str, Any]]:
    """Keep only the needinfo requests bugmon creates.

    Bugsy diffs the flags field as a full replacement list, so legitimate
    diffs may include the bug's pre-existing flags.  Omitting them from the
    update leaves them unchanged in Bugzilla, while forwarding them verbatim
    would allow a compromised processor to set arbitrary flags (e.g.
    approvals).

    :param value: The flags entry from the bug diff
    :raises BugmonTaskError: If the flags entry is not a list
    """
    if not isinstance(value, list):
        raise BugmonTaskError(f"Unexpected flags format: {value!r}")

    sanitized = []
    for flag in value:
        if (
            isinstance(flag, dict)
            and flag.get("name") == "needinfo"
            and flag.get("status") == "?"
            and "id" not in flag
            and isinstance(flag.get("requestee"), str)
        ):
            sanitized.append(
                {
                    "is_multiplicable": True,
                    "name": "needinfo",
                    "requestee": flag["requestee"],
                    "status": "?",
                }
            )
        else:
            LOG.warning(f"Dropping unexpected flag modification: {flag!r}")

    return sanitized


def _validate_diff(diff: Any) -> Dict[str, Any]:
    """Verify that the diff only touches fields and values bugmon can produce

    :param diff: The diff entry from the processor artifact
    :raises BugmonTaskError: If the diff contains unexpected data
    """
    if not isinstance(diff, dict):
        raise BugmonTaskError("Malformed processor artifact!")

    validated = dict(diff)
    for field, value in diff.items():
        if field == "whiteboard":
            if not isinstance(value, str):
                raise BugmonTaskError("Invalid whiteboard!")
        elif field == "status":
            if value not in ALLOWED_STATUSES:
                raise BugmonTaskError(f"Unexpected status: {value!r}")
        elif field == "keywords":
            _validate_keywords(value)
        elif field == "comment":
            _validate_comment(value)
        elif field == "flags":
            validated["flags"] = _sanitize_flags(value)
        elif CF_STATUS_PATTERN.match(field):
            if value not in CF_STATUS_VALUES:
                raise BugmonTaskError(f"Unexpected value for {field}: {value!r}")
        else:
            raise BugmonTaskError(f"Unexpected field in bug diff: {field!r}")

    return validated


def validate_bug_data(bug_data: Any, expected_bug_number: int) -> Dict[str, Any]:
    """Validate the processor artifact against what bugmon can legitimately produce.

    :param bug_data: Processor artifact contents
    :param expected_bug_number: Bug number from the trusted task definition
    :raises BugmonTaskError: If the artifact contains unexpected data
    """
    if not isinstance(bug_data, dict) or not set(bug_data) <= ARTIFACT_KEYS:
        raise BugmonTaskError("Malformed processor artifact!")

    bug_number = bug_data.get("bug_number")
    if bug_number != expected_bug_number:
        raise BugmonTaskError(
            f"Bug number mismatch (expected {expected_bug_number}, "
            f"found {bug_number!r})!"
        )

    trace_available = bug_data.get("trace_available", False)
    if not isinstance(trace_available, bool):
        raise BugmonTaskError("Malformed processor artifact!")

    return {
        "bug_number": expected_bug_number,
        "diff": _validate_diff(bug_data.get("diff")),
        "trace_available": trace_available,
    }
