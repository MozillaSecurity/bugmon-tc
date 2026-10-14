# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
from argparse import Namespace
from pathlib import Path

import pytest

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.report.cli import update_bug, parse_args, main


@pytest.fixture
def mock_args(tmp_path):
    processor_artifact_path = tmp_path / "processor_artifact.json"
    return Namespace(
        processor_artifact=processor_artifact_path,
        bug_number=123456,
    )


@pytest.fixture
def mock_bz_creds():
    return {"KEY": "fake_key", "URL": "fake_url"}


@pytest.fixture
def mock_task_data(bug_data_processed):
    return {**bug_data_processed, "trace_available": True}


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


def test_parse_args(tmp_path):
    processor_artifact = tmp_path / "processor.json"
    processor_artifact.touch()
    assert (
        parse_args([str(processor_artifact)]).processor_artifact == processor_artifact
    )


def test_parse_args_missing_file(tmp_path):
    with pytest.raises(SystemExit):
        parse_args([str(tmp_path / "missing.json")])


def test_parse_args_bug_number_from_env(tmp_path, monkeypatch):
    """The BUG_NUMBER env variable is used as the --bug-number default"""
    processor_artifact_path = tmp_path / "processor_artifact.json"
    processor_artifact_path.touch()
    monkeypatch.setenv("BUG_NUMBER", "654321")

    result = parse_args([str(processor_artifact_path)])

    assert result.bug_number == 654321


def test_parse_args_rejects_invalid_env_bug_number(tmp_path, monkeypatch):
    """A non-numeric BUG_NUMBER env variable raises a parser error"""
    processor_artifact_path = tmp_path / "processor_artifact.json"
    processor_artifact_path.touch()
    monkeypatch.setenv("BUG_NUMBER", "123/../user")

    with pytest.raises(SystemExit):
        parse_args([str(processor_artifact_path)])


def test_main_in_taskcluster(
    mocker,
    tmp_path,
    mock_args,
    mock_bz_creds,
    mock_task_data,
):
    """Test that update_bug are called with the correct args when in taskcluster"""
    mocker.patch("bugmon_tc.report.cli.parse_args", return_value=mock_args)
    mocker.patch("bugmon_tc.report.cli.get_bugzilla_auth", return_value=mock_bz_creds)
    mocker.patch("bugmon_tc.report.cli.in_taskcluster", return_value=True)
    mocker.patch("bugmon_tc.report.cli.queue.task", return_value={"dependencies": [""]})
    mocker.patch("os.getenv", return_value="")
    mocker.patch(
        "bugmon_tc.report.cli.fetch_json_artifact", return_value=mock_task_data
    )
    mock_update_bug = mocker.patch("bugmon_tc.report.cli.update_bug")

    main(mock_args)

    mock_update_bug.assert_called_once_with(mock_task_data, mock_bz_creds)


def test_main_local(mocker, tmp_path, mock_args, mock_bz_creds, mock_task_data):
    """Test that update_bug are called with the correct args when run locally"""
    mocker.patch("bugmon_tc.report.cli.parse_args", return_value=mock_args)
    mocker.patch("bugmon_tc.report.cli.get_bugzilla_auth", return_value=mock_bz_creds)
    mocker.patch("bugmon_tc.report.cli.in_taskcluster", return_value=False)
    mock_update_bug = mocker.patch("bugmon_tc.report.cli.update_bug")
    mocker.patch.object(Path, "read_text", return_value=json.dumps(mock_task_data))
    main(mock_args)

    mock_update_bug.assert_called_once_with(mock_task_data, mock_bz_creds)


def test_main_rejects_mismatched_artifact(mocker, tmp_path):
    """The reporter refuses to update a bug other than the expected one"""
    bug_data = {
        "bug_number": 999999,
        "diff": {"whiteboard": "[bugmon:confirmed]"},
        "trace_available": False,
    }
    processor_artifact = tmp_path / "processor.json"
    processor_artifact.write_text(json.dumps(bug_data))

    args = Namespace(
        processor_artifact=processor_artifact,
        bug_number=123456,
    )
    mocker.patch("bugmon_tc.report.cli.parse_args", return_value=args)
    mocker.patch("bugmon_tc.report.cli.in_taskcluster", return_value=False)
    mock_update_bug = mocker.patch("bugmon_tc.report.cli.update_bug")

    with pytest.raises(BugmonTaskError, match="Bug number mismatch"):
        main(args)

    mock_update_bug.assert_not_called()
