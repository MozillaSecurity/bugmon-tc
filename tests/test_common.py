# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from bugmon_tc import common


@pytest.mark.parametrize("is_enabled", [True, False])
def test_monitor_in_taskcluster(monkeypatch, is_enabled):
    """Test that in_taskcluster matches env state"""
    if is_enabled:
        monkeypatch.setenv("TASK_ID", "1")
        monkeypatch.setenv("TASKCLUSTER_ROOT_URL", "1")
    else:
        # Ensure neither env variable is set
        monkeypatch.delenv("TASK_ID", False)
        monkeypatch.delenv("TASKCLUSTER_ROOT_URL", False)

    assert common.in_taskcluster() is is_enabled
