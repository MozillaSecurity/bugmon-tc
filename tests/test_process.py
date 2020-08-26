# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import os

import pytest
from bugmon.bug import EnhancedBug

from bugmon_tc.process.process import TaskProcessor


@pytest.mark.parametrize("is_enabled", [True, False])
def test_processor_in_taskcluster(monkeypatch, is_enabled):
    """ Test that TaskProcessor.in_taskcluster matches env state """
    monitor = TaskProcessor(None)
    if is_enabled:
        monkeypatch.setenv("TASK_ID", "1")
        monkeypatch.setenv("TASKCLUSTER_ROOT_URL", "1")
    else:
        # Ensure neither env variable is set
        monkeypatch.delenv("TASK_ID", False)
        monkeypatch.delenv("TASKCLUSTER_ROOT_URL", False)

    assert monitor.in_taskcluster is is_enabled


@pytest.mark.parametrize("in_taskcluster", [True, False])
def test_processor_fetch_artifact(
    monkeypatch, mocker, tmp_path, in_taskcluster, bug_fixture
):
    """ Test fetching of artifact retrieval """
    if in_taskcluster:
        monkeypatch.setenv("TASK_ID", "0")
        mocker.patch("bugmon_tc.common.queue.task", return_value={"taskGroupId": 0})
        mocker.patch(
            "bugmon_tc.common.queue.getLatestArtifact", return_value=bug_fixture
        )
        mocker.patch(
            "bugmon_tc.process.process.TaskProcessor.in_taskcluster",
            new_callable=mocker.PropertyMock,
            return_value=True,
        )

        processor = TaskProcessor(None)
        bug = processor.fetch_artifact()
    else:
        artifact_path = os.path.join(tmp_path, "artifact.json")
        with open(artifact_path, "w") as file:
            json.dump(bug_fixture, file, indent=2)

        processor = TaskProcessor(artifact_path)
        bug = processor.fetch_artifact()

    assert isinstance(bug, EnhancedBug)
