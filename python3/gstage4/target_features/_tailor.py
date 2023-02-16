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

    def __init__(self, disable_items, exclude_items):
        self._disableItems = disable_items
        self._excludeItems = exclude_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-systemd" not in target_settings.install_mask_files

        td = {}

        def _updateDict(src):
            for k, v in src.items():
                if k not in td:
                    td[k] = v
                td[k] += v

        if "systemd-boot" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*bootctl*",
                    "*/systemd-boot.7.bz2",
                    "*systemd-boot-system-token*",
                ],
            })
            self._excludeItems.remove("systemd-boot")

        if "systemd-coredump" in self._excludeItems:
            target_settings.postsync_patch_directories.append("/usr/libexec/tailor-systemd-remove-coredump-user")
            _updateDict({
                "sys-apps/systemd": [
                    "*coredump*",
                ],
            })
            self._excludeItems.remove("systemd-coredump")

        if "systemd-hostnamed" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*hostname1*",
                    "*hostnamed*",
                    "*hostnamectl*",
                ],
            })
            self._excludeItems.remove("systemd-hostnamed")

        if "systemd-firstboot" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*firstboot*",
                ],
            })
            self._excludeItems.remove("systemd-firstboot")

        if "systemd-kexec" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*kexec*",
                ],
            })
            self._excludeItems.remove("systemd-kexec")

        if "systemd-localed" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*locale1*",
                    "*localed*",
                    "*localectl*",
                ],
            })
            self._excludeItems.remove("systemd-localed")

        if "systemd-machined" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*machine*",
                    "*nspawn*",
                    "*detect-virt*",
                    "*exit.target",
                    "*systemd-exit.service",
                ],
            })
            self._excludeItems.remove("systemd-machined")

        if "systemd-networkd" in self._excludeItems:
            target_settings.postsync_patch_directories.append("/usr/libexec/tailor-systemd-remove-network-user")
            _updateDict({
                "sys-apps/systemd": [
                    "*network*",
                    "/lib/systemd/network*",
                    "/etc/systemd/network",
                ],
            })
            self._excludeItems.remove("systemd-networkd")

        if "systemd-portabled" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*portable*",
                    "/lib/systemd/portable",
                ],
            })
            self._excludeItems.remove("systemd-portabled")

        if "systemd-oomd" in self._excludeItems:
            target_settings.postsync_patch_directories.append("/usr/libexec/tailor-systemd-remove-oom-user")
            _updateDict({
                "sys-apps/systemd": [
                    "*oom1*",
                    "*oomd*",
                    "*oomctl",
                ],
            })
            self._excludeItems.remove("systemd-oomd")

        if "systemd-pstore" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*pstore*",
                ],
            })
            self._excludeItems.remove("systemd-pstore")

        if "systemd-resolvd" in self._excludeItems:
            target_settings.postsync_patch_directories.append("/usr/libexec/tailor-systemd-remove-resolve-user")
            _updateDict({
                "sys-apps/systemd": [
                    "*resolv*",
                ],
            })
            self._excludeItems.remove("systemd-resolvd")

        if "systemd-sysext" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*sysext*",
                ],
            })
            self._excludeItems.remove("systemd-sysext")

        if "systemd-sysupdate" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*sysupdate*",
                ],
            })
            self._excludeItems.remove("systemd-sysupdate")

        if "systemd-sysusers" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*systemd-sysusers*",
                ],
            })
            self._excludeItems.remove("systemd-sysusers")

        if "systemd-timedated" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*timedate*",
                ],
            })
            self._excludeItems.remove("systemd-timedated")

        if "systemd-timesyncd" in self._excludeItems:
            target_settings.postsync_patch_directories.append("/usr/libexec/tailor-systemd-remove-timesync-user")
            _updateDict({
                "sys-apps/systemd": [
                    "*timesync*",
                    "*ntp*",
                    "/lib/systemd/ntp-units.d*",
                ],
            })
            self._excludeItems.remove("systemd-timesyncd")

        if "systemd-update" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*system-update*",
                    "*update-done*",
                ],
            })
            self._excludeItems.remove("systemd-update")

        if "systemd-userdbd" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*userdb*",
                ],
            })
            self._excludeItems.remove("systemd-userdbd")

        if "fstab" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*fstab*",
                ],
            })
            self._excludeItems.remove("fstab")

        if "fs-operations" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*repart*",
                    "*makefs*",
                    "*growfs*",
                    "*mkswap*",
                ],
            })
            self._excludeItems.remove("fs-operations")

        if "ldconfig.service" in self._excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*ldconfig*",
                ],
            })
            self._excludeItems.remove("ldconfig.service")

        assert len(self._excludeItems) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-systemd"] = td


class TailorShadow:

    def __init__(self, exclude_items):
        self._items = exclude_items

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
                    "/etc/pam.d/shfn",      # FIXME: it seems has something to do with chsh according to ebuild file
                ],
                "sys-apps/baselayout": [
                    "/etc/shells",
                ],
            })
            self._items.remove("chsh")

        if "expiry" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*expiry*",
                ],
            })
            self._items.remove("expiry")

        if "groupmems" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*groupmems*",
                ],
            })
            self._items.remove("groupmems")

        if "user-and-group-operations-for-admin" in self._items:
            _updateDict({
                "sys-apps/shadow": [
                    "*chage*",              # for root to change a user's password expiration
                    "*chpasswd*",           # change passwords in batch mode, obviously it's for root although it has a PAM config
                    "*pwck*",
                    "*grpck*",
                    "*pwconv*",
                    "*pwunconv*",
                    "*grpconv*",
                    "*grpunconv*",
                    "*useradd*",
                    "*usermod*",
                    "*userdel*",
                    "*newusers*",           # create users in batch mode, obviously it's for root although it has a PAM config
                    "*groupadd*",
                    "*groupmod*",
                    "*groupdel*",
                    "/etc/pam.d/shadow",    # this is the PAM config for user{add,del,mod} and group{add,del,mod}
                ],
            })
            self._items.remove("user-and-group-operations-for-admin")

        assert len(self._items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-shadow"] = td
