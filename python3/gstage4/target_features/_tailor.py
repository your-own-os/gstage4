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


import os


class TailorSystemd:

    def __init__(self, disable_items, exclude_items):
        self._disableItems = disable_items
        self._excludeItems = exclude_items

    def update_target_settings(self, host_info, target_settings):
        assert "10-tailor-systemd" not in target_settings.install_mask_files

        disableItems = list(self._disableItems)
        excludeItems = list(self._excludeItems)
        td = {}

        def _updateDict(src):
            for k, v in src.items():
                if k not in td:
                    td[k] = []
                td[k] += v

        if "systemd-boot" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*bootctl*",
                    "*/systemd-boot.7.bz2",
                    "*systemd-boot-system-token*",
                ],
            })
            excludeItems.remove("systemd-boot")

        if "systemd-coredump" in excludeItems:
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "systemd-remove-coredump-user"))
            _updateDict({
                "sys-apps/systemd": [
                    "*coredump*",
                ],
            })
            excludeItems.remove("systemd-coredump")

        if "systemd-hostnamed" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*hostname1*",
                    "*hostnamed*",
                    "*hostnamectl*",
                ],
            })
            excludeItems.remove("systemd-hostnamed")

        if "systemd-firstboot" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*firstboot*",
                ],
            })
            excludeItems.remove("systemd-firstboot")

        if "systemd-kexec" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*kexec*",
                ],
            })
            excludeItems.remove("systemd-kexec")

        if "systemd-localed" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*locale1*",
                    "*localed*",
                    "*localectl*",
                ],
            })
            excludeItems.remove("systemd-localed")

        if "systemd-machined" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*machine*",
                    "*nspawn*",
                    "*detect-virt*",
                    "*exit.target",
                    "*systemd-exit.service",
                ],
            })
            excludeItems.remove("systemd-machined")

        if "systemd-networkd" in excludeItems:
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "systemd-remove-network-user"))
            _updateDict({
                "sys-apps/systemd": [
                    "*network*",
                    "/lib/systemd/network*",
                    "/etc/systemd/network",
                ],
            })
            excludeItems.remove("systemd-networkd")

        if "systemd-portabled" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*portable*",
                    "/lib/systemd/portable",
                ],
            })
            excludeItems.remove("systemd-portabled")

        if "systemd-oomd" in excludeItems:
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "systemd-remove-oom-user"))
            _updateDict({
                "sys-apps/systemd": [
                    "*oom1*",
                    "*oomd*",
                    "*oomctl",
                ],
            })
            excludeItems.remove("systemd-oomd")

        if "systemd-pstore" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*pstore*",
                ],
            })
            excludeItems.remove("systemd-pstore")

        if "systemd-resolvd" in excludeItems:
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "systemd-remove-resolve-user"))
            _updateDict({
                "sys-apps/systemd": [
                    "*resolv*",
                ],
            })
            excludeItems.remove("systemd-resolvd")

        if "systemd-sysext" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*sysext*",
                ],
            })
            excludeItems.remove("systemd-sysext")

        if "systemd-sysupdate" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*sysupdate*",
                ],
            })
            excludeItems.remove("systemd-sysupdate")

        if "systemd-sysusers" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*systemd-sysusers*",
                ],
            })
            excludeItems.remove("systemd-sysusers")

        if "systemd-timedated" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*timedate*",
                ],
            })
            excludeItems.remove("systemd-timedated")

        if "systemd-timesyncd" in excludeItems:
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "systemd-remove-timesync-user"))
            _updateDict({
                "sys-apps/systemd": [
                    "*timesync*",
                    "*ntp*",
                    "/lib/systemd/ntp-units.d*",
                ],
            })
            excludeItems.remove("systemd-timesyncd")

        if "systemd-update" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*system-update*",
                    "*update-done*",
                ],
            })
            excludeItems.remove("systemd-update")

        if "systemd-userdbd" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*userdb*",
                ],
            })
            excludeItems.remove("systemd-userdbd")

        if "fstab" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*fstab*",
                ],
            })
            excludeItems.remove("fstab")

        if "fs-operations" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*repart*",
                    "*makefs*",
                    "*growfs*",
                    "*mkswap*",
                ],
            })
            excludeItems.remove("fs-operations")

        if "ldconfig.service" in excludeItems:
            _updateDict({
                "sys-apps/systemd": [
                    "*ldconfig*",
                ],
            })
            excludeItems.remove("ldconfig.service")

        assert len(excludeItems) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-systemd"] = td


class TailorShadow:

    def __init__(self, exclude_items):
        self._items = exclude_items

    def update_target_settings(self, host_info, target_settings):
        assert "10-tailor-shadow" not in target_settings.install_mask_files

        items = self._items
        td = {}

        def _updateDict(src):
            for k, v in src.items():
                if k not in td:
                    td[k] = []
                td[k] += v

        if "logoutd" in items:
            _updateDict({
                "sys-apps/shadow": [
                    "*logoutd*",
                ],
            })
            items.remove("logoutd")

        if "chfn" in items:
            # INSTALL_MASK can not eliminate possibly empty /etc/pam.d directory, so we modify ebuild
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "shadow-remove-chfn"))
            items.remove("chfn")

        if "chsh" in items:
            # INSTALL_MASK can not eliminate possibly empty /etc/pam.d directory, so we modify ebuild
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "shadow-remove-chsh"))
            _updateDict({
                "sys-apps/baselayout": [
                    "/etc/shells",              # no other application uses /etc/shells
                ],
            })
            items.remove("chsh")

        if "expiry" in items:
            _updateDict({
                "sys-apps/shadow": [
                    "*expiry*",
                ],
            })
            items.remove("expiry")

        if "groupmems" in items:
            # INSTALL_MASK can not eliminate possibly empty /etc/pam.d directory, so we modify ebuild
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "shadow-remove-groupmems"))
            items.remove("groupmems")

        if "user-and-group-operations-for-admin" in items:
            # INSTALL_MASK can not eliminate possibly empty /etc/pam.d directory, so we modify ebuild
            target_settings.repo_postsync_patch_directories.append(os.path.join(host_info.repo_postsync_patch_source_dir, "shadow-remove-user-and-group-operations-for-admin"))
            items.remove("user-and-group-operations-for-admin")

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-shadow"] = td
