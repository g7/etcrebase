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

import os

import shutil

ACTION_REGISTRY = {}
ACTION_DEFAULT_HANDLERS = {}


def register_action(action_name, *files):
    """
    Decorator to register an action in the global registry.
    """

    def decorator(cls):
        # Update registry
        ACTION_REGISTRY[action_name] = cls

        # Update default handlers
        if files:
            ACTION_DEFAULT_HANDLERS.update({x: cls for x in files})

        return cls

    return decorator


class Action:

    """
    Base class for Actions. An action is the actual process of modifying the
    target configuration file.

    Every action is specific to one file.
    """

    def __init__(self, source, target):
        """
        Initialises the class.

        :param: source: the source file
        :param: target: the target file
        """

        self.source = source
        self.target = target

    def apply(self):
        """
        Applies the action. You should override run().
        """

        print("Applying action %s" % self)
        self.run()
        self.sync_permissions()

    def sync_permissions(self):
        """
        Synchronizes the file permissions in the target.
        """

        source_stat = os.stat(self.source)
        os.chmod(self.target, source_stat.st_mode)
        os.chown(self.target, source_stat.st_uid, source_stat.st_gid)

    @property
    def applicable(self):
        """
        Override this to check if the Action can run. There might be cases
        where the Action can't be applied.

        :return: True if the Action can run, False if not
        """

        raise NotImplementedError("Child classes should override the applicable method")

    def run(self):
        """
        Runs the action.
        """

        raise NotImplementedError("Child classes should override the run method")

    def __repr__(self):
        return "<%(name)s: %(source)s -> %(target)s>" % {
            "name": self.__class__.__name__,
            "source": self.source,
            "target": self.target,
        }


class DirectoryAction(Action):

    """
    An action that creates a new directory.
    """

    def run(self):
        if not os.path.exists(self.target):
            os.makedirs(self.target)

    @property
    def applicable(self):
        # New directories are always possible
        return True


@register_action("copy")
class CopyAction(Action):

    """
    An action that simply copies the file to the target.
    """

    def run(self):
        shutil.copy2(self.source, self.target)

    @property
    def applicable(self):
        # Copies are always possible
        return True


@register_action("copyprefertarget")
class CopyPreferTargetAction(CopyAction):

    """
    An action that copies the file only if it's not existing into the target
    """

    @property
    def applicable(self):
        return not os.path.exists(self.target)


@register_action("mergepasswd", "etc/passwd")
class MergePasswdAction(Action):

    """
    An action that merges the contents of passwd.

    Only users with UID >= 1000 are merged.
    """

    def get_lines_to_append(self):
        with open(self.source, "r") as f:
            for line in f:
                try:
                    if ":" in line and int(line.split(":")[2]) >= 1000:
                        yield line
                except:
                    # Unable to parse
                    print("MergePasswdAction: skipping line")

    def run(self):
        with open(self.target, "a") as f:
            for line in self.get_lines_to_append():
                f.write(line)

    @property
    def applicable(self):
        # Always applicable
        return True


@register_action("mergeshadow", "etc/shadow")
class MergeShadowAction(Action):

    """
    An action that merges the contents of shadow.

    Only users with a set password are migrated.
    """

    def evaluate_entries(self):
        with open(self.source, "r") as f:
            for line in f:
                try:
                    if ":" in line and line.split(":")[1]:
                        yield line
                except:
                    # Unable to parse
                    print("MergeShadowAction: skipping line")

    def run(self):
        added_users = set()

        with open(self.target, "r+") as f:
            content = list(self.evaluate_entries()) + f.readlines()
            f.seek(0)
            for line in content:
                if ":" in line:
                    user = line.split(":")[0]
                    if not user in added_users:
                        f.write(line)

    @property
    def applicable(self):
        # Always applicable
        return True


@register_action("mergegroup", "etc/group")
class MergeGroupAction(Action):

    """
    An action that merges the contents of group.

    Only groups with GID >= 1000 and group membership are migrated.
    """

    def evaluate_entries(self):
        with open(self.source, "r") as f:
            for line in f:
                try:
                    gname, _, gid, gmemberships = line.strip().split(":")
                    if int(gid) >= 1000 or gmemberships:
                        yield line
                except:
                    # Unable to parse
                    raise
                    print("MergeGroupAction: skipping line")

    def run(self):
        added_groups = set()

        with open(self.target, "r+") as f:
            content = list(self.evaluate_entries()) + f.readlines()
            f.seek(0)
            for line in content:
                if ":" in line:
                    group = line.split(":")[0]
                    if not group in added_groups:
                        f.write(line)

    @property
    def applicable(self):
        # Always applicable
        return True


@register_action("microosfstab", "etc/fstab")
class MicroOSFstabAction(Action):

    """
    An action that adjusts the contents of /etc/fstab.

    Only the /etc mountpoint is touched.
    """

    fstab_line = "overlay /etc overlay defaults,lowerdir=/sysroot/etc,upperdir=/sysroot/var/lib/overlay/%(snapshot)d/etc,workdir=/sysroot/var/lib/overlay/%(snapshot)d/work-etc,x-systemd.requires-mounts-for=/var,x-systemd.requires-mounts-for=/sysroot/var,x-initrd.mount 0 0"

    def run(self):
        with open(self.source, "r") as f:
            content = f.readlines()

        with open(self.target, "w") as f:
            for line in content:
                if not line.startswith("overlay /etc"):
                    f.write(line)
                else:
                    # Try to infer snapshot number from the target. If not, just
                    # use 1.
                    if self.target.startswith("/.snapshots/"):
                        # maybe a regex? Or is it too much?
                        try:
                            snapshot = int(self.target.split("/", 3)[2])
                        except:
                            print("Unable to detect snapshot number")
                            snapshot = 1

                    f.write(self.fstab_line % {"snapshot": snapshot})

    @property
    def applicable(self):
        # Always applicable
        return True
