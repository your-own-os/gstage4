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
import shlex
import pathlib
import subprocess
from ._util import Util
from ._util import DirListMount
from ._prototype import ScriptInChroot
from ._errors import WorkDirError
from .scripts import ScriptFromBuffer


class Runner:

    def __init__(self, arch, chroot_dir_path):
        self._arch = arch
        self._dir = chroot_dir_path
        self._mountObj = None
        self._scriptDirList = []

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.unbind(remove_scripts=(exc_type is None))

    def is_binded(self):
        return self._mountObj is not None

    def bind(self):
        assert not self.is_binded()

        try:
            # clear tmp files (we should simulate the boot process)
            Util.removeDirContentExclude(os.path.join(self._dir, "run"), [])
            Util.removeDirContentExclude(os.path.join(self._dir, "tmp"), [])
            Util.removeDirContentExclude(os.path.join(self._dir, "var", "tmp"), [])

            # mount directories
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
                (runDir, "-t tmpfs -o nosuid,nodev,mode=755,size=32m none %s" % (runDir)),
                (runDevDir, "--rbind /run/udev %s" % (runDevDir), "--make-rslave %s" % (runDevDir)),
                (tmpDir, "-t tmpfs -o nosuid,nodev,strictatime,mode=1777 tmpfs %s" % (tmpDir)),
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
            if os.path.exists("/etc/resolv.conf"):
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

    def shell(self, env):
        assert self.is_binded()
        assert Util.isArchCompatible(self._arch, Util.getCpuArch())
        assert isinstance(env, str)

        self._shellExec(env, None, False, False)

    def shell_call(self, env, cmd):
        assert self.is_binded()
        assert Util.isArchCompatible(self._arch, Util.getCpuArch())
        assert isinstance(env, str) and isinstance(cmd, str)

        self._shellExec(env, cmd, False, True)

    def shell_exec(self, env, cmd, quiet=False):
        assert self.is_binded()
        assert Util.isArchCompatible(self._arch, Util.getCpuArch())
        assert isinstance(env, str) and isinstance(cmd, str)

        self._shellExec(env, cmd, quiet, False)

    def script_exec(self, env, script_obj, quiet=False):
        assert self.is_binded()
        assert Util.isArchCompatible(self._arch, Util.getCpuArch())
        assert isinstance(env, str) and isinstance(script_obj, ScriptInChroot)

        hostPath, scriptDir, scriptName = self._addScript(script_obj)
        self._shellExec(env, "cd %s ; ./%s" % (scriptDir, scriptName), quiet, False)

    def _addScript(self, scriptObj):
        scriptDir = os.path.join("/var", "tmp", "script_%d" % (len(self._scriptDirList)))
        hostPath = os.path.join(self._dir, scriptDir[1:])
        self._scriptDirList.append(hostPath)

        assert not os.path.exists(hostPath)
        os.makedirs(hostPath, mode=0o755)
        scriptObj.fill_script_dir(hostPath)

        return (hostPath, scriptDir, scriptObj.get_script_filename())

    def _shellExec(self, env, cmd, bQuiet, bNeedOutput):
        scriptObj = ScriptChrootInit(Util.getTermType(), Util.getLangEncoding(), cmd)
        hostPath, scriptDir, scriptName = self._addScript(scriptObj)

        cmdList = ["chroot", self._dir]
        if env != "":
            # env should be set in /bin/sh process, not in chroot process itself
            # this affects nothing, but it should be like this
            cmdList += shlex.split("/bin/env %s" % (env))
        if True:
            # let /bin/sh executes a predefined script that do some checks
            # chroot would be terminated if check fails
            # failure message would be returned through error.log file in script directory
            cmdList += ["/bin/sh", "-l", "-c", "cd %s ; ./%s" % (scriptDir, scriptName)]

        # we must use an empty environment except some specific environment variables
        envDict = {}
        for k, v in os.environ.items():
            if k == "TERM":
                envDict[k] = self._processTermInfo(v)
                continue

        # do work
        try:
            if bNeedOutput:
                assert not bQuiet
                return subprocess.check_output(cmdList, stderr=subprocess.STDOUT, text=True, env=envDict)
            else:
                if bQuiet:
                    subprocess.check_call(cmdList, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=envDict)
                else:
                    subprocess.check_call(cmdList, env=envDict)
                return None
        except subprocess.CalledProcessError:
            errFn = os.path.join(hostPath, "error.log")
            if os.path.exists(errFn):
                raise WorkDirError(pathlib.Path(errFn).read_text())
            else:
                raise
        finally:
            self._cleanupTermInfo()

    def _processTermInfo(self, termType):
        # FIXME: terminfo file should be put in /etc
        if not Util.hasTermInfoFile(termType, self._dir):
            Util.copyTermInfoFile(termType, "/", self._dir)
        return termType

    def _cleanupTermInfo(self):
        # FIXME: should remove terminfo file in /etc
        pass


class ScriptChrootInit(ScriptFromBuffer):

    def __init__(self, termType, languageEncoding, cmd):
        buf = self._scriptTemplate

        if termType is not None:
            buf += self._scriptTemplateCheckTermType.replace("@@termType@@", termType)

        if languageEncoding is not None:
            buf += self._scriptTemplateCheckLanguageEncoding.replace("@@languageEncoding@@", languageEncoding)

        if cmd is None:
            buf += self._scriptTemplateShell
        else:
            buf += self._scriptTemplateExec.replace("@@cmd@@", cmd)

        super().__init__(buf)

    _scriptTemplate = """
#!/bin/sh

die() {
    echo -n "$1" > ./error.log
    exit 1
}
"""

    _scriptTemplateCheckTermType = """
if [ -n "$TERM" ]; then
    if [ "$TERM" != "@@termType@@" ] ; then
        die "stage4 uses another terminal type (TERM=$TERM)"
    fi
fi
"""

    _scriptTemplateCheckLanguageEncoding = r"""
if [ -z "$LANG" ]; then
    die "stage4 does not have LANG environment variable"
fi

get_encoding() {
    if [[ "$1" =~ \.([^ ]*) ]] ; then
        echo "${BASH_REMATCH[1]}"
    fi
}
for var in LANG $(env | grep -oP '^LC_\w+'); do
    value=$(printenv $var)
    if [ -n "$value" ] ; then
        enc=$(get_encoding $value)
        shopt -s nocasematch
        if [[ "$enc" != "@@languageEncoding@@" ]]; then
            die "stage4 language encoding differs from current: ($var=$value vs @@languageEncoding@@)"
        fi
        shopt -u nocasematch
    fi
done
"""

    _scriptTemplateShell = """
userinfo=$(grep "^[^:]*:[^:]*:$(id -u):" /etc/passwd | cut -d: -f1,7)
usershell=$(echo "$userinfo" | cut -d: -f2)
if [ -z "$usershell" ] ; then
    username=$(echo "$userinfo" | cut -d: -f1)
    die "stage4 has no shell for user \"$username\""
fi

cd /
exec $usershell
"""

    _scriptTemplateExec = """
exec sh -c "@@cmd@@"
"""
