# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.

from taskcluster.helper import TaskclusterConfig

ARTIFACT_BASE = "project/fuzzing/bugmon/"

# Shared taskcluster configuration
taskcluster = TaskclusterConfig("https://community-tc.services.mozilla.com")
queue = taskcluster.get_service("queue")
