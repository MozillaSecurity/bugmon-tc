# -*- coding: utf-8 -*-

# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
import argparse
import logging


def base_parser(*args, **kwargs):
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

    parser.set_defaults(log_level=logging.INFO)
    return parser
