#!/usr/bin/env python3

# Copyright (c) 2020-2021 Fpemud <fpemud@sina.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import passlib.hosts
from ..scripts import OneLinerScript
from ..scripts import ScriptInstallPackages
from .._builder import CustomAction


class SimpleCustomAction(CustomAction):                         # FIXME: should be renamed to UserDefinedAction

    def __init__(self, *custom_scripts, after=[], before=[]):
        self._custom_scripts = custom_scripts
        self._after = after
        self._before = before

    @property
    def custom_scripts(self):
        return self._custom_scripts

    def get_after(self):
        return self._after

    def get_before(self):
        return self._before


class SetRootPassword(CustomAction):

    def __init__(self, password):
        self._hash = passlib.hosts.linux_context.hash(password)

    @property
    def custom_scripts(self):
        return [OneLinerScript("sed -i 's#^root:[^:]*:#root:%s:#' /etc/shadow" % (self._hash))]

    def get_after(self):
        return ["init_confdir", "create_overlays", "update_world", "install_kernel", "enable_services"]

    def get_before(self):
        return []


class AddUser(CustomAction):

    def __init__(self, username, password, comment=""):
        self._user = username
        self._pwd = password
        self._comment = comment

    @property
    def custom_scripts(self):
        return []

    def get_after(self):
        return []

    def get_before(self):
        return []


class InstallPackages(CustomAction):

    def __init__(self, packages, record_to_world):
        self._script = ScriptInstallPackages(packages, record_to_world, 0)

    @property
    def custom_scripts(self):
        return [self._script]

    def get_after(self):
        return ["init_confdir", "create_overlays"]

    def get_before(self):
        return ["update_world", "install_kernel", "enable_services"]


class RemovePackagesFromWorld(CustomAction):

    def __init__(self, packages):
        self._pkgList = packages

    @property
    def custom_scripts(self):
        return []

    def get_after(self):
        return []

    def get_before(self):
        return []


class RemoveUsrSrcDirectoryContent(CustomAction):

    @property
    def custom_scripts(self):
        return [OneLinerScript("rm -rf /usr/src/*")]

    def get_after(self):
        return ["init_confdir", "create_overlays", "update_world", "install_kernel"]

    def get_before(self):
        return []
