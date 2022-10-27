# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os
import pathlib
import tarfile
import tempfile
from contextlib import contextmanager
from urllib.parse import urlparse

import requests
from requests import RequestException
from taskcluster.helper import TaskclusterConfig

LOG = logging.getLogger(__name__)

# Shared taskcluster configuration
taskcluster = TaskclusterConfig(os.environ["TASKCLUSTER_ROOT_URL"])
queue = taskcluster.get_service("queue")


class BugmonTaskError(Exception):
    """Error handler for bugmon tasks"""


def in_taskcluster():
    """Helper function for determining if we're running in taskcluster"""
    return "TASK_ID" in os.environ and "TASKCLUSTER_ROOT_URL" in os.environ


def get_url(url: str):
    """Retrieve URL contents

    :param url: The URL to retrieve
    """
    try:
        data = requests.get(url, stream=True)
        data.raise_for_status()
    except RequestException as e:
        raise BugmonTaskError(e) from None

    return data


@contextmanager
def download_url(url):
    """Download a URL to a temporary file and return the handle

    :param url: The URL to download
    """
    parsed = urlparse(url)
    ext = pathlib.PurePosixPath(parsed.path).suffix

    resp = get_url(url)
    with tempfile.TemporaryFile(suffix=ext) as temp:
        for chunk in resp.iter_content(chunk_size=128 * 1024):
            temp.write(chunk)

        temp.seek(0)
        yield temp


def fetch_artifact(task_id, artifact_path):
    """Get artifact url

    :param task_id: Task id
    :param artifact_path: Path to the artifact
    """
    LOG.info(f"Fetching artifact: {task_id} {artifact_path}")
    return queue.getLatestArtifact(task_id, artifact_path)


@contextmanager
def fetch_trace_artifact(artifact_path):
    """Retrieve an rr trace artifact

    :param artifact_path: Path to the trace artifact
    """
    with tempfile.TemporaryDirectory() as tempdir:
        if in_taskcluster():
            # Trace artifacts are only used by the report, so they are linked to the
            # processor task
            task = queue.task(os.getenv("TASK_ID"))
            dependencies = task.get("dependencies")
            artifact_info = fetch_artifact(dependencies[-1], artifact_path)
            # All artifacts are returned as JSON.  If the artifact itself is not JSON,
            # it will include a URL to the direct resource.
            with download_url(artifact_info["url"]) as artifact:
                archive = tarfile.open(fileobj=artifact)
                archive.extractall(tempdir.name)
        else:
            with open(artifact_path, "r") as file:
                archive = tarfile.open(file.name)
                archive.extractall(tempdir)

        yield pathlib.Path(tempdir)


def get_bugzilla_auth():
    """Extract Bugzilla API keys from env"""
    try:
        return {
            "KEY": os.environ["BZ_API_KEY"],
            "URL": os.environ["BZ_API_ROOT"],
        }
    except KeyError as e:
        raise BugmonTaskError("Cannot find Bugzilla credentials in env") from e


def get_pernosco_auth():
    """Extract Bugzilla API keys from env"""
    try:
        return {
            "PERNOSCO_USER": os.environ["PERNOSCO_USER"],
            "PERNOSCO_GROUP": os.environ["PERNOSCO_GROUP"],
            "PERNOSCO_USER_SECRET_KEY": os.environ["PERNOSCO_USER_SECRET_KEY"],
        }
    except KeyError as e:
        raise BugmonTaskError("Cannot find Pernosco credentials in env") from e
