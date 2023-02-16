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
import pathlib


class UseSystemd:

    def __init__(self, module_flags={}):
        self._selfDir = os.path.dirname(os.path.realpath(__file__))
        self._mFlagDict = module_flags

    def update_target_settings(self, target_settings):
        assert "10-systemd" not in target_settings.pkg_use_files
        assert "10-systemd" not in target_settings.pkg_mask_files
        assert "10-systemd" not in target_settings.install_mask_files

        target_settings.service_manager = "systemd"

        if True:
            fn = os.path.join(self._selfDir, "package.use")
            target_settings.pkg_use_files["10-systemd"] = pathlib.Path(fn).read_text()

        if True:
            fn = os.path.join(self._selfDir, "package.mask")
            target_settings.pkg_mask_files["10-systemd"] = pathlib.Path(fn).read_text()

        if True:
            td = {}
            flagRecord = set()

            def _updateDict(src):
                for k, v in src.items():
                    if k not in td:
                        td[k] = v
                    td[k] += v

            def _flagExec(flag_name, disable_func=None, exclude_func=None):
                ret = self._mFlagDict.get(flag_name, None)
                if ret is None:
                    pass
                elif ret == "disable":
                    if disable_func is not None:
                        disable_func()
                    else:
                        assert False
                elif ret == "exclude":
                    if exclude_func is not None:
                        exclude_func()
                    else:
                        assert False
                else:
                    assert False
                if True:
                    assert flag_name not in flagRecord
                    flagRecord.add(flag_name)

            _flagExec("systemd-boot", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*bootctl*",
                    "*/systemd-boot.7.bz2",
                    "*systemd-boot-system-token*",
                ],
            }))
            _flagExec("systemd-coredump", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*coredump*",
                ],
            }))
            _flagExec("systemd-hostnamed", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*hostname1*",
                    "*hostnamed*",
                    "*hostnamectl*",
                ],
            }))
            _flagExec("systemd-firstboot", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*firstboot*",
                ],
            }))
            _flagExec("systemd-kexec", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*kexec*",
                ],
            }))
            _flagExec("systemd-localed", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*locale1*",
                    "*localed*",
                    "*localectl*",
                ],
            }))
            _flagExec("systemd-machined", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*machine*",
                    "*nspawn*",
                    "*detect-virt*",
                    "*exit.target",
                    "*systemd-exit.service",
                ],
            }))
            _flagExec("systemd-networkd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*network*",
                    "/lib/systemd/network*",
                    "/etc/systemd/network",
                ],
            }))
            _flagExec("systemd-portabled", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*portable*",
                    "/lib/systemd/portable",
                ],
            }))
            _flagExec("systemd-oomd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*oom1*",
                    "*oomd*",
                    "*oomctl",
                ],
            }))
            _flagExec("systemd-pstore", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*pstore*",
                ],
            }))
            _flagExec("systemd-repart", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*repart*",
                ],
            }))
            _flagExec("systemd-resolvd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*resolv*",
                ],
            }))
            _flagExec("systemd-sysext", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*sysext*",
                ],
            }))
            _flagExec("systemd-sysupdate", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*sysupdate*",
                ],
            }))
            _flagExec("systemd-sysusers", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*systemd-sysusers*",
                ],
            }))
            _flagExec("systemd-timedated", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*timedate*",
                ],
            }))
            _flagExec("systemd-timesyncd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*timesync*",
                    "*ntp*",
                    "/lib/systemd/ntp-units.d*",
                ],
            }))
            _flagExec("systemd-update", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*system-update*",
                    "*update-done*",
                ],
            }))
            _flagExec("systemd-userdbd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*userdb*",
                ],
            }))
            _flagExec("fstab", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*fstab*",
                ],
            }))
            _flagExec("fs-operations", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*makefs*",
                    "*growfs*",
                    "*mkswap*",
                ],
            }))
            _flagExec("ldconfig.service", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*ldconfig*",
                ],
            }))
            _flagExec("sysvinit", exclude_func=lambda: _updateDict({
                "*/*": [
                    "/etc/init.d",
                    "/etc/conf.d",
                    "/etc/rc.d",
                ],
                "sys-apps/systemd": [
                    "*initctl*",
                    "*runlevel*",
                    "*systemd-sysv-generator*",
                    "*rc-local*",
                ],
            }))
            assert len(set(self._mFlagDict.keys()) - flagRecord) == 0
            if len(td) > 0:
                target_settings.install_mask_files["10-systemd"] = td

    def update_world_set(self, world_set):
        world_set.add("sys-apps/systemd")
