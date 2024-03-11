# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
from argparse import Namespace
from pathlib import Path

import pytest

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.report.cli import update_bug, submit_trace, parse_args, main


@pytest.fixture
def mock_args(tmp_path):
    processor_artifact_path = tmp_path / "processor_artifact.json"
    trace_artifact_path = tmp_path / "trace_artifact.json"
    return Namespace(
        processor_artifact=processor_artifact_path, trace_artifact=trace_artifact_path
    )


@pytest.fixture
def mock_bz_creds():
    return {"KEY": "fake_key", "URL": "fake_url"}


@pytest.fixture
def mock_pernosco_token():
    return {"token": "fake_token"}


@pytest.fixture
def mock_task_data():
    return {"bug_id": 123, "status": "NEW"}


def test_update_bug(bug_data_processed, caplog, mocker):
    """Test bug updates"""
    mock_bugsy = mocker.patch("bugmon_tc.report.cli.Bugsy")
    mock_bugsy.request.return_value = None

    bz_creds = {"KEY": "foo", "URL": "https://bugzilla.mozilla.org/rest"}
    update_bug(bug_data_processed, bz_creds)
    assert (
        caplog.messages[0]
        == 'Committing (123456): {"whiteboard": "[bugmon:bisected,confirmed]"}'
    )


def test_submit_trace(bug_data_processed, build_info, mocker, monkeypatch, tmp_path):
    """Test submitting a pernosco trace"""
    trace_artifact = tmp_path / "trace_artifact.tar.gz"
    trace_dir = tmp_path / "trace_dir"
    trace_dir.mkdir()

    fetch_artifact_mock = mocker.patch("bugmon_tc.report.cli.fetch_trace_artifact")
    fetch_artifact_mock.return_value.__enter__.return_value = trace_dir

    submit_pernosco_mock = mocker.patch("bugmon_tc.report.cli.submit_pernosco")
    pernosco_creds = {
        "PERNOSCO_USER": "user",
        "PERNOSCO_GROUP": "group",
        "PERNOSCO_USER_SECRET_KEY": "key",
    }
    mocker.patch("bugmon_tc.report.cli.is_pernosco_available", return_value=True)
    submit_trace(bug_data_processed, trace_artifact, pernosco_creds)

    assert fetch_artifact_mock.call_args == mocker.call(trace_artifact)
    assert submit_pernosco_mock.call_args == mocker.call(
        trace_dir,
        bug_data_processed["bug_number"],
        pernosco_creds,
    )


def test_submit_trace_without_pernosco(
    bug_data_processed, build_info, mocker, monkeypatch, tmp_path
):
    """Test that submitting a trace fails when pernosco is not available"""
    mocker.patch("bugmon_tc.report.cli.is_pernosco_available", return_value=False)

    trace_artifact = tmp_path / "trace_artifact.tar.gz"
    trace_dir = tmp_path / "trace_dir"
    trace_dir.mkdir()

    pernosco_creds = {
        "PERNOSCO_USER": "user",
        "PERNOSCO_GROUP": "group",
        "PERNOSCO_USER_SECRET_KEY": "key",
    }

    with pytest.raises(BugmonTaskError) as e_info:
        submit_trace(bug_data_processed, trace_artifact, pernosco_creds)

    assert str(e_info.value) == "Cannot find working instance of pernosco-submit!"


def test_parse_args(tmp_path):
    """Simple test of parse args"""
    processor_artifact_path = tmp_path / "processor_artifact.json"
    trace_artifact_path = tmp_path / "trace_artifact.tar.gz"
    processor_artifact_path.touch()
    trace_artifact_path.touch()

    result = parse_args(
        [
            str(processor_artifact_path),
            "--trace-artifact",
            str(trace_artifact_path),
        ]
    )

    assert result.processor_artifact == processor_artifact_path
    assert result.trace_artifact == trace_artifact_path


@pytest.mark.parametrize("skip", ["processor", "trace"])
def test_parse_args_missing_file(tmp_path, skip):
    """Test that parse_args raises when the artifact paths cannot be found"""
    processor_artifact_path = tmp_path / "processor_artifact.json"
    trace_artifact_path = tmp_path / "trace_artifact.tar.gz"
    if skip != "processor":
        processor_artifact_path.touch()
    if skip != "trace":
        trace_artifact_path.touch()

    with pytest.raises(SystemExit) as _:
        parse_args(
            [
                str(processor_artifact_path),
                "--trace-artifact",
                str(trace_artifact_path),
            ]
        )


def test_main_in_taskcluster(
    mocker,
    tmp_path,
    mock_args,
    mock_bz_creds,
    mock_pernosco_token,
    mock_task_data,
):
    """Test that submit_trace and update_bug are called with the correct args when in taskcluster"""
    mocker.patch("bugmon_tc.report.cli.parse_args", return_value=mock_args)
    mocker.patch("bugmon_tc.report.cli.get_bugzilla_auth", return_value=mock_bz_creds)
    mocker.patch("bugmon_tc.report.cli.in_taskcluster", return_value=True)
    mocker.patch("bugmon_tc.report.cli.queue.task", return_value={"dependencies": [""]})
    mocker.patch("os.getenv", return_value="")
    mocker.patch(
        "bugmon_tc.report.cli.fetch_json_artifact", return_value=mock_task_data
    )
    mocker.patch(
        "bugmon_tc.report.cli.get_pernosco_auth", return_value=mock_pernosco_token
    )
    mock_submit_trace = mocker.patch("bugmon_tc.report.cli.submit_trace")
    mock_update_bug = mocker.patch("bugmon_tc.report.cli.update_bug")

    main(mock_args)

    mock_submit_trace.assert_called_once_with(
        mock_task_data,
        mock_args.trace_artifact,
        mock_pernosco_token,
    )
    mock_update_bug.assert_called_once_with(mock_task_data, mock_bz_creds)


def test_main_local(mocker, tmp_path, mock_args, mock_pernosco_token, mock_task_data):
    """Test that submit_trace and update_bug are called with the correct args when run locally"""
    mocker.patch("bugmon_tc.report.cli.parse_args", return_value=mock_args)
    mocker.patch("bugmon_tc.report.cli.get_bugzilla_auth", return_value=mock_bz_creds)
    mocker.patch("bugmon_tc.report.cli.in_taskcluster", return_value=False)
    mocker.patch(
        "bugmon_tc.report.cli.get_pernosco_auth", return_value=mock_pernosco_token
    )
    mock_submit_trace = mocker.patch("bugmon_tc.report.cli.submit_trace")
    mock_update_bug = mocker.patch("bugmon_tc.report.cli.update_bug")
    mocker.patch.object(Path, "read_text", return_value=json.dumps(mock_task_data))
    main(mock_args)

    mock_submit_trace.assert_called_once_with(
        mock_task_data,
        mock_args.trace_artifact,
        mock_pernosco_token,
    )
    mock_update_bug.assert_called_once_with(mock_task_data, mock_bz_creds)
