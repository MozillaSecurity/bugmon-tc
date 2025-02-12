# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
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
        "--debug",
        "-d",
        dest="debug",
        action="store_true",
        help="Enable verbose debugging output",
    )

    enable_debug = False
    if bool(os.getenv("DEBUG")):
        enable_debug = True

    parser.set_defaults(debug=enable_debug)

    return parser
