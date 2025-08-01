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


from .._util import Util


class TailorWine:

    def __init__(self, disable_items=[]):
        self._disableItems = disable_items

    def update_target_settings(self, target_settings):
        disableItems = list(self._disableItems)

        if "auto-adding-menu-entries" in disableItems:
            target_settings.repo_postsync_patch_directories.append("wine-disable-auto-adding-menu-entries")
            disableItems.remove("auto-adding-menu-entries")

        assert len(disableItems) == 0


class TailorSystemd:

    def __init__(self, disable_items=[], remove_items=[]):
        self._disableItems = disable_items
        self._removeItems = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-systemd" not in target_settings.pkg_mask_files
        assert "10-tailor-systemd" not in target_settings.install_mask_files

        disableItems = list(self._disableItems)
        if True:
            if "systemd-udevd-socket-activation" in disableItems:
                target_settings.repo_postsync_patch_directories.append("systemd-disable-systemd-udevd-socket-activation")
                disableItems.remove("systemd-udevd-socket-activation")

            if "kmod-static-nodes" in disableItems:
                target_settings.repo_postsync_patch_directories.append("systemd-disable-kmod-static-nodes")
                disableItems.remove("kmod-static-nodes")

            assert len(disableItems) == 0

        removeItems = list(self._removeItems)
        if True:
            td = {}
            tm = []

            if "systemd-battery-check" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*battery-check*",
                    ],
                })
                removeItems.remove("systemd-battery-check")

            if "systemd-backlight" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*backlight*",
                    ],
                })
                removeItems.remove("systemd-backlight")

            if "systemd-boot" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*bootctl*",
                        "*/systemd-boot.7.bz2",
                        "*systemd-boot-system-token*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*bootctl*",
                        "*systemd-boot-system-token*",
                    ],
                })
                removeItems.remove("systemd-boot")

            if "systemd-coredump" in removeItems:
                target_settings.repo_postsync_patch_directories.append("systemd-remove-coredump-user")
                tm += [
                    "acct-user/systemd-coredump",
                    "acct-group/systemd-coredump",
                ]
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*coredump*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*coredump*",
                    ],
                })
                removeItems.remove("systemd-coredump")

            if "systemd-dissect" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-dissect*",
                        "*mount.ddi*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*systemd-dissect*",
                    ],
                })
                removeItems.remove("systemd-dissect")

            if "systemd-firstboot" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*firstboot*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*systemd-firstboot*",
                    ],
                    "app-i18n/man-pages-zh_CN": [       # why i18n man pages not in the original package itself?
                        "*systemd-firstboot*",
                    ],
                })
                removeItems.remove("systemd-firstboot")

            if "systemd-hostnamed" in removeItems:
                tm += [
                    "acct-group/systemd-hostname",
                ]
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*hostname1*",
                        "*hostnamed*",
                        "*hostnamectl*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*hostnamed*",
                        "*hostnamectl*",
                    ],
                    "app-i18n/man-pages-zh_CN": [       # why i18n man pages not in the original package itself?
                        "*hostnamed*",
                        "*hostnamectl*",
                    ],
                })
                removeItems.remove("systemd-hostnamed")

            if "systemd-kexec" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*kexec*",
                    ],
                })
                removeItems.remove("systemd-kexec")

            if "systemd-localed" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*locale1*",
                        "*localed*",
                        "*localectl*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*localed*",
                        "*localectl*",
                    ],
                })
                removeItems.remove("systemd-localed")

            if "systemd-machined" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*machine*",
                        "*nspawn*",
                        "*vmspawn*",
                        "*detect-virt*",
                        "*exit.target",
                        "*systemd-exit.service",
                        "/usr/lib/systemd/system/machines.target.wants",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*machine*",                    # warn: may hide extra files
                    ],
                })
                removeItems.remove("systemd-machined")

            if "systemd-networkd" in removeItems:
                target_settings.repo_postsync_patch_directories.append("systemd-remove-network-user")
                tm += [
                    "acct-user/systemd-network",
                    "acct-group/systemd-network",
                ]
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*network*",
                        "/usr/lib/systemd/network*",
                        "/etc/systemd/network",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*networkctl*",
                        "*networkd*",
                        "*systemd.network*",
                        "*systemd-network*",
                    ],
                    "app-i18n/man-pages-zh_CN": [       # why i18n man pages not in the original package itself?
                        "*networkctl*",
                        "*networkd*",
                        "*systemd.network*",
                        "*systemd-network*",
                    ],
                    "*/*": [
                        "/usr/lib/systemd/network",
                    ],
                })
                removeItems.remove("systemd-networkd")

            if "systemd-portabled" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*portable*",
                        "/usr/lib/systemd/portable",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*portablectl*",
                        "*systemd-portabled*",
                    ],
                })
                removeItems.remove("systemd-portabled")

            if "systemd-oomd" in removeItems:
                target_settings.repo_postsync_patch_directories.append("systemd-remove-oom-user")
                tm += [
                    "acct-user/systemd-oom",
                    "acct-group/systemd-oom",
                ]
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*oom1*",
                        "*oomd*",
                        "*oomctl*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*oomctl*",
                        "*oomd*",
                    ],
                })
                removeItems.remove("systemd-oomd")

            if "systemd-pstore" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*pstore*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*pstore*",                     # warn: may hide extra files
                    ],
                })
                removeItems.remove("systemd-pstore")

            if "systemd-resolvd" in removeItems:
                target_settings.repo_postsync_patch_directories.append("systemd-remove-resolve-user")
                tm += [
                    "acct-user/systemd-resolve",
                    "acct-group/systemd-resolve",
                ]
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*resolv*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*resolvectl*",
                        "*resolved*",
                        "*nss-resolve*",
                    ],
                    "app-i18n/man-pages-zh_CN": [       # why i18n man pages not in the original package itself?
                        "*resolvectl*",
                        "*resolved*",
                        "*nss-resolve*",
                    ],
                })
                removeItems.remove("systemd-resolvd")

            if "systemd-storagetm" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*storagetm*",
                        "*storage-target-mode.target",
                    ],
                })
                removeItems.remove("systemd-storagetm")

            if "systemd-sysext" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*sysext*",
                        "*confext*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*systemd-sysext*",
                    ],
                })
                removeItems.remove("systemd-sysext")

            if "systemd-sysupdate" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*sysupdate*",
                    ],
                })
                removeItems.remove("systemd-sysupdate")

            if "systemd-sysusers" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*sysusers*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*sysusers*",                   # warn: may hide extra files
                    ],
                })
                removeItems.remove("systemd-sysusers")

            if "systemd-timedated" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*timedate*",
                        "/usr/lib/systemd/ntp-units.d*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*timedatectl*",
                        "*systemd-timedated*",
                    ],
                    "*/*": [
                        "/usr/lib/systemd/ntp-units.d",
                    ],
                })
                removeItems.remove("systemd-timedated")

            if "systemd-timesyncd" in removeItems:
                target_settings.repo_postsync_patch_directories.append("systemd-remove-timesync-user")
                tm += [
                    "acct-user/systemd-timesync",
                    "acct-group/systemd-timesync",
                ]
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*timesync*",
                        "*ntp*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*timesyncd*",
                    ],
                })
                removeItems.remove("systemd-timesyncd")

            if "systemd-update" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*system-update*",
                        "*systemd-update-helper*",
                        "*update-done*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*systemd-system-update*",
                    ],
                })
                removeItems.remove("systemd-update")

            if "systemd-userdbd" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*userdb*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*userdb*",
                    ],
                })
                removeItems.remove("systemd-userdbd")

            if "systemd-ssh-proxy" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-ssh-proxy*",
                        "/etc/ssh",
                        "/usr/lib/systemd/ssh_config.d",
                        "/usr/lib/systemd/sshd_config.d",
                    ],
                })
                removeItems.remove("systemd-ssh-proxy")

            if "systemd-run-generator" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-run-generator*",
                    ],
                })
                removeItems.remove("systemd-run-generator")

            if "systemd-efi-boot-generator" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-efi-boot-generator*",
                    ],
                })
                removeItems.remove("systemd-efi-boot-generator")

            if "systemd-gpt-auto-generator" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-gpt-auto-generator*",
                    ],
                })
                removeItems.remove("systemd-gpt-auto-generator")

            if "systemd-ssh-generator" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-ssh-generator*",
                    ],
                })
                removeItems.remove("systemd-ssh-generator")

            if "kernel-management" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*kernel-install*",
                        "/usr/lib/kernel*",
                    ],
                })
                removeItems.remove("kernel-management")

            if "fstab" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*fstab*",
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*systemd-fstab*",
                    ],
                })
                removeItems.remove("fstab")

            if "fs-operations" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*repart*",
                        "/usr/lib/systemd/repart",
                        "*makefs*",
                        "*growfs*",
                        "*mkswap*",
                        "/usr/lib/tmpfiles.d/etc.conf",        # don't auto create baselayout files or directories
                        "/usr/lib/tmpfiles.d/home.conf",       # same as above
                        "/usr/lib/tmpfiles.d/legacy.conf",     # same as above
                        "/usr/lib/tmpfiles.d/tmp.conf",        # same as above
                        "/usr/lib/tmpfiles.d/var.conf",        # same as above
                    ],
                    "app-i18n/man-pages-l10n": [        # why i18n man pages not in the original package itself?
                        "*repart*",
                        "*makefs*",
                    ],
                })
                removeItems.remove("fs-operations")

            if "ldconfig.service" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*ldconfig*",
                    ],
                })
                removeItems.remove("ldconfig.service")

            if "initrd-facility" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*initrd*",
                        "*volatile-root*",
                        "*hibernate-resume*",
                    ],
                })
                removeItems.remove("initrd-facility")

            if "debug-facility" in removeItems:
                _updateDict(td, {
                    "sys-apps/systemd": [
                        "*systemd-debug-generator*",
                        "*debug-shell*",
                    ],
                })
                removeItems.remove("debug-facility")

            if len(tm) > 0:
                target_settings.pkg_mask_files["10-tailor-systemd"] = "\n".join(tm) + "\n"
            if len(td) > 0:
                target_settings.install_mask_files["10-tailor-systemd"] = td

            assert len(removeItems) == 0


class TailorBaselayout:

    def __init__(self, remove_items=[]):
        self._items = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-baselayout" not in target_settings.install_mask_files

        items = list(self._items)
        td = {}

        if "/etc/shells" in items:
            _updateDict(td, {
                "sys-apps/baselayout": [
                    "/etc/shells",
                ],
            })
            items.remove("/etc/shells")

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-baselayout"] = td


class TailorShadow:

    def __init__(self, remove_items=[]):
        self._items = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-shadow" not in target_settings.install_mask_files

        items = list(self._items)
        td = {}

        if "logoutd" in items:
            _updateDict(td, {
                "sys-apps/shadow": [
                    "*logoutd*",
                ],
            })
            items.remove("logoutd")

        if "chfn" in items:
            _updateDict(td, {
                "sys-apps/shadow": [
                    "*chfn*",
                ],
            })
            items.remove("chfn")

        if "chsh" in items:
            _updateDict(td, {
                "sys-apps/shadow": [
                    "*chsh*",
                ],
                "sys-apps/baselayout": [
                    "/etc/shells",              # no other application uses /etc/shells
                ],
            })
            items.remove("chsh")

        if "expiry" in items:
            _updateDict(td, {
                "sys-apps/shadow": [
                    "*expiry*",
                ],
            })
            items.remove("expiry")

        if "groupmems" in items:
            _updateDict(td, {
                "sys-apps/shadow": [
                    "*groupmems*",
                ],
            })
            items.remove("groupmems")

        if "old-group-operations" in items:         # group operations are old, no one use them in a modern distribution
            _updateDict(td, {
                "sys-apps/shadow": [
                    "gpasswd*",
                    "*newgrp*",
                    "*sg*",
                ],
            })
            items.remove("old-group-operations")

        if "user-and-group-operations-for-admin" in items:
            _updateDict(td, {
                "sys-apps/shadow": [
                    "*chage*",
                    "*chpasswd*",
                    "*chgpasswd*",
                    "*pwck*",
                    "*grpck*",
                    "*pwconv*",
                    "*pwunconv*",
                    "*grpconv*",
                    "*grpunconv*",
                    "*useradd*",
                    "*usermod*",
                    "*userdel*",
                    "*newusers*",
                    "*groupadd*",
                    "*groupmod*",
                    "*groupdel*",
                    "/etc/pam.d/shadow",
                ],
                "*/*": [
                    "/etc/skel",
                ],
            })
            items.remove("user-and-group-operations-for-admin")

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-shadow"] = td


class TailorAvahi:

    def __init__(self, disable_items=[]):
        self._disableItems = disable_items

    def update_target_settings(self, target_settings):
        disableItems = list(self._disableItems)

        if "auto-activation" in disableItems:
            target_settings.repo_postsync_patch_directories.append("avahi-disable-auto-activation")
            disableItems.remove("auto-activation")

        assert len(disableItems) == 0


class TailorEselect:

    def __init__(self, remove_items=[]):
        self._removeItems = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-eselect" not in target_settings.install_mask_files

        items = list(self._removeItems)
        td = {}

        def _simpleRemoveModule(outerName):
            name = outerName.replace("-module", "")
            if outerName in items:
                _updateDict(td, {
                    "app-admin/eselect": [
                        "*%s*" % (name),
                    ],
                })
                items.remove(outerName)

        _simpleRemoveModule("editor-module")

        _simpleRemoveModule("env-module")

        _simpleRemoveModule("kernel-module")

        _simpleRemoveModule("locale-module")

        _simpleRemoveModule("pager-module")

        _simpleRemoveModule("profile-module")

        _simpleRemoveModule("rc-module")

        _simpleRemoveModule("visual-module")

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-eselect"] = td


class TailorGit:

    def __init__(self, add_items=[]):
        self._addItems = add_items

    def update_target_settings(self, target_settings):
        items = list(self._addItems)

        bHttpConnectionTimeout = False
        if "http-connection-timeout-extension" in items:
            target_settings.repo_postsync_patch_directories.append("git-add-http-connection-timeout-extension")
            items.remove("http-connection-timeout-extension")
            bHttpConnectionTimeout = True

        if "robust-extension" in items:
            assert bHttpConnectionTimeout
            target_settings.repo_postsync_patch_directories.append("git-add-robust-extension")
            items.remove("robust-extension")

        assert len(items) == 0


class TailorWget:

    def __init__(self, add_items=[]):
        self._addItems = add_items

    def update_target_settings(self, target_settings):
        items = list(self._addItems)

        if "robust-extension" in items:
            target_settings.repo_postsync_patch_directories.append("wget-add-robust-extension")
            items.remove("robust-extension")

        assert len(items) == 0


class TailorRsync:

    def __init__(self, add_items=[]):
        self._addItems = add_items

    def update_target_settings(self, target_settings):
        items = list(self._addItems)

        if "robust-extension" in items:
            target_settings.repo_postsync_patch_directories.append("rsync-add-robust-extension")
            items.remove("robust-extension")

        assert len(items) == 0


class TailorLmSensors:

    def __init__(self, remove_items=[]):
        self._removeItems = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-lm-sensors" not in target_settings.install_mask_files

        items = list(self._removeItems)
        td = {}

        if "fancontrol" in items:
            _updateDict(td, {
                "sys-apps/lm-sensors": [
                    "*fancontrol*",
                    "*pwmconfig*",
                ],
            })
            items.remove("fancontrol")

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-lm-sensors"] = td


class TailorQemu:

    def __init__(self, add_items=[]):
        self._addItems = add_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-qemu" not in target_settings.pkg_use_files
        assert "10-tailor-qemu" not in target_settings.install_mask_files

        items = list(self._addItems)

        if "3dfx-patch" in items:
            target_settings.repo_postsync_patch_directories.append("qemu-add-3dfx-patch")
            target_settings.pkg_use_files["10-tailor-qemu"] = self._useFileContent.strip("\n") + "\n"
            target_settings.pkg_mask_files["10-tailor-qemu"] = self._maskFileContent.strip("\n") + "\n"
            items.remove("3dfx-patch")

        assert len(items) == 0

    _useFileContent = """
app-emulation/qemu          sdl sdl-image
"""

    _maskFileContent = """
<app-emulation/qemu-8.2.0
>=app-emulation/qemu-9.0.0
"""


class TailorPam:

    def __init__(self, remove_items=[]):
        self._removeItems = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-pam" not in target_settings.install_mask_files

        items = list(self._removeItems)
        td = {}

        if "pam_access" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*pam_access*",
                    "*access.conf*",
                ],
            })
            items.remove("pam_access")

        if "pam_group" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*group*",              # including /etc/security/group.conf
                ],
            })
            items.remove("pam_group")

        if "pam_limits" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*limits*",             # including /etc/security/limits.conf
                ],
                "media-video/pipewire": [
                    "/etc/security",        # remove /etc/security/limits.d/*
                ],
            })
            items.remove("pam_limits")

        if "pam_namespace" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*namespace*",
                ],
            })
            items.remove("pam_namespace")

        if "pam_pwhistory" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*pwhistory*",
                ],
            })
            items.remove("pam_pwhistory")

        if "pam_time" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*pam_time.*",
                    "*time.conf*",
                ],
            })
            items.remove("pam_time")

        if "pam_xauth" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "*xauth*",
                ],
            })
            items.remove("pam_xauth")

        if "pam_env_conf" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "/etc/security/pam_env.conf",
                    "/etc/environment",
                ],
                "sys-apps/systemd": [
                    "/usr/lib/environment.d/99-environment.conf",       # this symlink points to /etc/environment
                ],
            })
            items.remove("pam_env_conf")
        # FIXME: modify pam files, add conffile=/dev/null, envfile=/dev/null

        if "pam_faillock_conf" in items:
            _updateDict(td, {
                "sys-libs/pam": [
                    "/etc/security/faillock.conf",
                ],
            })
            items.remove("pam_faillock_conf")
        # FIXME: modify pam files, add conf=/dev/null

        # also remove the whole /etc/security directory if we can
        etcSecurityDirItem = [
            "pam_access",
            "pam_env_conf",
            "pam_faillock_conf",
            "pam_group",
            "pam_limits",
            "pam_namespace",
            "pam_pwhistory",
            "pam_time",
        ]
        if Util.listSparseContain(self._removeItems, etcSecurityDirItem):
            _updateDict(td, {
                "sys-libs/pam": [
                    "/etc/security",
                ],
            })

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-pam"] = td


class TailorUtilLinux:

    def __init__(self, remove_items=[]):
        self._removeItems = remove_items

    def update_target_settings(self, target_settings):
        assert "10-tailor-util-linux" not in target_settings.install_mask_files

        items = list(self._removeItems)
        td = {}

        if "runuser" in items:
            _updateDict(td, {
                "sys-apps/util-linux": [
                    "*runuser*",
                ],
            })
            items.remove("runuser")

        assert len(items) == 0
        if len(td) > 0:
            target_settings.install_mask_files["10-tailor-util-linux"] = td


def _updateDict(td, src):
    for k, v in src.items():
        if k not in td:
            td[k] = []
        td[k] += v
