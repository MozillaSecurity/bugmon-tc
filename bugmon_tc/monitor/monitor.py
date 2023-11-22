# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Iterator

from bugsy import Bugsy
from bugmon import BugMonitor, BugmonException
from bugmon.bug import EnhancedBug
from taskcluster import slugId

from .tasks import ProcessorTask, ReporterTask
from ..common import queue, in_taskcluster

LOG = logging.getLogger(__name__)

QUERY = {
    "query_format": "advanced",
    "keywords": "bugmon",
    "keywords_type": "anywords",
    "chfield": "[Bug creation]",
    "chfieldfrom": "2020-03-01",
    "include_fields": "_default",
}

CONFIRMABLE = [
    "ASSIGNED",
    "NEW",
    "UNCONFIRMED",
    "REOPENED",
]


class MonitorError(Exception):
    """Exception for monitor issues"""


def needs_force_confirmed(force_confirm: bool, bug: EnhancedBug) -> bool:
    """Determine if bug is eligible for forced confirmation"""
    return force_confirm and bug.status in [
        "ASSIGNED",
        "NEW",
        "UNCONFIRMED",
        "REOPENED",
    ]


class BugMonitorTask(object):
    """Class for generating bugmon taskgraph"""

    def __init__(
        self,
        api_key: str,
        api_root: str,
        force_confirm: bool = False,
    ) -> None:
        """

        :param api_key: BZ_API_KEY
        :param api_root: BZ_API_ROOT
        :param force_confirm: Boolean indicating if bugs should be confirmed regardless of whiteboard
        """
        self.bugsy = Bugsy(api_key=api_key, bugzilla_url=api_root)
        self.force_confirm = force_confirm

    def fetch_bugs(self) -> Iterator[EnhancedBug]:
        """
        Generate EnhancedBug instances for all actionable bugs

        :return: list of EnhancedBug
        """
        response = self.bugsy.request("bug", params=QUERY)
        bugs = [EnhancedBug(self.bugsy, **bug) for bug in response["bugs"]]
        for bug in sorted(bugs, key=lambda bug: bug.id):
            if self.is_actionable(bug):
                yield EnhancedBug.cache_bug(bug)

    def is_actionable(self, bug: EnhancedBug) -> bool:
        """
        Determine which action, if any, can be performed on the bug

        :param bug: Bug to analyse
        :return: bool
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                bugmon = BugMonitor(self.bugsy, bug, Path(temp_dir))
                LOG.info(f"Analyzing bug {bug.id} (Status: {bug.status})")

                # If the bug is not supported, we still want to close it out
                if not bugmon.is_supported():
                    LOG.info(f"Bug {bug.id} not supported - queuing for removal")
                    return True

                if any(
                    [
                        bugmon.needs_verify(),
                        bugmon.needs_confirm(),
                        bugmon.needs_bisect(),
                        bugmon.needs_pernosco(),
                        self.force_confirm and bug.status in CONFIRMABLE,
                    ]
                ):
                    LOG.info(f"Queuing bug {bug.id} for processing")
                    return True

            except BugmonException as e:
                LOG.error(f"Error processing bug {bug.id}: {e}")

        return False

    def create_tasks(self, artifact_dir: Path) -> None:
        """Fetch all bugs and generate artifacts representing the tasks that need to be
        performed on those bugs"""

        for bug in self.fetch_bugs():
            parent_id = os.getenv("TASK_ID") if in_taskcluster() else slugId()
            monitor_path = Path(f"monitor-{bug.id}-{parent_id}.json")

            if not artifact_dir.exists():
                artifact_dir.mkdir(parents=True)

            # Write monitor artifact
            with (artifact_dir / monitor_path).open("w") as file:
                bug_data = bug.to_json()
                json.dump(json.loads(bug_data), file, indent=2)

            use_pernosco = (
                "pernosco" in bug.commands or "pernosco-wanted" in bug.keywords
            )
            processor = ProcessorTask(
                parent_id,
                bug.id,
                monitor_path,
                use_pernosco=use_pernosco,
                force_confirm=self.force_confirm,
            )
            reporter = ReporterTask(
                parent_id,
                bug.id,
                processor.dest,
                dep=processor.id,
                trace_path=processor.trace_dest,
            )

            if in_taskcluster():
                queue.createTask(processor.id, processor.task)
                queue.createTask(reporter.id, reporter.task)
            else:
                processor_task_path = f"processor-task-{bug.id}-{parent_id}.json"
                reporter_task_path = f"reporter-task-{bug.id}-{parent_id}.json"
                with (artifact_dir / processor_task_path).open("w") as file:
                    json.dump(processor.task, file, indent=2)
                with (artifact_dir / reporter_task_path).open("w") as file:
                    json.dump(reporter.task, file, indent=2)
