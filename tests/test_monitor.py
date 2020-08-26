# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json

import pytest
from bugmon.bug import EnhancedBug

from bugmon_tc.monitor.cli import main as monitor_cli
from bugmon_tc.monitor.monitor import BugMonitorTask


def test_monitor_cli_missing_args():
    """ Test that monitor CLI raises when missing BZ_* args """
    with pytest.raises(SystemExit):
        monitor_cli(None)


def test_monitor_fetch_bug(mocker, tmp_path, bug_response):
    """ Test bug retrieval and iteration """
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    monitor = BugMonitorTask("key", "root", tmp_path, dry_run=True)
    result = list(monitor.fetch_bugs())
    assert len(result) == 1
    assert isinstance(result[0], EnhancedBug)


@pytest.mark.parametrize("command", ["verify", "confirm", "bisect", None])
def test_monitor_is_actionable(mocker, tmp_path, bug_fixture, command):
    """ Test that BugMonitorTask.is_actionable matches expected state """
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    monitor = BugMonitorTask("key", "root", tmp_path, dry_run=True)
    bug_fixture["whiteboard"] = f"[bugmon:{command}"
    bug = EnhancedBug(bugsy=None, **bug_fixture)

    # Change status to avoid unspecified actions
    bug.status = "RESOLVED"

    if command is None:
        assert monitor.is_actionable(bug) is False
    else:
        assert monitor.is_actionable(bug) is True


@pytest.mark.parametrize("is_enabled", [True, False])
def test_monitor_in_taskcluster(monkeypatch, is_enabled):
    """ Test that BugMonitorTask.in_taskcluster matches env state """
    monitor = BugMonitorTask("key", "root", None)
    if is_enabled:
        monkeypatch.setenv("TASK_ID", "1")
        monkeypatch.setenv("TASKCLUSTER_ROOT_URL", "1")
    else:
        # Ensure neither env variable is set
        monkeypatch.delenv("TASK_ID", False)
        monkeypatch.delenv("TASKCLUSTER_ROOT_URL", False)

    assert monitor.in_taskcluster is is_enabled


def test_monitor_create_tasks_local(
    mocker, tmp_path, bug_response, processor_task, reporter_task
):
    """ Test task creation """
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    mocker.patch("bugmon_tc.monitor.tasks.slugId", return_value="1")
    mocker.patch(
        "bugmon_tc.monitor.monitor.BugMonitorTask.in_taskcluster",
        new_callable=mocker.PropertyMock,
        return_value=False,
    )

    mocker.patch("uuid.uuid1", return_value=123)

    monitor = BugMonitorTask("key", "root", tmp_path, dry_run=True)
    monitor.create_tasks()

    files = list(tmp_path.glob("*"))
    assert len(files) == 3
    for prefix in ["monitor", "process", "reporter"]:
        assert f"{prefix}-123.json" in [file.name for file in files]

    for file in files:
        with file.open() as f:
            data = json.load(f)
            if file.name.startswith("monitor"):
                assert data == bug_response["bugs"][0]
            elif file.name.startswith("process"):
                assert data == processor_task
            elif file.name.startswith("report"):
                assert data == reporter_task


def test_monitor_create_tasks_taskcluster(mocker, tmp_path, bug_response):
    """ Test task creation in simulated TC environment """
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    mocker.patch(
        "bugmon_tc.monitor.monitor.BugMonitorTask.in_taskcluster",
        new_callable=mocker.PropertyMock,
        return_value=True,
    )

    monitor = BugMonitorTask("key", "root", tmp_path, dry_run=True)

    mocked_create_task = mocker.patch("bugmon_tc.common.queue.createTask")
    monitor.create_tasks()
    assert mocked_create_task.call_count == 2
