# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os
from pathlib import Path

from bugsy import Bugsy

from bugmon.utils import (
    download_zip_archive,
    get_source_url,
    submit_pernosco,
    is_pernosco_available,
)

from ..common import (
    fetch_trace_artifact,
    BugmonTaskError,
    get_bugzilla_auth,
    get_pernosco_auth,
    in_taskcluster,
    fetch_artifact,
    queue,
)
from ..common.cli import base_parser

LOG = logging.getLogger(__name__)


def update_bug(bug_data, bz_creds):
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


def submit_trace(bug_data, trace_artifact, pernosco_creds):
    """Submit pernosco trace

    :param bug_data: Processed bug data
    :param trace_artifact: Trace artifact path
    :param pernosco_creds: Pernosco credentials
    """
    if not is_pernosco_available():
        raise BugmonTaskError("Cannot find working instance of pernosco-submit!")

    LOG.info("Attempting to submit pernosco trace (this may take a while)...")

    LOG.info(f"Unpacking trace artifact: {trace_artifact}")
    with fetch_trace_artifact(trace_artifact) as trace_dir:
        build_info_path = trace_dir / "build.json"
        if not build_info_path.exists():
            raise BugmonTaskError("Cannot find build.json in trace archive.")

        build_info = json.loads(build_info_path.read_text())
        source_archive_url = get_source_url(build_info["branch"], build_info["rev"])
        LOG.info(f"Unpacking source archive: {source_archive_url}")
        with download_zip_archive(source_archive_url) as source_dir:
            LOG.info("Uploading pernosco session...")

            env = {"PATH": os.environ.get("PATH"), **pernosco_creds}
            submit_pernosco(trace_dir, source_dir, bug_data["bug_number"], env)


def parse_args(argv):
    """Parse arguments"""
    parser = base_parser(prog="BugmonReporter")
    parser.add_argument("processor_artifact", type=Path, help="Path to bug artifact")
    parser.add_argument(
        "--trace-artifact",
        type=Path,
        help="Path to store the rr trace archive.",
    )

    args = parser.parse_args(args=argv)
    logging.basicConfig(level=args.log_level)

    return args


def main(argv=None):
    """Report processed results"""
    args = parse_args(argv)
    bz_creds = get_bugzilla_auth()

    if in_taskcluster():
        task = queue.task(os.getenv("TASK_ID"))
        dependencies = task.get("dependencies")
        bug_data = fetch_artifact(dependencies[-1], str(args.processor_artifact))
    else:
        bug_data = json.loads(args.processor_artifact.read_text())

    if args.trace_artifact is not None:
        pernosco_creds = get_pernosco_auth()
        submit_trace(bug_data, str(args.trace_artifact), pernosco_creds)

    update_bug(bug_data, bz_creds)
