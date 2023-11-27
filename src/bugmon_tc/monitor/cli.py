# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import logging
from pathlib import Path
from typing import Any

from .monitor import BugMonitorTask
from ..common import get_bugzilla_auth
from ..common.cli import base_parser

LOG = logging.getLogger(__name__)


def parse_args(argv: Any = None) -> argparse.Namespace:
    """Parse arguments"""
    parser = base_parser("BugmonMonitor")
    parser.add_argument(
        "--force-confirm",
        action="store_true",
        help="Force bug confirmation regardless of state",
    )
    parser.add_argument("output", type=Path, help="Path to store artifacts")
    args = parser.parse_args(args=argv)
    logging.basicConfig(level=args.log_level)

    return args


def main(argv: Any = None) -> None:
    """Generate bugmon tasks"""
    args = parse_args(argv)
    bz_creds = get_bugzilla_auth()

    monitor = BugMonitorTask(
        bz_creds["KEY"],
        bz_creds["URL"],
        force_confirm=args.force_confirm,
    )
    monitor.create_tasks(args.output)
