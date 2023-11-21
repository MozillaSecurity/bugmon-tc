# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import os
from pathlib import Path

import pytest

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.process.cli import process_bug, parse_args


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
def test_process_bug(mocker, tmp_path, bug_data, with_trace):
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
    assert dest.read_text() == '{\n  "bug_number": 123456,\n  "diff": {}\n}'

    if with_trace:
        assert trace_dest.exists() is True


def test_process_bug_raises_no_trace(mocker, tmp_path, bug_data):
    """Test that process raises when no trace_path is discovered"""
    mocker.patch("bugmon_tc.process.cli.BugMonitor.process", return_value=None)
    dest = tmp_path / "results.json"
    trace_dest = tmp_path / "trace.tar.gz"
    with pytest.raises(BugmonTaskError) as e_info:
        process_bug(bug_data, dest, trace_dest=trace_dest)

    assert str(e_info.value) == "Unable to identify a pernosco trace!"
