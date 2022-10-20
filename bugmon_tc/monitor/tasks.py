# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import abc
from datetime import datetime, timedelta

from taskcluster.utils import fromNow
from taskcluster.utils import slugId
from taskcluster.utils import stringDate

MAX_RUNTIME = 14400


class BaseTask(abc.ABC):
    """Abstract class for defining tasks"""

    def __init__(self, parent_id, bug_id):
        self.id = slugId()
        self.parent_id = parent_id
        self.bug_id = bug_id

        self.dependency = None

    @property
    @abc.abstractmethod
    def env(self):
        """Environment variables for the task"""

    @property
    def task(self):
        """Task definition"""
        now = datetime.utcnow()

        dependencies = [self.parent_id]
        if self.dependency is not None:
            dependencies.append(self.dependency)

        return {
            "taskGroupId": self.parent_id,
            "dependencies": dependencies,
            "created": stringDate(now),
            "deadline": stringDate(now + timedelta(seconds=MAX_RUNTIME)),
            "expires": stringDate(fromNow("1 week", now)),
            "provisionerId": "proj-fuzzing",
            "metadata": {
                "description": "",
                "name": f"{__class__.__name__} ({self.bug_id})",
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
                "capabilities": {
                    "devices": {"hostSharedMemory": True, "loopbackAudio": True}
                },
                "env": self.env,
                "features": {"taskclusterProxy": True},
                "image": "mozillasecurity/bugmon:latest",
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

    @property
    def scopes(self):
        """Scopes applied to the task"""
        return [
            "docker-worker:capability:device:hostSharedMemory",
            "docker-worker:capability:device:loopbackAudio",
            "docker-worker:capability:privileged",
            "queue:scheduler-id:-",
        ]

    @property
    @abc.abstractmethod
    def worker_type(self):
        """The worker type to use for this task"""
        pass


class ProcessorTask(BaseTask):
    """Helper class for generating processor tasks"""

    def __init__(
        self,
        parent_id,
        bug_id,
        monitor_path,
        use_pernosco=False,
        force_confirm=False,
    ):
        """Instantiate new instance.

        :param parent_id: ID of parent task
        :param bug_id: Bug ID
        :param src: Path to monitor artifact
        :param kwargs: Additional options
        """
        super().__init__(parent_id, bug_id)
        self.id = slugId()
        self.parent_id = parent_id
        self.bug_id = bug_id
        self.monitor_path = monitor_path
        self.dest = f"processor-result-{self.bug_id}-{self.parent_id}.json"

        self.trace_dest = None
        if use_pernosco:
            self.trace_dest = f"processor-rr-trace-{bug_id}-{parent_id}.tar.gz"

        self.force_confirm = force_confirm

    @property
    def env(self):
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

        return env_object

    @property
    def scopes(self):
        """Scopes applied to the task"""
        scopes = super().scopes
        scopes.extend(
            [
                "docker-worker:capability:disableSeccomp",
                f"queue:get-artifact:project/fuzzing/bugmon/{self.monitor_path}",
            ]
        )

        return scopes

    @property
    def task(self):
        task = super().task
        task["payload"]["capabilities"]["privileged"] = True
        task["payload"]["capabilities"]["disableSeccomp"] = True

        return task

    @property
    def worker_type(self):
        """The worker type to use for this task"""
        # If a trace path was supplied, use the bugmon-pernosco worker
        if self.trace_dest:
            return "bugmon-pernosco"

        return "bugmon-processor"


class ReporterTask(BaseTask):
    """Helper class for generating reporter tasks"""

    def __init__(self, parent_id, bug_id, process_path, dep, trace_path=None):
        """Instantiate a new ReporterTask instance.

        :param parent_id: ID of parent task
        :param bug_id: Bug ID
        :param process_path: Path to process artifact
        :param dep: Task dependency
        :param trace_path: Optional path to trace artifact.
        """
        super().__init__(parent_id, bug_id)
        self.process_path = process_path

        self.dependency = dep
        self.trace_dest = trace_path

    @property
    def env(self):
        """Environment variables for the task"""
        env_object = {
            "BUG_ACTION": "report",
            "PROCESSOR_ARTIFACT": str(self.process_path),
        }

        if self.trace_dest is not None:
            env_object["TRACE_ARTIFACT"] = str(self.trace_dest)

        return env_object

    @property
    def scopes(self):
        """Scopes applied to the task"""
        base = "project/fuzzing/bugmon"
        scopes = super().scopes
        scopes.extend(
            [
                "secrets:get:project/fuzzing/bz-api-key",
                f"queue:get-artifact:{base}/{self.process_path}",
            ]
        )

        if self.trace_dest is not None:
            scopes.extend(
                [
                    "secrets:get:project/fuzzing/pernosco-user",
                    "secrets:get:project/fuzzing/pernosco-group",
                    "secrets:get:project/fuzzing/pernosco-secret",
                    f"queue:get-artifact:{base}/{self.trace_dest}",
                ]
            )

        return scopes

    @property
    def worker_type(self):
        """The worker type to use for this task"""
        return "bugmon-monitor"
