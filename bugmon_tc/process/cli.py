# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import json
import logging
import os
from pathlib import Path

from ..common.cli import base_parser
from .process import TaskProcessor

LOG = logging.getLogger(__name__)


def main(argv=None):
    """
    Process bug
    """

    parser = base_parser(prog="BugmonProcessor")
    parser.add_argument("artifact", type=str, help="Path to artifact")
    parser.add_argument("output", type=Path, help="Path to store result")

    args = parser.parse_args(args=argv)
    logging.basicConfig(level=args.log_level)

    if os.path.exists(args.output):
        raise parser.error("Output path exists")

    processor = TaskProcessor(args.dry_run, args.artifact)
    results = processor.process()

    with open(args.output, "w") as file:
        json.dump(results, file, indent=2)
