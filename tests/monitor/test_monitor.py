# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
from unittest.mock import MagicMock

import pytest
from bugmon import BugmonException
from bugmon.bug import EnhancedBug

from bugmon_tc.monitor.monitor import BugMonitorTask, needs_force_confirmed


@pytest.mark.parametrize("status", ["ASSIGNED", "NEW", "UNCONFIRMED", "REOPENED"])
def test_needs_force_confirm_true(bug_data, status):
    """Test that applicable bugs can be confirmed when the force flag is set"""
    bug_data["status"] = status
    bug = EnhancedBug(None, **bug_data)
    assert needs_force_confirmed(True, bug) is True


def test_needs_force_confirm_false(bug_data):
    """Test that bugs with an invalid state will not be marked as confirmable"""
    bug_data["status"] = "RESOLVED"
    bug = EnhancedBug(None, **bug_data)
    assert needs_force_confirmed(True, bug) is False


def test_monitor_fetch_bug(mocker, tmp_path, bug_data):
    """Test bug retrieval and iteration"""
    bug_response = {"bugs": [bug_data]}
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=False)

    cached_bug = EnhancedBug(None, **bug_data)
    mocker.patch("bugmon.bug.EnhancedBug.cache_bug", return_value=cached_bug)

    monitor = BugMonitorTask("key", "root")
    result = list(monitor.fetch_bugs())
    assert len(result) == 1
    assert isinstance(result[0], EnhancedBug)


@pytest.mark.parametrize(
    "action",
    [
        "bisect",
        "confirm",
        "pernosco",
        "verify",
    ],
)
def test_is_actionable_needs_analysis(mocker, action):
    """Test that is_actionable returns true for bugs requiring attention"""
    mock_monitor = mocker.patch("bugmon_tc.monitor.monitor.BugMonitor", autospec=True)
    if action == "bisect":
        mock_monitor.needs_bisect.return_value = True
    elif action == "confirm":
        mock_monitor.needs_confirm.return_value = True
    elif action == "pernosco":
        mock_monitor.needs_pernosco.return_value = True
    elif action == "verify":
        mock_monitor.needs_verify.return_value = True

    bug = MagicMock(spec=EnhancedBug, id=12345, status="NEW")
    monitor = BugMonitorTask("", "", force_confirm=False)
    assert monitor.is_actionable(bug) is True


def test_is_actionable_no_valid_actions(mocker):
    """Test that is_actionable returns false for bugs with no valid action"""
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=True)
    mocker.patch("bugmon.BugMonitor.needs_bisect", return_value=False)
    mocker.patch("bugmon.BugMonitor.needs_confirm", return_value=False)
    mocker.patch("bugmon.BugMonitor.needs_pernosco", return_value=False)
    mocker.patch("bugmon.BugMonitor.needs_verify", return_value=False)

    bug = MagicMock(spec=EnhancedBug, id=12345, status="RESOLVED")
    monitor = BugMonitorTask("", "", force_confirm=False)
    assert monitor.is_actionable(bug) is False


def test_is_actionable_throws(mocker):
    """Test that is_actionable returns false if BugMonitor throws a BugmonException"""
    mocker.patch(
        "bugmon_tc.monitor.monitor.BugMonitor", side_effect=BugmonException("Error!")
    )
    bug = MagicMock(spec=EnhancedBug, id=12345, status="NEW")
    monitor = BugMonitorTask("", "", force_confirm=False)
    assert monitor.is_actionable(bug) is False


def test_monitor_create_tasks_local(mocker, tmp_path, bug_data):
    """Test task creation"""
    bug_response = {"bugs": [bug_data]}
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=False)
    mocker.patch("bugmon_tc.monitor.monitor.slugId", return_value="1")
    mocker.patch("bugmon_tc.monitor.monitor.in_taskcluster", return_value=False)

    cached_bug = EnhancedBug(None, **bug_data)
    mocker.patch("bugmon.bug.EnhancedBug.cache_bug", return_value=cached_bug)

    monitor = BugMonitorTask("key", "root")
    artifact_dir = tmp_path / "artifact_dir"
    monitor.create_tasks(artifact_dir)
    monitor_artifact = artifact_dir / f"monitor-{bug_data['id']}-1.json"

    with monitor_artifact.open() as f:
        assert json.load(f) == bug_data


def test_monitor_create_tasks_taskcluster(mocker, tmp_path, bug_data):
    """Test task creation in simulated TC environment"""
    bug_response = {"bugs": [bug_data]}
    mocker.patch("bugsy.Bugsy.request", return_value=bug_response)
    mocker.patch("bugmon.BugMonitor.is_supported", return_value=False)
    mocker.patch("bugmon_tc.monitor.monitor.in_taskcluster", return_value=True)

    cached_bug = EnhancedBug(None, **bug_data)
    mocker.patch("bugmon.bug.EnhancedBug.cache_bug", return_value=cached_bug)

    monitor = BugMonitorTask("key", "root")

    mocked_create_task = mocker.patch("bugmon_tc.common.queue.createTask")
    monitor.create_tasks(tmp_path)
    assert mocked_create_task.call_count == 2
