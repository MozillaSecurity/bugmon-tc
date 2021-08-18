# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os
import tempfile
from pathlib import Path

from bugsy import Bugsy
from bugmon import BugMonitor, BugmonException
from bugmon.bug import EnhancedBug
from taskcluster import slugId

from .tasks import ProcessorTask, ReporterTask
from ..common import queue

LOG = logging.getLogger(__name__)

QUERY = {
    "query_format": "advanced",
    "keywords": "bugmon",
    "keywords_type": "anywords",
    "chfield": "[Bug creation]",
    "chfieldfrom": "2020-08-19",
    "include_fields": "_default",
}


class MonitorError(Exception):
    """Exception for monitor issues"""


class BugMonitorTask(object):
    """
    Class for generating bugmon taskgraph
    """

    def __init__(self, api_key, api_root, artifact_dir, **kwargs):
        """

        :param api_key: BZ_API_KEY
        :param api_root: BZ_API_ROOT
        :param artifact_dir: Path to store artifacts
        :param dry_run: Boolean indicating if bugs should be updated
        """
        self.bugsy = Bugsy(api_key=api_key, bugzilla_url=api_root)
        self.artifact_dir = artifact_dir
        self.force_confirm = kwargs.get("force_confirm", False)
        self.dry_run = kwargs.get("dry_run", False)

    @property
    def in_taskcluster(self):
        """
        Helper to determine if we're in a taskcluster worker

        :return: bool
        """
        return "TASK_ID" in os.environ and "TASKCLUSTER_ROOT_URL" in os.environ

    def fetch_bugs(self):
        """
        Generate EnhancedBug instances for all actionable bugs

        :return: list of EnhancedBug
        """
        response = self.bugsy.request("bug", params=QUERY)
        bugs = [EnhancedBug(self.bugsy, **bug) for bug in response["bugs"]]
        for bug in sorted(bugs, key=lambda bug: bug.id):
            if self.is_actionable(bug):
                yield EnhancedBug.cache_bug(bug)

    def is_actionable(self, bug):
        """
        Determine which action, if any, can be performed on the bug

        :param bug: Bug to analyse
        :return: bool
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                bugmon = BugMonitor(self.bugsy, bug, Path(temp_dir), self.dry_run)
                LOG.info(f"Analyzing bug {bug.id} (Status: {bug.status})")

                if bugmon.is_supported():
                    if bugmon.needs_verify():
                        LOG.info(f"Queuing bug {bug.id} for verification")
                        return True
                    if bugmon.needs_confirm():
                        LOG.info(f"Queuing bug {bug.id} for confirmation")
                        return True
                    if bugmon.needs_bisect():
                        LOG.info(f"Queuing bug {bug.id} for bisection")
                        return True
                    if self.force_confirm and bug.status in [
                        "ASSIGNED",
                        "NEW",
                        "UNCONFIRMED",
                        "REOPENED",
                    ]:
                        return True

            except BugmonException as e:
                LOG.error(f"Error processing bug {bug.id}: {e}")

        return False

    def create_tasks(self):
        """
        Fetch all bugs and generate artifacts representing the tasks that need to be
        performed on those bugs
        """

        for bug in self.fetch_bugs():
            parent_id = os.getenv("TASK_ID") if self.in_taskcluster else slugId()
            monitor_path = f"monitor-{bug.id}-{parent_id}.json"

            # Write monitor artifact
            with open(os.path.join(self.artifact_dir, monitor_path), "w") as file:
                bug_data = bug.to_json()
                json.dump(json.loads(bug_data), file, indent=2)

            processor = ProcessorTask(
                parent_id,
                monitor_path,
                bug.id,
                force_confirm=self.force_confirm,
            )
            reporter = ReporterTask(parent_id, processor.dest, bug.id, dep=processor.id)

            if self.in_taskcluster:
                queue.createTask(processor.id, processor.task)
                queue.createTask(reporter.id, reporter.task)
