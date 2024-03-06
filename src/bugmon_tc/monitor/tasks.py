# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import abc

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Dict

from bugmon import EnhancedBug
from taskcluster.utils import fromNow
from taskcluster.utils import slugId
from taskcluster.utils import stringDate

MAX_RUNTIME = 14400


class BaseTask(abc.ABC):
    """Abstract class for defining tasks"""

    def __init__(self, parent_id: str, bug: EnhancedBug) -> None:
        self.id = slugId()
        self.parent_id = parent_id
        self.bug = bug
        self.dependency: Optional[str] = None
        self._task: Optional[Dict[str, Any]] = None

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Task capabilities"""
        return {}

    @property
    @abc.abstractmethod
    def env(self) -> Dict[str, str]:
        """Environment variables for the task"""

    @property
    def task(self) -> Dict[str, Any]:
        """Task definition"""
        if self._task is None:
            dependencies = [self.parent_id]
            if self.dependency is not None:
                dependencies.append(self.dependency)

            now = datetime.utcnow()

            self._task = {
                "taskGroupId": self.parent_id,
                "dependencies": dependencies,
                "created": stringDate(now),
                "deadline": stringDate(now + timedelta(seconds=MAX_RUNTIME)),
                "expires": stringDate(fromNow("1 week", now)),
                "provisionerId": "proj-fuzzing",
                "metadata": {
                    "description": "Bugmon worker",
                    "name": f"{type(self).__name__} ({self.bug.id})",
                    "owner": "jkratzer@mozilla.com",
                    "source": "https://github.com/MozillaSecurity/bugmon",
                },
                "payload": {
                    "artifacts": {
                        "project/fuzzing/bugmon": {
                            "path": "/bugmon-artifacts/",
                            "type": "directory",
                        }
                    },
                    "cache": {},
                    "capabilities": self.capabilities,
                    "env": self.env,
                    "features": {"taskclusterProxy": True},
                    "image": {
                        "type": "indexed-image",
                        "path": "public/bugmon.tar.zst",
                        "namespace": "project.fuzzing.orion.bugmon.master",
                    },
                    "maxRunTime": MAX_RUNTIME,
                },
                "priority": "high",
                "workerType": self.worker_type,
                "retries": 5,
                "routes": ["notify.email.jkratzer@mozilla.com.on-failed"],
                "schedulerId": "-",
                "scopes": self.scopes,
                "tags": {},
            }

        return self._task

    @property
    @abc.abstractmethod
    def scopes(self) -> List[str]:
        """Scopes applied to the task"""

    @property
    @abc.abstractmethod
    def worker_type(self) -> str:
        """The worker type to use for this task"""


class ProcessorTask(BaseTask):
    """Helper class for generating processor tasks"""

    def __init__(
        self,
        parent_id: str,
        bug: EnhancedBug,
        monitor_path: Path,
        use_pernosco: bool = False,
        force_confirm: bool = False,
    ) -> None:
        """Instantiate new instance.

        :param parent_id: ID of parent task
        :param bug: Bug instance
        :param monitor_path: Path to monitor artifact
        :param use_pernosco: Boolean indicating if we need to record a pernosco trace
        :param force_confirm: Boolean indicating if we should confirm regardless of status
        """
        super().__init__(parent_id, bug)
        self.id = slugId()
        self.parent_id = parent_id
        self.monitor_path = monitor_path
        self.dest = Path(f"processor-result-{bug.id}-{self.parent_id}.json")

        self.trace_dest = None
        if use_pernosco:
            self.trace_dest = Path(f"processor-rr-trace-{bug.id}-{parent_id}.tar.gz")

        self.force_confirm = force_confirm
        self._task = None

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Task capabilities"""
        if self.bug.platform.system == "Linux":
            return {
                "devices": {"hostSharedMemory": True, "loopbackAudio": True},
                "disableSeccomp": True,
                "privileged": True,
            }

        return super().capabilities

    @property
    def env(self) -> Dict[str, str]:
        """Environment variables for the task"""
        env_object = {
            "BUG_ACTION": "process",
            "MONITOR_ARTIFACT": str(self.monitor_path),
            "PROCESSOR_ARTIFACT": str(self.dest),
        }

        if self.force_confirm:
            env_object["FORCE_CONFIRM"] = "1"

        if self.trace_dest:
            env_object["TRACE_ARTIFACT"] = str(self.trace_dest)

        if self.bug.platform.system == "Windows":
            env_object["MSYSTEM"] = "MINGW64"

        return env_object

    @property
    def scopes(self) -> List[str]:
        """Scopes applied to the task"""
        scopes = [
            f"queue:get-artifact:project/fuzzing/bugmon/{self.monitor_path}",
            "queue:scheduler-id:-",
        ]
        if self.bug.platform.system == "Linux":
            scopes.extend(
                [
                    "docker-worker:capability:device:hostSharedMemory",
                    "docker-worker:capability:device:loopbackAudio",
                    "docker-worker:capability:disableSeccomp",
                    "docker-worker:capability:privileged",
                ]
            )

        return sorted(scopes)

    @property
    def task(self) -> Dict[str, Any]:
        """Processor task definition"""
        if self._task is None:
            self._task = super().task
            if self.bug.platform.system == "Windows":
                self._task["payload"]["command"] = [
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
                del self._task["payload"]["cache"]
                del self._task["payload"]["capabilities"]
                del self._task["payload"]["image"]
                self._task["payload"]["mounts"] = [
                    {
                        "format": "tar.bz2",
                        "content": {
                            "artifact": "public/msys2.tar.bz2",
                            "namespace": "project.fuzzing.orion.bugmon-win.master",
                        },
                        "directory": ".",
                    }
                ]
                self._task["payload"]["onExitStatus"] = {"retry": [0x40010004]}

                # translate artifacts from dict to array for generic-worker
                artifacts = []
                for name, artifact in self._task["payload"]["artifacts"].items():
                    # strip preceding "/" as generic-worker requires relative paths
                    artifact.update(
                        {"name": name, "path": artifact["path"].lstrip("/")}
                    )
                    artifacts.append(artifact)
                self._task["payload"]["artifacts"] = artifacts

        return self._task

    @property
    def worker_type(self) -> str:
        """The worker type to use for this task"""
        if self.bug.platform.system == "Windows":
            return "bugmon-processor-windows"
        if self.trace_dest:
            # If a trace path was supplied, use the bugmon-pernosco worker
            return "bugmon-pernosco"

        return "bugmon-processor"


class ReporterTask(BaseTask):
    """Helper class for generating reporter tasks"""

    def __init__(
        self,
        parent_id: str,
        bug: EnhancedBug,
        process_path: Path,
        dep: str,
        trace_path: Optional[Path] = None,
    ):
        """Instantiate a new ReporterTask instance.

        :param parent_id: ID of parent task
        :param bug: Bug ID
        :param process_path: Path to process artifact
        :param dep: Task dependency
        :param trace_path: Optional path to trace artifact.
        """
        super().__init__(parent_id, bug)
        self.process_path = process_path

        self.dependency = dep
        self.trace_dest = trace_path

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Task capabilities"""
        if self.bug.platform.system == "Linux":
            return {
                "privileged": True,
            }

        return super().capabilities

    @property
    def env(self) -> Dict[str, str]:
        """Environment variables for the task"""
        env_object = {
            "BUG_ACTION": "report",
            "PROCESSOR_ARTIFACT": str(self.process_path),
        }

        if self.trace_dest is not None:
            env_object["TRACE_ARTIFACT"] = str(self.trace_dest)

        return env_object

    @property
    def scopes(self) -> List[str]:
        """Scopes applied to the task"""
        base = "project/fuzzing/bugmon"
        scopes = [
            "secrets:get:project/fuzzing/bz-api-key",
            "secrets:get:project/fuzzing/pernosco-user",
            "secrets:get:project/fuzzing/pernosco-group",
            "secrets:get:project/fuzzing/pernosco-secret",
            f"queue:get-artifact:{base}/{self.process_path}",
            "queue:scheduler-id:-",
        ]

        if self.trace_dest:
            scopes.append(
                f"queue:get-artifact:{base}/{self.trace_dest}",
            )

        return sorted(scopes)

    @property
    def worker_type(self) -> str:
        """The worker type to use for this task"""
        return "bugmon-monitor"
