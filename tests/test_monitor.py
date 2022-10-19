# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json

import pytest
from bugmon.bug import EnhancedBug

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.monitor.cli import main as monitor_cli
from bugmon_tc.monitor.monitor import BugMonitorTask


def test_monitor_cli_missing_args():
    """Test that monitor CLI raises when missing BZ_* args"""
    with pytest.raises(BugmonTaskError):
        monitor_cli(None)


def test_monitor_fetch_bug(mocker, tmp_path, bug_data):
    """Test bug retrieval and iteration"""
    bug_response = {"bugs": [bug_data]}
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)

    cached_bug = EnhancedBug(None, **bug_data)
    mocker.patch("bugmon.bug.EnhancedBug.cache_bug", return_value=cached_bug)

    monitor = BugMonitorTask("key", "root", tmp_path)
    result = list(monitor.fetch_bugs())
    assert len(result) == 1
    assert isinstance(result[0], EnhancedBug)


@pytest.mark.parametrize("command", ["verify", "confirm", "bisect", None])
def test_monitor_is_actionable(mocker, tmp_path, bug_data, command):
    """Test that BugMonitorTask.is_actionable matches expected state"""
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    monitor = BugMonitorTask("key", "root", tmp_path)
    bug_data["whiteboard"] = f"[bugmon:{command}"
    bug = EnhancedBug(bugsy=None, **bug_data)

    # Change status to avoid unspecified actions
    bug.status = "RESOLVED"

    if command is None:
        assert monitor.is_actionable(bug) is False
    else:
        assert monitor.is_actionable(bug) is True


def test_monitor_create_tasks_local(mocker, tmp_path, bug_data):
    """Test task creation"""
    bug_response = {"bugs": [bug_data]}
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    mocker.patch("bugmon_tc.monitor.monitor.slugId", return_value="1")
    mocker.patch("bugmon_tc.monitor.monitor.in_taskcluster", return_value=False)

    cached_bug = EnhancedBug(None, **bug_data)
    mocker.patch("bugmon.bug.EnhancedBug.cache_bug", return_value=cached_bug)

    monitor = BugMonitorTask("key", "root", tmp_path)
    monitor.create_tasks(tmp_path)
    monitor_artifact = tmp_path / f"monitor-{bug_data['id']}-1.json"

    with monitor_artifact.open() as f:
        assert json.load(f) == bug_data


def test_monitor_create_tasks_taskcluster(mocker, tmp_path, bug_data):
    """Test task creation in simulated TC environment"""
    bug_response = {"bugs": [bug_data]}
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    mocker.patch("bugmon_tc.monitor.monitor.in_taskcluster", return_value=True)

    cached_bug = EnhancedBug(None, **bug_data)
    mocker.patch("bugmon.bug.EnhancedBug.cache_bug", return_value=cached_bug)

    monitor = BugMonitorTask("key", "root", tmp_path)

    mocked_create_task = mocker.patch("bugmon_tc.common.queue.createTask")
    monitor.create_tasks(tmp_path)
    assert mocked_create_task.call_count == 2
