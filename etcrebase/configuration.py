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

from .action import ACTION_REGISTRY, ACTION_DEFAULT_HANDLERS, DirectoryAction

import os

DEFAULT_CONFIGS_LIST_FILE = "/usr/share/etcrebase/configs-microos.txt"


class Configuration:

    """
    Analyses the configuration of a source (that can be a running system) and
    proposes relevant actions in order to apply the changes in a new installation.

    This object is an iterable. Example usage:

    for action in Configuration("/", "/target"):
        print("Action %s" % action)
        if action.applicable:
            action.apply()
    """

    def __init__(
        self, source, target, filelist=DEFAULT_CONFIGS_LIST_FILE, default_handler="copy"
    ):
        """
        Initialises the class.

        :param: source: the source directory of the filesystem tree
        :param: target: the target directory
        :param: filelist: the configuration to use (uses the default one if omitted)
        :param: default_handler: the default handler (default is copy)
        """

        self.source = source
        self.target = target
        self.rules = {**ACTION_DEFAULT_HANDLERS}  # pre-populate

        # Load filelist
        with open(filelist, "r") as f:
            for line in f:
                linecontent = line.strip().split(";", 1)
                filename = (
                    linecontent[0]
                    if not linecontent[0].startswith("/")
                    else linecontent[0][1:]
                )

                if len(linecontent) == 2:
                    # Handler specified
                    handler = linecontent[1]
                elif not filename in self.rules:
                    # Handler not specified, and not overriden internally, use
                    # the default handler
                    handler = default_handler
                else:
                    # Already in self.rules
                    continue

                self.rules[filename] = ACTION_REGISTRY[handler]

    def __iter__(self):
        # The rules are evaluated top-bottom.
        # During evaluation, later rules in a directory take precedence. For example:
        #
        #    /etc/dir1/;copy
        #    /etc/dir1/dir2/file;diff
        #
        # Every content in /etc/dir1 will be copied *except* for /etc/dir1/dir2/file,
        # that will use the diff handler instead.
        expanded_actions = {}
        for rule, handler in self.rules.items():
            source_full_path = os.path.join(self.source, rule)
            target_full_path = os.path.join(self.target, rule)

            if not os.path.exists(source_full_path):
                continue

            # We should create the directory tree as well
            directory_path = source_dirname = os.path.dirname(source_full_path)
            target_dirname = os.path.dirname(target_full_path)
            while directory_path != self.source:
                if not directory_path in expanded_actions:
                    expanded_actions[directory_path] = DirectoryAction(
                        directory_path,
                        directory_path.replace(source_dirname, target_dirname, 1),
                    )
                directory_path = source_dirname = os.path.dirname(source_dirname)
                target_dirname = os.path.dirname(target_dirname)

            if os.path.isdir(source_full_path):
                for walk_root, walk_dirs, walk_files in os.walk(source_full_path):
                    # Create new directories actions for every dir we encounter
                    for walk_dir_name in walk_dirs:
                        _source = os.path.join(walk_root, walk_dir_name)
                        expanded_actions[_source] = DirectoryAction(
                            _source,
                            _source.replace(source_full_path, target_full_path, 1),
                        )

                    # Use the specified handler for actual files
                    for walk_file_name in walk_files:
                        _source = os.path.join(walk_root, walk_file_name)
                        expanded_actions[_source] = handler(
                            _source,
                            _source.replace(source_full_path, target_full_path, 1),
                        )
            else:
                expanded_actions[source_full_path] = handler(
                    source_full_path, target_full_path
                )

        yield from sorted(expanded_actions.values(), key=lambda x: x.source)
