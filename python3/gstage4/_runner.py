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
import platform
import subprocess
from ._util import Util
from ._util import DirListMount


class Runner:

    def __init__(self, chroot_dir_path):
        self._dir = chroot_dir_path
        self._mountObj = None
        self._scriptDirList = []

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, type, value, traceback):
        self.unbind()

    def is_binded(self):
        return self._mountObj is not None

    def bind(self):
        assert not self.is_binded()

        try:
            # mount layer 1 directories
            if True:
                procDir = os.path.join(self._dir, "proc")
                sysDir = os.path.join(self._dir, "sys")
                devDir = os.path.join(self._dir, "dev")
                runDir = os.path.join(self._dir, "run")
                runDevDir = os.path.join(self._dir, "run", "udev")
                tmpDir = os.path.join(self._dir, "tmp")

                assert os.path.exists(procDir) and not Util.isMount(procDir)
                assert os.path.exists(sysDir) and not Util.isMount(sysDir)
                assert os.path.exists(devDir) and not Util.isMount(devDir)
                assert os.path.exists(runDir) and not Util.isMount(runDir)
                assert os.path.exists(tmpDir) and not Util.isMount(tmpDir)

                mountDirs = [
                    (procDir, "-t proc -o nosuid,noexec,nodev proc %s" % (procDir)),
                    (sysDir, "--rbind /sys %s" % (sysDir), "--make-rslave %s" % (sysDir)),
                    (devDir, "--rbind /dev %s" % (devDir), "--make-rslave %s" % (devDir)),
                    (runDir, "-t tmpfs tmpfs %s" % (runDir)),
                    (runDevDir, "--rbind /run/udev %s" % (runDevDir), "--make-rslave %s" % (runDevDir)),
                    (tmpDir, "-t tmpfs -o mode=1777,strictatime,nodev,nosuid tmpfs %s" % (tmpDir)),
                ]
                # if os.path.exists("/sys/firmware/efi/efivars"):
                #     mountList += [
                #         ("/mnt/gentoo/sys/firmware/efi/efivars", "-t efivarfs -o nosuid,noexec,nodev /mnt/gentoo/sys/firmware/efi/efivars"),
                #     ]

                self._mountObj = DirListMount(mountDirs)

            # copy resolv.conf
            # FIMXE: can not adapt the network cfg of host system change
            targetFullfn = os.path.join(self._dir, "etc", "resolv.conf")
            if os.path.exists(targetFullfn):
                os.rename(targetFullfn, targetFullfn + ".bak")
            subprocess.check_call(["cp", "-L", "/etc/resolv.conf", targetFullfn])
        except BaseException:
            self.unbind(remove_scripts=False)
            raise

    def unbind(self, remove_scripts=True):
        if remove_scripts:
            for i in range(0, len(self._scriptDirList)):
                Util.forceDelete(self._scriptDirList.pop())

        targetFullfn = os.path.join(self._dir, "etc", "resolv.conf")
        if os.path.exists(targetFullfn + ".bak"):
            os.rename(targetFullfn + ".bak", targetFullfn)
        else:
            Util.forceDelete(targetFullfn)

        if self._mountObj is not None:
            self._mountObj.dispose()
            self._mountObj = None

    def shell_call(self, env, cmd):
        # "CLEAN_DELAY=0 emerge -C sys-fs/eudev" -> "CLEAN_DELAY=0 chroot emerge -C sys-fs/eudev"
        assert self.is_binded()

        # FIXME
        env = "LANG=C.utf8 PATH=/bin:/usr/bin:/sbin:/usr/sbin " + env
        assert self._detectArch() == platform.machine()

        return subprocess.check_output("%s chroot \"%s\" %s" % (env, self._dir, cmd), shell=True, stderr=subprocess.STDOUT, universal_newlines=True)

    def shell_exec(self, env, cmd, quiet=False):
        assert self.is_binded()

        # FIXME
        env = "LANG=C.utf8 PATH=/bin:/usr/bin:/sbin:/usr/sbin " + env
        assert self._detectArch() == platform.machine()

        if quiet:
            subprocess.check_call("%s chroot \"%s\" %s" % (env, self._dir, cmd), shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.check_call("%s chroot \"%s\" %s" % (env, self._dir, cmd), shell=True)

    def script_exec(self, scriptObj, quiet=False):
        assert self.is_binded()

        path = os.path.join("/var", "tmp", "script_%d" % (len(self._scriptDirList)))
        hostPath = os.path.join(self._dir, path[1:])

        assert not os.path.exists(hostPath)
        os.makedirs(hostPath, mode=0o755)
        self._scriptDirList.append(hostPath)

        scriptObj.fill_script_dir(hostPath)
        self.shell_exec("", "sh -c \"cd %s ; ./%s\"" % (path, scriptObj.get_script()), quiet)

    def _detectArch(self):
        # FIXME: use profile function of pkgwh to get arch from CHOST
        return "x86_64"
