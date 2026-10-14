# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import json
import os
from pathlib import Path

import pytest

from bugmon import BugMonitor
from bugmon_tc.common import BugmonTaskError
from bugmon_tc.process.cli import process_bug, parse_args, main


@pytest.fixture(autouse=True)
def pernosco(mocker, monkeypatch):
    creds = {
        "PERNOSCO_USER": "user",
        "PERNOSCO_GROUP": "group",
        "PERNOSCO_USER_SECRET_KEY": "key",
    }
    for key, value in creds.items():
        monkeypatch.setenv(key, value)
    mocker.patch("bugmon_tc.process.cli.is_pernosco_available", return_value=True)
    submit = mocker.patch("bugmon_tc.process.cli.submit_pernosco")
    return submit, creds


@pytest.fixture
def mock_args():
    return {
        "monitor_artifact": "monitor_artifact.json",
        "processor_artifact": "processor_artifact.json",
        "trace_artifact": "trace_artifact.tar.gz",
        "force_confirm": True,
    }


@pytest.fixture
def mock_task_data():
    return {"bug_id": 123, "status": "NEW"}  # Adjust this to match your actual data


def test_parse_args_basic(caplog):
    """Test arg parsing with minimal arguments"""
    args = parse_args(["path/to/monitor_artifact", "path/to/processor_artifact"])
    assert isinstance(args, argparse.Namespace)
    assert args.monitor_artifact == Path("path/to/monitor_artifact")
    assert args.processor_artifact == Path("path/to/processor_artifact")
    assert args.trace_artifact is None
    assert not args.force_confirm
    assert caplog.text == ""


def test_parse_args_with_trace_artifact(caplog):
    """Test arg parsing with a trace artifact path"""
    args = parse_args(
        [
            "path/to/monitor_artifact",
            "path/to/processor_artifact",
            "--trace-artifact",
            "path/to/trace_artifact",
        ]
    )
    assert args.trace_artifact == Path("path/to/trace_artifact")
    assert caplog.text == ""


def test_parse_args_with_existing_paths_warning(caplog, mocker):
    """Test arg parsing using paths that exist"""
    # Mock Path.exists to simulate existing paths
    mocker.patch.object(Path, "exists", return_value=True)
    parse_args(
        [
            "path/to/monitor_artifact",
            "path/to/processor_artifact",
            "--trace-artifact",
            "path/to/trace_artifact",
        ]
    )
    assert "Path" in caplog.text
    assert "exists! Contents will be overwritten!" in caplog.text


def test_parse_args_force_confirm_from_env_var(caplog, mocker):
    """Test arg parsing of force_confirm using the env variable"""
    # Mock os.environ.get to simulate the presence of FORCE_CONFIRM environment variable
    mocker.patch.object(os.environ, "get", return_value="1")

    # Call the parse_args function
    args = parse_args(
        [
            "path/to/monitor_artifact",
            "path/to/processor_artifact",
        ]
    )
    assert args.force_confirm


def test_parse_args_force_confirm_from_cmd_line(caplog, mocker):
    """Test arg parsing of force_confirm using the command line option"""
    # Mock os.environ.get to simulate the absence of FORCE_CONFIRM environment variable
    mocker.patch.object(os.environ, "get", return_value=None)

    args = parse_args(
        [
            "path/to/monitor_artifact",
            "path/to/processor_artifact",
            "--force-confirm",
        ]
    )
    assert args.force_confirm


@pytest.mark.parametrize("with_trace", [True, False])
def test_process_bug(mocker, tmp_path, bug_data, with_trace, pernosco):
    """Test bug processing"""
    mocker.patch("bugmon_tc.process.cli.BugMonitor.process", return_value=None)
    dest = tmp_path / "results.json"

    trace_dest = None
    if with_trace:
        trace_dest = tmp_path / "trace.tar.gz"
        raw_trace = tmp_path / "latest-trace"
        raw_trace.mkdir()
        mocker.patch("bugmon_tc.process.cli.get_pernosco_trace", return_value=raw_trace)

    process_bug(bug_data, dest, trace_dest=trace_dest)

    assert dest.exists() is True
    assert json.loads(dest.read_text()) == {
        "bug_number": 123456,
        "diff": {},
        "trace_available": with_trace,
    }

    submit, creds = pernosco
    if with_trace:
        assert trace_dest.exists() is True
        submit.assert_called_once_with(raw_trace, 123456, creds)
    else:
        submit.assert_not_called()


def test_process_bug_submits_trace_when_closed(mocker, tmp_path, bug_data, pernosco):
    """A requested recording must be submitted even if fix verification closes the bug."""
    dest = tmp_path / "results.json"
    trace_dest = tmp_path / "trace.tar.gz"

    def mock_process(self, force_confirm=False):
        self._close_bug = True  # pylint: disable=protected-access

    mocker.patch.object(BugMonitor, "process", mock_process)
    raw_trace = tmp_path / "latest-trace"
    raw_trace.mkdir()
    mocker.patch("bugmon_tc.process.cli.get_pernosco_trace", return_value=raw_trace)

    process_bug(bug_data, dest, trace_dest=trace_dest)

    assert dest.exists()
    assert trace_dest.exists()
    assert json.loads(dest.read_text())["trace_available"] is True
    submit, creds = pernosco
    submit.assert_called_once_with(raw_trace, 123456, creds)


def test_process_bug_raises_no_trace(mocker, tmp_path, bug_data):
    """Test that process raises when no trace_path is discovered"""
    mocker.patch("bugmon_tc.process.cli.BugMonitor.process", return_value=None)
    dest = tmp_path / "results.json"
    trace_dest = tmp_path / "trace.tar.gz"
    with pytest.raises(BugmonTaskError) as e_info:
        process_bug(bug_data, dest, trace_dest=trace_dest)

    assert str(e_info.value) == "Unable to identify a pernosco trace!"


def test_main_in_taskcluster(mocker, tmp_path):
    """Test that process_bug is called with the correct args when in taskcluster"""
    mocker.patch("bugmon_tc.process.cli.in_taskcluster", return_value=True)
    mocker.patch(
        "bugmon_tc.process.cli.queue.task", return_value={"taskGroupId": "123"}
    )
    mock_task_data = {"bug_id": 123, "status": "NEW"}
    mocker.patch(
        "bugmon_tc.process.cli.fetch_json_artifact", return_value=mock_task_data
    )
    mock_process_bug = mocker.patch("bugmon_tc.process.cli.process_bug")

    main(["monitor_artifact.json", "processor_artifact.json"])

    mock_process_bug.assert_called_once_with(
        mock_task_data,
        Path("processor_artifact.json"),
        force_confirm=False,
        trace_dest=None,
    )


def test_main_local(mocker, tmp_path):
    """Test that process_bug is called with the correct args when run locally"""
    mocker.patch("bugmon_tc.process.cli.in_taskcluster", return_value=False)
    mock_task_data = {"bug_id": 123, "status": "NEW"}
    monitor_artifact_path = tmp_path / "monitor.json"
    monitor_artifact_path.write_text(json.dumps({"bug_id": 123, "status": "NEW"}))
    processor_artifact_path = tmp_path / "processor.json"
    mock_process_bug = mocker.patch("bugmon_tc.process.cli.process_bug")

    main([str(monitor_artifact_path), str(processor_artifact_path)])

    mock_process_bug.assert_called_once_with(
        mock_task_data,
        processor_artifact_path,
        force_confirm=False,
        trace_dest=None,
    )


def test_recording_does_not_inherit_pernosco_credentials(
    mocker, tmp_path, bug_data, pernosco
):
    def process(self, force_confirm=False):
        assert all(key not in os.environ for key in pernosco[1])

    mocker.patch.object(BugMonitor, "process", process)
    raw_trace = tmp_path / "latest-trace"
    raw_trace.mkdir()
    mocker.patch("bugmon_tc.process.cli.get_pernosco_trace", return_value=raw_trace)
    process_bug(bug_data, tmp_path / "result.json", tmp_path / "trace.tar.gz")
    pernosco[0].assert_called_once_with(raw_trace, 123456, pernosco[1])


@pytest.mark.parametrize("available", [True, False])
def test_submission_failure_does_not_write_result(
    mocker, tmp_path, bug_data, pernosco, available
):
    mocker.patch.object(BugMonitor, "process")
    trace = tmp_path / "trace"
    trace.mkdir()
    mocker.patch("bugmon_tc.process.cli.get_pernosco_trace", return_value=trace)
    mocker.patch("bugmon_tc.process.cli.is_pernosco_available", return_value=available)
    pernosco[0].side_effect = BugmonTaskError("Upload failed")
    dest = tmp_path / "result.json"
    with pytest.raises(BugmonTaskError):
        process_bug(bug_data, dest, tmp_path / "trace.tar.gz")
    assert not dest.exists()
    assert (tmp_path / "trace.tar.gz").exists()
    if not available:
        pernosco[0].assert_not_called()
