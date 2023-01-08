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


import crypt
from .. import CustomAction
from ..scripts import OneLinerScript
from ..scripts import ScriptFromBuffer
from ..scripts import ScriptInstallPackages
from ..scripts import ScriptUpdateWorld


class SimpleCustomAction(CustomAction):                         # FIXME: should be renamed to UserDefinedAction

    def __init__(self, *custom_scripts, after=[], before=[]):
        self._custom_scripts = custom_scripts
        self._after = after
        self._before = before

    @property
    def custom_scripts(self):
        return self._custom_scripts

    @property
    def after(self):
        return self._after

    @property
    def before(self):
        return self._before


class SetRootPassword(CustomAction):

    def __init__(self, password):
        self._hash = crypt.crypt(password)

    @property
    def custom_scripts(self):
        return [OneLinerScript("sed -i 's#^root:[^:]*:#root:%s:#' /etc/shadow" % (self._hash))]

    @property
    def after(self):
        return ["init_confdir", "create_overlays", "update_world", "install_kernel", "enable_services"]

    @property
    def before(self):
        return []


class AddUser(CustomAction):

    def __init__(self, username, password, comment=""):
        self._user = username
        self._pwd = password
        self._comment = comment

    @property
    def custom_scripts(self):
        return []

    @property
    def after(self):
        return []

    @property
    def before(self):
        return []


class InstallPackages:

    def __init__(self, packages):
        self._script = ScriptInstallPackages(packages, 0)

    @property
    def custom_scripts(self):
        return [self._script]

    @property
    def after(self):
        return ["init_confdir", "create_overlays"]

    @property
    def before(self):
        return ["update_world", "install_kernel", "enable_services"]


class RemovePackagesFromWorld:

    def __init__(self, packages):
        self._pkgList = packages

    @property
    def custom_scripts(self):
        return []

    @property
    def after(self):
        return []

    @property
    def before(self):
        return []


class DisablePcSpeaker:

    @property
    def custom_scripts(self):
        return [ScriptFromBuffer(self._scriptFileContent)]

    @property
    def after(self):
        return ["init_confdir", "create_overlays", "update_world", "install_kernel", "enable_services"]

    @property
    def before(self):
        return []

    _scriptFileContent = """
#!/bin/sh
echo "blacklist pcspkr" > /etc/modprobe.d/disable-pc-speaker.conf
"""
