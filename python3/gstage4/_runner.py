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
import robust_layer.simple_fops
from ._util import Util


class Runner:

    def __init__(self, chroot_dir_path):
        self._dir = chroot_dir_path
        self._mountList = []
        self._scriptDirList = []

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, type, value, traceback):
        self.unbind()

    def is_binded(self):
        return len(self._mountList) > 0

    def bind(self):
        assert len(self._mountList) == 0

        try:
            # copy resolv.conf
            # FIMXE: can not adapt the network cfg of host system change
            subprocess.check_call(["cp", "-L", "/etc/resolv.conf", os.path.join(self._dir, "etc")])

            # mount /proc
            fullfn = os.path.join(self._dir, "proc")
            assert os.path.exists(fullfn) and not Util.isMount(fullfn)
            subprocess.check_call(["mount", "-t", "proc", "proc", fullfn])
            self._mountList.append(fullfn)

            # mount /sys
            fullfn = os.path.join(self._dir, "sys")
            assert os.path.exists(fullfn) and not Util.isMount(fullfn)
            subprocess.check_call(["mount", "--rbind", "/sys", fullfn])
            subprocess.check_call(["mount", "--make-rslave", fullfn])
            self._mountList.append(fullfn)

            # mount /dev
            fullfn = os.path.join(self._dir, "dev")
            assert os.path.exists(fullfn) and not Util.isMount(fullfn)
            subprocess.check_call(["mount", "--rbind", "/dev", fullfn])
            subprocess.check_call(["mount", "--make-rslave", fullfn])
            self._mountList.append(fullfn)

            # FIXME: mount /run
            pass

            # mount /tmp
            fullfn = os.path.join(self._dir, "tmp")
            assert os.path.exists(fullfn) and not Util.isMount(fullfn)
            subprocess.check_call(["mount", "-t", "tmpfs", "tmpfs", fullfn])
            self._mountList.append(fullfn)
        except BaseException:
            self._unbind(False)
            raise

    def unbind(self, remove_scripts=True):
        assert len(self._mountList) > 0
        self._unbind(bool(remove_scripts))

    def interactive_shell(self):
        assert len(self._mountList) > 0
        subprocess.check_call(["chroot", self._dir])

    def shell_call(self, env, cmd):
        # "CLEAN_DELAY=0 emerge -C sys-fs/eudev" -> "CLEAN_DELAY=0 chroot emerge -C sys-fs/eudev"
        assert len(self._mountList) > 0

        # FIXME
        env = "LANG=C.utf8 PATH=/bin:/usr/bin:/sbin:/usr/sbin " + env
        assert self._detectArch() == platform.machine()

        subprocess.check_output("%s chroot \"%s\" %s" % (env, self._dir, cmd), shell=True, stderr=subprocess.STDOUT)

    def shell_exec(self, env, cmd, quiet=False):
        assert len(self._mountList) > 0

        # FIXME
        env = "LANG=C.utf8 PATH=/bin:/usr/bin:/sbin:/usr/sbin " + env
        assert self._detectArch() == platform.machine()

        if not quiet:
            subprocess.check_call("%s chroot \"%s\" %s" % (env, self._dir, cmd), shell=True)
        else:
            subprocess.check_output("%s chroot \"%s\" %s" % (env, self._dir, cmd), shell=True, stderr=subprocess.STDOUT)

    def script_exec(self, scriptObj, quiet=False):
        assert len(self._mountList) > 0

        path = os.path.join("/var", "tmp", "script_%d" % (len(self._scriptDirList)))
        hostPath = os.path.join(self._dir, path[1:])

        assert not os.path.exists(hostPath)
        os.makedirs(hostPath, mode=0o755)
        self._scriptDirList.append(hostPath)

        scriptObj.fill_script_dir(hostPath)
        self.shell_exec("", "sh -c \"cd %s ; ./%s\"" % (path, scriptObj.get_script()), quiet)

    def _unbind(self, remove_scripts):
        assert isinstance(remove_scripts, bool)

        for fullfn in reversed(self._mountList):
            if os.path.exists(fullfn) and Util.isMount(fullfn):
                subprocess.check_call(["umount", "-l", fullfn])
        self._mountList = []

        robust_layer.simple_fops.rm(os.path.join(self._dir, "etc", "resolv.conf"))

        if remove_scripts:
            for hostPath in reversed(self._scriptDirList):
                robust_layer.simple_fops.rm(hostPath)
        self._scriptDirList = []

    def _detectArch(self):
        # FIXME: use profile function of pkgwh to get arch from CHOST
        return "x86_64"
