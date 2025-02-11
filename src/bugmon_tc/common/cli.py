# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import logging
import os
from typing import Any


def base_parser(*args: Any, **kwargs: Any) -> argparse.ArgumentParser:
    """
    Common arguments shared across modules
    """
    parser = argparse.ArgumentParser(*args, **kwargs)
    parser.add_argument("--dry-run", action="store_true", help="Perform tasks locally")

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--quiet",
        "-q",
        dest="log_level",
        action="store_const",
        const=logging.WARNING,
        help="Be less verbose",
    )
    group.add_argument(
        "--verbose",
        "-v",
        dest="log_level",
        action="store_const",
        const=logging.DEBUG,
        help="Be more verbose",
    )

    log_level = logging.INFO
    if bool(os.getenv("DEBUG")):
        log_level = logging.DEBUG

    parser.set_defaults(log_level=log_level)

    return parser
