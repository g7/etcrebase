# -*- coding: utf-8 -*-
#
# etcrebase
# Copyright (C) 2023  Eugenio Paolantonio <me@medesimo.eu>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from etcrebase import Configuration

import sys

import argparse


def build_parser():
    """
    Builds an ArgumentParser with the allowed arguments.

    :return: an argparse.ArgumentParser object
    """

    parser = argparse.ArgumentParser(
        description="Utility to rebase configuration files in /etc into another tree."
    )
    parser.add_argument("target", type=str, help="the target directory")
    parser.add_argument(
        "--source",
        "-s",
        type=str,
        default="/",
        help="the source directory (defaults to /)",
    )
    parser.add_argument("--dry-run", "-d", action="store_true", help="simulate changes")

    return parser


def main():
    """
    The main entrypoint for the command line.
    """

    parser = build_parser()

    parsed = parser.parse_args(sys.argv[1:])

    for action in Configuration(parsed.source, parsed.target):
        if not action.applicable:
            print("Skipping %s as it's not applicable" % action)

        if parsed.dry_run:
            print(action)
        else:
            action.apply()
