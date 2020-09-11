# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os
from pathlib import Path

from bugsy import Bugsy

from ..common import queue
from ..common.cli import base_parser

LOG = logging.getLogger(__name__)


def in_taskcluster():
    """
    Helper to determine if we're in a taskcluster worker

    :return: bool
    """
    return "TASK_ID" in os.environ and "TASKCLUSTER_ROOT_URL" in os.environ


def report(api_key, api_root, artifact_path, dry_run=False):
    """
    Report resuls to bugzilla

    :param api_key: BZ_API_KEY
    :param api_root: BZ_API_ROOT
    :param artifact_path: Path to processor artifact
    :param dry_run: Boolean indicating if bugs should be updated
    """
    if in_taskcluster():
        task = queue.task(os.getenv("TASK_ID"))
        dependencies = task.get("dependencies")
        data = queue.getLatestArtifact(dependencies[-1], artifact_path)
    else:
        with open(artifact_path, "r") as file:
            data = json.load(file)

    bug_number = data["bug_number"]
    diff = data["diff"]

    if not dry_run:
        bugsy = Bugsy(api_key=api_key, bugzilla_url=api_root)
        bugsy.request(f"bug/{bug_number}", "PUT", json=diff)

    # Log changes
    comment = diff.pop("comment", None)
    LOG.info(f"Commit changes ({bug_number}): {json.dumps(diff)}")

    if comment is not None:
        for line in comment.splitlines():
            LOG.info(f">{line}")


def main(argv=None):
    """
    Report processed results
    """
    parser = base_parser(prog="BugmonReporter")
    parser.add_argument("artifact", type=str, help="Path to artifact")
    parser.add_argument(
        "--api-root",
        type=str,
        help="The target bugzilla instance",
        default=os.environ.get("BZ_API_ROOT"),
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="The bugzilla API key",
        default=os.environ.get("BZ_API_KEY"),
    )

    args = parser.parse_args(args=argv)
    if args.api_root is None or args.api_key is None:
        raise parser.error("BZ_API_ROOT and BZ_API_KEY must be set!")

    logging.basicConfig(level=args.log_level)

    report(args.api_key, args.api_root, args.artifact, args.dry_run)
