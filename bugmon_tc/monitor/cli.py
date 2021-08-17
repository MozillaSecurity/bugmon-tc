# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os
from pathlib import Path

from .monitor import BugMonitorTask
from ..common.cli import base_parser


def main(argv=None):
    """
    Generate bugmon tasks
    """

    parser = base_parser(prog="BugmonMonitor")
    parser.add_argument(
        "--api-root",
        type=str,
        help="The target bugzilla instance",
        default=os.environ.get("BZ_API_ROOT"),
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="The bugzilla API key",
        default=os.environ.get("BZ_API_KEY"),
    )
    parser.add_argument(
        "--force-confirm",
        action="store_true",
        help="Force bug confirmation regardless of state",
    )
    parser.add_argument("output", type=Path, help="Path to store artifacts")

    args = parser.parse_args(args=argv)

    logging.basicConfig(level=args.log_level)

    if args.api_root is None or args.api_key is None:
        parser.error("BZ_API_ROOT and BZ_API_KEY must be set!")

    monitor = BugMonitorTask(
        args.api_key,
        args.api_root,
        args.output,
        force_confirm=args.force_confirm,
        dry_run=args.dry_run,
    )
    monitor.create_tasks()
