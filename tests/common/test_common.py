# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest
import requests
from requests import RequestException
from taskcluster import TaskclusterRestFailure

from bugmon_tc import common
from bugmon_tc.common import (
    get_url,
    BugmonTaskError,
    fetch_artifact,
    fetch_json_artifact,
    get_bugzilla_auth,
    get_pernosco_auth,
    fetch_trace_artifact,
)


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


def test_get_url_success(mocker):
    """Test that get_url succeeds"""
    # Mock the requests.get method to return a successful response
    mock_response = Mock(status_code=200, raise_for_status=Mock())
    mocker.patch.object(requests, "get", return_value=mock_response)
    result = get_url("http://example.com")
    assert result is not None


def test_get_url_request_exception(mocker):
    """Test that get_url raises a BugmonTaskError on exception"""
    mocker.patch.object(requests, "get", side_effect=RequestException("Request failed"))
    with pytest.raises(BugmonTaskError) as exc_info:
        get_url("http://example.com")

    assert isinstance(exc_info.value.__cause__, RequestException)
    assert str(exc_info.value) == "Request failed"


def test_fetch_artifact(mocker):
    """Simple test of fetch_artifact"""
    mock_response = Mock()
    mock_response.iter_content.return_value = b"artifact content"

    mocker.patch("bugmon_tc.common.queue.session.get", return_value=mock_response)
    response = fetch_artifact("12345", Path("path/to/artifact"))
    assert response == mock_response


def test_fetch_artifact_exception_condition(mocker):
    """Test that failed requests raise"""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = TaskclusterRestFailure(
        "HTTP 404 Not Found", None, 500
    )

    mocker.patch("bugmon_tc.common.queue.session.get", return_value=mock_response)

    with pytest.raises(BugmonTaskError, match="HTTP 404 Not Found"):
        fetch_artifact("12345", Path("path/to/artifact"))
    mock_response.raise_for_status.assert_called_once_with()


def test_fetch_json_artifact(mocker):
    """Simple test of fetch_json_artifact"""
    task_id = "12345"
    json_data = {id: task_id}
    mock_fetch_artifact = mocker.patch("bugmon_tc.common.fetch_artifact")
    mock_fetch_artifact.return_value.json.return_value = json_data

    artifact_path = "path/to/artifact"
    result = fetch_json_artifact(task_id, Path(artifact_path))

    mock_fetch_artifact.assert_called_once_with(task_id, Path(artifact_path))
    mock_fetch_artifact.return_value.json.assert_called_once_with()
    assert result == json_data


def test_fetch_trace_artifact_in_taskcluster(mocker):
    mock_response = Mock()
    mocker.patch("bugmon_tc.common.in_taskcluster", return_value=True)
    mocker.patch("bugmon_tc.common.fetch_artifact", return_value=mock_response)
    mock_queue = mocker.patch("bugmon_tc.common.queue")

    # Mock dependencies to simulate a task with dependencies
    mock_task = Mock()
    mock_task.get.return_value = MagicMock()
    mock_queue.task.return_value = mock_task

    mock_iter_content = Mock(side_effect=[[b"chunk1", b"chunk2"]])
    mock_response.iter_content = mock_iter_content

    # Mock the open method to simulate opening a TemporaryFile
    mocker.patch("builtins.open", mocker.mock_open())

    # Mock the tarfile.open method to simulate extracting the archive
    mock_tarfile = mocker.patch("tarfile.open", autospec=True)

    with fetch_trace_artifact(Path("/fake/path")) as tempdir:
        assert os.path.exists(tempdir)
        assert mock_tarfile.called
        assert mock_iter_content.called


def test_fetch_trace_artifact_local(mocker):
    """Test that when not in taskcluster, the function should use the local file"""
    mocker.patch("bugmon_tc.common.in_taskcluster", return_value=False)
    mocker.patch("builtins.open", mocker.mock_open())
    artifact_path = Path("/path/to/artifact")
    with patch("tarfile.open", autospec=True) as mock_tarfile_open:
        # Call the function that uses tarfile.open
        with fetch_trace_artifact(artifact_path) as tempdir:
            assert os.path.exists(tempdir)

        # Assert that tarfile.open was called with the correct arguments
        mock_tarfile_open.assert_called_once_with(artifact_path, mode="r:gz")


def test_get_bugzilla_auth(monkeypatch):
    """Returns bugzilla key and url when env variable is present"""
    monkeypatch.setenv("BZ_API_KEY", "your_bugzilla_api_key")
    monkeypatch.setenv("BZ_API_ROOT", "https://bugzilla.mozilla.org/rest")

    result = get_bugzilla_auth()

    assert result == {
        "KEY": "your_bugzilla_api_key",
        "URL": "https://bugzilla.mozilla.org/rest",
    }


def test_get_bugzilla_auth_missing_key(monkeypatch):
    """Raises exception when bugzilla env variables are missing"""
    monkeypatch.delenv("BZ_API_KEY", raising=False)
    monkeypatch.setenv("BZ_API_ROOT", "https://bugzilla.mozilla.org/rest")

    msg = "Cannot find Bugzilla credentials in env"
    with pytest.raises(BugmonTaskError, match=msg):
        get_bugzilla_auth()


def test_get_pernosco_auth(monkeypatch):
    """Returns pernosco credentials when env variables are set"""
    monkeypatch.setenv("PERNOSCO_USER", "your_pernosco_user")
    monkeypatch.setenv("PERNOSCO_GROUP", "your_pernosco_group")
    monkeypatch.setenv("PERNOSCO_USER_SECRET_KEY", "your_pernosco_secret_key")

    result = get_pernosco_auth()

    assert result == {
        "PERNOSCO_USER": "your_pernosco_user",
        "PERNOSCO_GROUP": "your_pernosco_group",
        "PERNOSCO_USER_SECRET_KEY": "your_pernosco_secret_key",
    }


def test_get_pernosco_auth_missing_key(monkeypatch):
    """Raises exception when pernosco env variables are missing"""
    monkeypatch.delenv("PERNOSCO_USER", raising=False)
    monkeypatch.setenv("PERNOSCO_GROUP", "your_pernosco_group")
    monkeypatch.setenv("PERNOSCO_USER_SECRET_KEY", "your_pernosco_secret_key")

    msg = "Cannot find Pernosco credentials in env"
    with pytest.raises(BugmonTaskError, match=msg):
        get_pernosco_auth()
