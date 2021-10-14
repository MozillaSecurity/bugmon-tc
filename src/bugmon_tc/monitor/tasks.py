# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
from datetime import datetime, timedelta

from taskcluster.utils import fromNow
from taskcluster.utils import slugId
from taskcluster.utils import stringDate

MAX_RUNTIME = 14400


class ProcessorTask:
    """
    Helper class for generating processor tasks
    """

    TASK_NAME = "Processor Task"
    WORKER_TYPE = "bugmon-processor"

    def __init__(self, parent_id, src, bug_id, **kwargs):
        """

        :param parent_id: ID of parent task
        :param src: Path to src artifact
        :param bug_id: Bug ID
        :param kwargs: Additional options
        """
        self.id = slugId()
        self.parent_id = parent_id
        self.src = src
        self.bug_id = bug_id

        prefix = self.TASK_NAME.lower().replace(" ", "-")
        self.dest = f"{prefix}-{self.bug_id}-{self.parent_id}.json"

        self.dependency = kwargs.get("dep", None)
        self.force_confirm = kwargs.get("force_confirm", False)

    @property
    def env(self):
        """Environment variables for the task"""
        env_object = {
            "BUG_ACTION": "process",
            "MONITOR_ARTIFACT": self.src,
            "PROCESSOR_ARTIFACT": self.dest,
        }

        if self.force_confirm:
            env_object["FORCE_CONFIRM"] = "1"

        return env_object

    @property
    def scopes(self):
        """Scopes applied to the task"""
        return [
            "docker-worker:capability:device:hostSharedMemory",
            "docker-worker:capability:device:loopbackAudio",
            "docker-worker:capability:privileged",
            "queue:scheduler-id:-",
            f"queue:get-artifact:project/fuzzing/bugmon/{self.src}",
        ]

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
                "name": f"{self.TASK_NAME} ({self.bug_id})",
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
            "workerType": self.WORKER_TYPE,
            "retries": 5,
            "routes": ["notify.email.jkratzer@mozilla.com.on-failed"],
            "schedulerId": "-",
            "scopes": self.scopes,
            "tags": {},
        }


class ReporterTask(ProcessorTask):
    """
    Helper class for generating reporter tasks
    """

    TASK_NAME = "Reporter Task"
    WORKER_TYPE = "bugmon-monitor"

    def __init__(self, parent_id, src, bug_id, dep=None):
        super().__init__(parent_id, src, bug_id, dep=dep)

    @property
    def env(self):
        """Environment variables for the task"""
        return {
            "BUG_ACTION": "report",
            "PROCESSOR_ARTIFACT": self.src,
        }

    @property
    def scopes(self):
        """Scopes applied to the task"""
        return [
            "docker-worker:capability:device:hostSharedMemory",
            "docker-worker:capability:device:loopbackAudio",
            "queue:scheduler-id:-",
            f"queue:get-artifact:project/fuzzing/bugmon/{self.src}",
            "secrets:get:project/fuzzing/bz-api-key",
        ]
