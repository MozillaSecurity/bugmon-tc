# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
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
    mock_response = mocker.Mock(status_code=200, raise_for_status=mocker.Mock())
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
    mock_response = mocker.Mock()
    mock_response.iter_content.return_value = b"artifact content"

    mocker.patch("bugmon_tc.common.queue.session.get", return_value=mock_response)
    response = fetch_artifact("12345", "path/to/artifact")
    assert response == mock_response


def test_fetch_artifact_exception_condition(mocker):
    """Test that failed requests raise"""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.side_effect = TaskclusterRestFailure(
        "HTTP 404 Not Found", None, 500
    )

    mocker.patch("bugmon_tc.common.queue.session.get", return_value=mock_response)

    with pytest.raises(BugmonTaskError, match="HTTP 404 Not Found"):
        fetch_artifact("12345", "path/to/artifact")
    mock_response.raise_for_status.assert_called_once_with()


def test_fetch_json_artifact(mocker):
    """Simple test of fetch_json_artifact"""
    task_id = "12345"
    json_data = {id: task_id}
    mock_fetch_artifact = mocker.patch("bugmon_tc.common.fetch_artifact")
    mock_fetch_artifact.return_value.json.return_value = json_data

    artifact_path = "path/to/artifact"
    result = fetch_json_artifact(task_id, artifact_path)

    mock_fetch_artifact.assert_called_once_with(task_id, artifact_path)
    mock_fetch_artifact.return_value.json.assert_called_once_with()
    assert result == json_data


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
