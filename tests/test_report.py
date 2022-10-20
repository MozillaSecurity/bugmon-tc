# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import os
from operator import itemgetter

import pytest

from bugmon_tc.common import BugmonTaskError
from bugmon_tc.report.cli import update_bug, submit_trace


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

    (trace_dir / "build.json").write_text(json.dumps(build_info))
    branch, rev = itemgetter("branch", "rev")(build_info)

    fetch_artifact_mock = mocker.patch("bugmon_tc.report.cli.fetch_trace_artifact")
    fetch_artifact_mock.return_value.__enter__.return_value = trace_dir

    get_source_mock = mocker.patch("bugmon_tc.report.cli.get_source_url")
    source_url = f"https://hg.mozilla.org/mozilla-central/archive/{rev}.zip"
    get_source_mock.return_value = source_url

    source_dir = tmp_path / "source_dir"
    source_dir.mkdir()
    download_zip_mock = mocker.patch("bugmon_tc.report.cli.download_zip_archive")
    download_zip_mock.return_value.__enter__.return_value = source_dir

    submit_pernosco_mock = mocker.patch("bugmon_tc.report.cli.submit_pernosco")
    pernosco_creds = {
        "PERNOSCO_USER": "user",
        "PERNOSCO_GROUP": "group",
        "PERNOSCO_USER_SECRET_KEY": "key",
    }
    mocker.patch("bugmon_tc.report.cli.is_pernosco_available", return_value=True)
    submit_trace(bug_data_processed, trace_artifact, pernosco_creds)

    assert fetch_artifact_mock.call_args == mocker.call(trace_artifact)
    assert get_source_mock.call_args == mocker.call(branch, rev)
    assert download_zip_mock.call_args == mocker.call(source_url)
    assert submit_pernosco_mock.call_args == mocker.call(
        trace_dir,
        source_dir,
        bug_data_processed["bug_number"],
        {"PATH": os.environ.get("PATH"), **pernosco_creds},
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


def test_submit_trace_missing_build_info(bug_data_processed, mocker, tmp_path):
    """Test that submitting a trace fails when pernosco is not available"""
    mocker.patch("bugmon_tc.report.cli.is_pernosco_available", return_value=True)

    trace_artifact = tmp_path / "trace_artifact.tar.gz"
    trace_dir = tmp_path / "trace_dir"
    trace_dir.mkdir()
    fetch_artifact_mock = mocker.patch("bugmon_tc.report.cli.fetch_trace_artifact")
    fetch_artifact_mock.return_value.__enter__.return_value = trace_dir

    pernosco_creds = {
        "PERNOSCO_USER": "user",
        "PERNOSCO_GROUP": "group",
        "PERNOSCO_USER_SECRET_KEY": "key",
    }

    with pytest.raises(BugmonTaskError) as e_info:
        submit_trace(bug_data_processed, trace_artifact, pernosco_creds)

    assert str(e_info.value) == "Cannot find build.json in trace archive."
