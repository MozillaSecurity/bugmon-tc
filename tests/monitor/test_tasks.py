# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
from datetime import datetime, timedelta

import pytest
from pathlib import Path

from bugmon import EnhancedBug
from freezegun import freeze_time
from taskcluster import stringDate, fromNow

from bugmon_tc.monitor.tasks import ProcessorTask, ReporterTask, MAX_RUNTIME

PARENT_ID = "UkGN9k6QSNi0-s62I5vvdg"
MONITOR_ARTIFACT_PATH = Path("path/to/monitor_artifact")
PROCESSOR_ARTIFACT_PATH = Path("path/to/processor_artifact")
TRACE_ARTIFACT_PATH = Path("path/to/trace_artifact")


def test_processor_task_init(bug_data):
    """Simple test of initializing a ProcessorTask"""
    bug = EnhancedBug(None, **bug_data)
    processor_task = ProcessorTask(PARENT_ID, bug, MONITOR_ARTIFACT_PATH)

    assert processor_task.id is not None
    assert processor_task.parent_id == PARENT_ID
    assert processor_task.monitor_path == MONITOR_ARTIFACT_PATH
    assert processor_task.dest == Path(f"processor-result-{bug.id}-{PARENT_ID}.json")
    assert processor_task.trace_dest is None  # By default, use_pernosco is False
    assert processor_task.force_confirm is False  # By default, force_confirm is False


def test_processor_task_init_with_options(bug_data):
    """Test initializing a ProcessorTask with optional options"""
    bug = EnhancedBug(None, **bug_data)
    processor_task = ProcessorTask(
        PARENT_ID,
        bug,
        MONITOR_ARTIFACT_PATH,
        use_pernosco=True,
        force_confirm=True,
    )

    # Assertions
    assert processor_task.id is not None
    assert processor_task.parent_id == PARENT_ID
    assert processor_task.monitor_path == MONITOR_ARTIFACT_PATH
    assert processor_task.dest == Path(f"processor-result-{bug.id}-{PARENT_ID}.json")
    assert processor_task.trace_dest == Path(
        f"processor-rr-trace-{bug.id}-{PARENT_ID}.tar.gz"
    )
    assert processor_task.force_confirm is True


def test_processor_task_capabilities_linux(bug_data, mocker):
    """Test that a ProcessorTask for a Linux bug returns the expected capabilities"""
    bug_data["op_sys"] = "Linux"
    mocker.patch("bugmon.bug.platform.system", return_value="Linux")
    bug = EnhancedBug(None, **bug_data)

    task = ProcessorTask(PARENT_ID, bug, Path("/path/to/artifact"))
    assert task.capabilities == {
        "devices": {"hostSharedMemory": True, "loopbackAudio": True},
        "disableSeccomp": True,
        "privileged": True,
    }


def test_processor_task_capabilities_windows(bug_data, mocker):
    """Test that a ProcessorTask for a Windows bug returns the expected capabilities"""
    bug_data["op_sys"] = "Windows"
    mocker.patch("bugmon.bug.platform.system", return_value="Windows")
    bug = EnhancedBug(None, **bug_data)

    task = ProcessorTask(PARENT_ID, bug, Path("/path/to/artifact"))
    assert task.capabilities == {}


def test_processor_task_env(bug_data):
    """Test that a ProcessorTask with no extra args contains the minimal env variables"""
    bug = EnhancedBug(None, **bug_data)
    processor = ProcessorTask(PARENT_ID, bug, MONITOR_ARTIFACT_PATH)
    assert processor.env == {
        "BUG_ACTION": "process",
        "MONITOR_ARTIFACT": str(MONITOR_ARTIFACT_PATH),
        "PROCESSOR_ARTIFACT": str(processor.dest),
    }


def test_processor_task_env_windows(bug_data, mocker):
    """Test that a ProcessorTask for a windows bug includes the necessary env variables"""
    bug_data["op_sys"] = "Windows"
    mocker.patch("bugmon.bug.platform.system", return_value="Windows")
    bug = EnhancedBug(None, **bug_data)
    processor = ProcessorTask(PARENT_ID, bug, MONITOR_ARTIFACT_PATH)
    assert processor.env == {
        "BUG_ACTION": "process",
        "MONITOR_ARTIFACT": str(MONITOR_ARTIFACT_PATH),
        "MSYSTEM": "MINGW64",
        "PROCESSOR_ARTIFACT": str(processor.dest),
    }


def test_processor_task_env_extra_args(bug_data):
    """Test that a ProcessorTask with extra args contains the expected env variables"""
    bug = EnhancedBug(None, **bug_data)
    processor = ProcessorTask(
        "PARENT_ID",
        bug,
        MONITOR_ARTIFACT_PATH,
        use_pernosco=True,
        force_confirm=True,
    )
    assert processor.env == {
        "BUG_ACTION": "process",
        "FORCE_CONFIRM": "1",
        "MONITOR_ARTIFACT": str(MONITOR_ARTIFACT_PATH),
        "PROCESSOR_ARTIFACT": str(processor.dest),
        "TRACE_ARTIFACT": str(processor.trace_dest),
    }


def test_processor_task_scopes_linux(bug_data, mocker):
    """Test that a ProcessorTask for a Linux bug returns the expected scopes"""
    bug_data["op_sys"] = "Linux"
    mocker.patch("bugmon.bug.platform.system", return_value="Linux")

    bug = EnhancedBug(None, **bug_data)
    task = ProcessorTask("PARENT_ID", bug, MONITOR_ARTIFACT_PATH)

    assert task.scopes == [
        f"queue:get-artifact:project/fuzzing/bugmon/{MONITOR_ARTIFACT_PATH}",
        "queue:scheduler-id:-",
        "docker-worker:capability:device:hostSharedMemory",
        "docker-worker:capability:device:loopbackAudio",
        "docker-worker:capability:disableSeccomp",
        "docker-worker:capability:privileged",
    ]


def test_processor_task_scopes_windows(bug_data, mocker):
    """Test that a ProcessorTask for a Windows bug returns the expected scopes"""
    bug_data["op_sys"] = "Windows"
    mocker.patch("bugmon.bug.platform.system", return_value="Windows")

    bug = EnhancedBug(None, **bug_data)
    task = ProcessorTask("PARENT_ID", bug, MONITOR_ARTIFACT_PATH)

    assert task.scopes == [
        f"queue:get-artifact:project/fuzzing/bugmon/{MONITOR_ARTIFACT_PATH}",
        "queue:scheduler-id:-",
    ]


@freeze_time("2023-01-01")
def test_processor_task_task_definition_linux(bug_data, mocker):
    """Test that a ProcessorTask's task definition matches the expected format for Linux bugs"""
    bug_data["op_sys"] = "Linux"
    mocker.patch("bugmon.bug.platform.system", return_value="Linux")

    created = datetime(2023, 1, 1)

    bug = EnhancedBug(None, **bug_data)
    processor = ProcessorTask(PARENT_ID, bug, MONITOR_ARTIFACT_PATH)

    assert processor.task["taskGroupId"] == PARENT_ID
    assert processor.task["dependencies"] == [PARENT_ID]
    assert processor.task["created"] == stringDate(created)
    assert processor.task["deadline"] == stringDate(
        created + timedelta(seconds=MAX_RUNTIME)
    )
    assert processor.task["expires"] == stringDate(fromNow("1 week", created))
    assert (
        processor.task["metadata"]["name"] == f"{type(processor).__name__} ({bug.id})"
    )
    assert processor.task["payload"]["capabilities"] == processor.capabilities
    assert processor.task["payload"]["env"] == processor.env
    assert processor.task["payload"]["maxRunTime"] == MAX_RUNTIME
    assert processor.task["workerType"] == processor.worker_type
    assert processor.task["scopes"] == processor.scopes

    assert "command" not in processor.task["payload"]


def test_processor_task_task_definition_windows(bug_data, mocker):
    """Test that a ProcessorTask's task definition matches the expected format for Windows bugs"""
    bug_data["op_sys"] = "Windows"
    mocker.patch("bugmon.bug.platform.system", return_value="Windows")
    bug = EnhancedBug(None, **bug_data)
    processor = ProcessorTask(PARENT_ID, bug, MONITOR_ARTIFACT_PATH)

    assert processor.task["payload"]["command"] == [
        "set HOME=%CD%",
        "set ARTIFACTS=%CD%",
        "set PATH="
        + ";".join(
            [
                r"%CD%\msys64\opt\python",
                r"%CD%\msys64\opt\python\Scripts",
                r"%CD%\msys64\MINGW64\bin",
                r"%CD%\msys64\usr\bin",
                "%PATH%",
            ]
        ),
        "launch.sh",
    ]
    assert processor.task["payload"]["onExitStatus"]["retry"] == [0x40010004]
    assert processor.task["payload"]["artifacts"] == [
        {
            "name": "project/fuzzing/bugmon",
            "path": "/bugmon-artifacts/",
            "type": "directory",
        }
    ]


@pytest.mark.parametrize(
    "opts",
    [
        {"platform": "Linux", "pernosco": False, "type": "bugmon-processor"},
        {"platform": "Linux", "pernosco": True, "type": "bugmon-pernosco"},
        {"platform": "Windows", "pernosco": False, "type": "bugmon-processor-windows"},
    ],
)
def test_processor_task_worker_type_windows(bug_data, mocker, opts):
    """Test that a ProcessorTask for a Linux bug returns the expected worker type"""
    mocker.patch("bugmon.bug.platform.system", return_value=opts["platform"])
    bug_data["op_sys"] = opts["platform"]
    bug = EnhancedBug(None, **bug_data)

    processor = ProcessorTask(
        "PARENT_ID",
        bug,
        MONITOR_ARTIFACT_PATH,
        use_pernosco=opts["pernosco"],
    )

    assert processor.worker_type == opts["type"]


def test_reporter_task_init(bug_data):
    bug = EnhancedBug(None, **bug_data)
    dependency = "BaQj_QARRh-PH0w6anyyxg"

    reporter_task = ReporterTask(
        PARENT_ID,
        bug,
        PROCESSOR_ARTIFACT_PATH,
        dep=dependency,
        trace_path=TRACE_ARTIFACT_PATH,
    )

    assert reporter_task.parent_id == PARENT_ID
    assert reporter_task.bug == bug
    assert reporter_task.process_path == PROCESSOR_ARTIFACT_PATH
    assert reporter_task.dependency == dependency
    assert reporter_task.trace_dest == TRACE_ARTIFACT_PATH


def test_reporter_task_env(bug_data):
    bug = EnhancedBug(None, **bug_data)
    dependency = "BaQj_QARRh-PH0w6anyyxg"

    reporter_task = ReporterTask(
        PARENT_ID,
        bug,
        PROCESSOR_ARTIFACT_PATH,
        dep=dependency,
        trace_path=TRACE_ARTIFACT_PATH,
    )

    assert reporter_task.env == {
        "BUG_ACTION": "report",
        "PROCESSOR_ARTIFACT": str(PROCESSOR_ARTIFACT_PATH),
        "TRACE_ARTIFACT": str(TRACE_ARTIFACT_PATH),
    }


def test_reporter_task_env_without_trace(bug_data):
    bug = EnhancedBug(None, **bug_data)
    dependency = "BaQj_QARRh-PH0w6anyyxg"

    reporter_task = ReporterTask(
        PARENT_ID,
        bug,
        PROCESSOR_ARTIFACT_PATH,
        dep=dependency,
    )

    assert reporter_task.env == {
        "BUG_ACTION": "report",
        "PROCESSOR_ARTIFACT": str(PROCESSOR_ARTIFACT_PATH),
    }


def test_reporter_task_task(bug_data):
    bug = EnhancedBug(None, **bug_data)
    dependency = "BaQj_QARRh-PH0w6anyyxg"
    reporter_task = ReporterTask(
        PARENT_ID, bug, PROCESSOR_ARTIFACT_PATH, dep=dependency
    )

    assert reporter_task.task["dependencies"] == [PARENT_ID, dependency]


def test_reporter_task_scopes(bug_data):
    bug = EnhancedBug(None, **bug_data)
    dependency = "BaQj_QARRh-PH0w6anyyxg"

    reporter_task = ReporterTask(
        PARENT_ID,
        bug,
        PROCESSOR_ARTIFACT_PATH,
        dep=dependency,
        trace_path=TRACE_ARTIFACT_PATH,
    )

    assert reporter_task.scopes == [
        "secrets:get:project/fuzzing/bz-api-key",
        "secrets:get:project/fuzzing/pernosco-user",
        "secrets:get:project/fuzzing/pernosco-group",
        "secrets:get:project/fuzzing/pernosco-secret",
        f"queue:get-artifact:project/fuzzing/bugmon/{PROCESSOR_ARTIFACT_PATH}",
        f"queue:get-artifact:project/fuzzing/bugmon/{TRACE_ARTIFACT_PATH}",
        "queue:scheduler-id:-",
    ]


def test_reporter_task_worker_type(bug_data):
    bug = EnhancedBug(None, **bug_data)
    dependency = "BaQj_QARRh-PH0w6anyyxg"

    reporter_task = ReporterTask(
        PARENT_ID,
        bug,
        PROCESSOR_ARTIFACT_PATH,
        dep=dependency,
        trace_path=TRACE_ARTIFACT_PATH,
    )

    assert reporter_task.worker_type == "bugmon-monitor"
