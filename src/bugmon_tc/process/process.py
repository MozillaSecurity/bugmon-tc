# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os
import tempfile
from pathlib import Path

from bugmon import BugMonitor
from bugmon.bug import EnhancedBug

from ..common import queue

LOG = logging.getLogger(__name__)


class ProcessorError(Exception):
    """Exception for processor issues"""


class TaskProcessor(object):
    """
    Class for processing monitor tasks
    """

    def __init__(self, dry_run, artifact_path):
        self.dry_run = dry_run
        self.artifact_path = artifact_path

    @property
    def in_taskcluster(self):
        """
        Helper to determine if we're in a taskcluster worker

        :return: bool
        """
        return "TASK_ID" in os.environ and "TASKCLUSTER_ROOT_URL" in os.environ

    def fetch_artifact(self):
        """
        Retrieve artifact for processing

        :return: EnhancedBug
        """
        if self.in_taskcluster:
            task = queue.task(os.getenv("TASK_ID"))
            parent_id = task.get("taskGroupId")
            LOG.info(f"Fetching artifact: {parent_id} {self.artifact_path}")
            data = queue.getLatestArtifact(parent_id, self.artifact_path)
        else:
            with open(self.artifact_path, "r") as file:
                data = json.load(file)

        if data is None:
            raise ProcessorError("Failed to retrieve artifact")

        return EnhancedBug(bugsy=None, **data)

    def process(self, force_confirm=False):
        """
        Process monitor artifact and write the results to disk

        :param force_confirm: Boolean indicating if bug should be confirmed regardless of state
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            bug = self.fetch_artifact()
            bugmon = BugMonitor(None, bug, Path(temp_dir), self.dry_run)
            LOG.info(f"Processing bug {bug.id} (Status: {bug.status})")
            bugmon.process(force_confirm)

            return {"bug_number": bug.id, "diff": bug.diff()}
