# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

from bugsy import Bugsy

from ..common import (
    get_bugzilla_auth,
    in_taskcluster,
    fetch_json_artifact,
    queue,
    BugzillaCreds,
)
from ..common.cli import base_parser
from .validation import resolve_bug_number, validate_bug_data

LOG = logging.getLogger(__name__)


def update_bug(bug_data: Dict[str, Any], bz_creds: BugzillaCreds) -> None:
    """Update bug.

    :param bug_data: Processed bug data
    :param bz_creds: Bugzilla credentials
    """
    bugsy = Bugsy(api_key=bz_creds["KEY"], bugzilla_url=bz_creds["URL"])
    bugsy.request(f"bug/{bug_data['bug_number']}", "PUT", json=bug_data["diff"])

    # Log changes
    comment = bug_data["diff"].pop("comment", None)
    LOG.info(f"Committing ({bug_data['bug_number']}): {json.dumps(bug_data['diff'])}")

    if comment is not None:
        for line in comment["body"].splitlines():
            LOG.info(f">{line}")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse arguments"""
    parser = base_parser(prog="BugmonReporter")
    parser.add_argument("processor_artifact", type=Path, help="Path to bug artifact")
    parser.add_argument(
        "--bug-number",
        type=int,
        default=os.environ.get("BUG_NUMBER"),
        help="Expected bug number (defaults to the BUG_NUMBER env variable).",
    )

    args = parser.parse_args(args=argv)

    logging.basicConfig(level=logging.INFO)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not in_taskcluster():
        if not args.processor_artifact.exists():
            parser.error(f"Cannot find path {args.processor_artifact}!")

    return args


def main(argv: Optional[List[str]] = None) -> None:
    """Report processed results"""
    args = parse_args(argv)
    bug_number = resolve_bug_number(args.bug_number, args.processor_artifact)

    if in_taskcluster():
        task = queue.task(os.getenv("TASK_ID"))
        dependencies = task.get("dependencies")
        bug_data = fetch_json_artifact(dependencies[-1], args.processor_artifact)
    else:
        bug_data = json.loads(args.processor_artifact.read_text())

    bug_data = validate_bug_data(bug_data, bug_number)

    bz_creds = get_bugzilla_auth()
    update_bug(bug_data, bz_creds)
