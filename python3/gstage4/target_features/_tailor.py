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


class TailorSystemd:

    def __init__(self, items):
        self._items = items
        assert False


class TailorShadow:

    def __init__(self, items):
        self._items = items

    def update_target_settings(self, target_settings):
        assert "10-tailor-shadow" not in target_settings.install_mask_files

        td = {}

        def _updateDict(src):
            for k, v in src.items():
                if k not in td:
                    td[k] = v
                td[k] += v

        if "logoutd" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*logoutd*",
                ],
            })
            self._items.remove("logoutd")

        if "chage" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*chage*",
                    "*expiry*",
                ],
            })
            self._items.remove("chage")

        if "chfn" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*chfn*",
                ],
            })
            self._items.remove("chfn")

        if "chsh" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*chsh*",
                ],
                "sys-apps/baselayout": [
                    "/etc/shells",
                ],
            })
            self._items.remove("chsh")

        if "groupmems" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*groupmems*",
                ],
            })
            self._items.remove("groupmems")

        if "pwck-and-grpck" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*pwck*",
                    "*grpck*",
                ],
            })
            self._items.remove("pwck-and-grpck")

        if "pwconv-and-grpconv" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*pwconv*",
                    "*pwunconv*",
                    "*grpconv*",
                    "*grpunconv*",
                ],
            })
            self._items.remove("pwconv-and-grpconv")

        if "user-and-group-operations" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*useradd*",
                    "*usermod*",
                    "*userdel*",
                    "*newusers*",
                    "*groupadd*",
                    "*groupmod*",
                    "*groupdel*",
                ],
            })
            self._items.remove("user-and-group-operations")

        assert len(self._items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-shadow"] = td
