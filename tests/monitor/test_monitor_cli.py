# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
from pathlib import Path
from bugmon_tc.monitor.cli import parse_args, main


def test_parse_args():
    """Test that args are parsed as expected"""
    args = parse_args(["--force-confirm", "output_path"])

    assert args.force_confirm is True
    assert args.output == Path("output_path")


def test_main(mocker, tmp_path):
    """Test that BugMonitorTask is called with the expected arguments"""
    mocker.patch("bugmon_tc.monitor.cli.get_bugzilla_auth").return_value = {
        "KEY": "key",
        "URL": "url",
    }
    mock_bug_monitor_task = mocker.patch(
        "bugmon_tc.monitor.cli.BugMonitorTask", autospec=True
    )

    main(["--force-confirm", str(tmp_path)])

    mock_bug_monitor_task.assert_called_once_with("key", "url", force_confirm=True)
    mock_bug_monitor_task.return_value.create_tasks.assert_called_once_with(tmp_path)
