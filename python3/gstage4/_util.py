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
import re
import time
import shutil
import tempfile
import subprocess


class Util:

    @staticmethod
    def forceDelete(path):
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.lexists(path):
            os.remove(path)             # other type of file, such as device node
        else:
            pass                        # path does not exist, do nothing

    @staticmethod
    def pathCompare(path1, path2):
        # Change double slashes to slash
        path1 = re.sub(r"//", r"/", path1)
        path2 = re.sub(r"//", r"/", path2)
        # Removing ending slash
        path1 = re.sub("/$", "", path1)
        path2 = re.sub("/$", "", path2)

        if path1 == path2:
            return 1
        return 0

    @staticmethod
    def isMount(path):
        """Like os.path.ismount, but also support bind mounts"""
        if os.path.ismount(path):
            return 1
        a = os.popen("mount")
        mylines = a.readlines()
        a.close()
        for line in mylines:
            mysplit = line.split()
            if Util.pathCompare(path, mysplit[2]):
                return 1
        return 0

    @staticmethod
    def isInstanceList(obj, *instances):
        for inst in instances:
            if isinstance(obj, inst):
                return True
        return False

    @staticmethod
    def cmdCall(cmd, *kargs):
        # call command to execute backstage job
        #
        # scenario 1, process group receives SIGTERM, SIGINT and SIGHUP:
        #   * callee must auto-terminate, and cause no side-effect
        #   * caller must be terminated by signal, not by detecting child-process failure
        # scenario 2, caller receives SIGTERM, SIGINT, SIGHUP:
        #   * caller is terminated by signal, and NOT notify callee
        #   * callee must auto-terminate, and cause no side-effect, after caller is terminated
        # scenario 3, callee receives SIGTERM, SIGINT, SIGHUP:
        #   * caller detects child-process failure and do appopriate treatment

        ret = subprocess.run([cmd] + list(kargs),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             universal_newlines=True)
        if ret.returncode > 128:
            # for scenario 1, caller's signal handler has the oppotunity to get executed during sleep
            time.sleep(1.0)
        if ret.returncode != 0:
            print(ret.stdout)
            ret.check_returncode()
        return ret.stdout.rstrip()

    @staticmethod
    def shellCall(cmd):
        # call command with shell to execute backstage job
        # scenarios are the same as FmUtil.cmdCall

        ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             shell=True, universal_newlines=True)
        if ret.returncode > 128:
            # for scenario 1, caller's signal handler has the oppotunity to get executed during sleep
            time.sleep(1.0)
        if ret.returncode != 0:
            print(ret.stdout)
            ret.check_returncode()
        return ret.stdout.rstrip()

    @staticmethod
    def portageIsPkgInstalled(rootDir, pkg):
        dir = os.path.join(rootDir, "var", "db", "pkg", os.path.dirname(pkg))
        if os.path.exists(dir):
            for fn in os.listdir(dir):
                if fn.startswith(os.path.basename(pkg)):
                    return True
        return False


class TempChdir:

    def __init__(self, dirname):
        self.olddir = os.getcwd()
        os.chdir(dirname)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.olddir)


class TmpMount:

    def __init__(self, path, options=None):
        self._path = path
        self._tmppath = tempfile.mkdtemp()

        try:
            cmd = ["mount"]
            if options is not None:
                cmd.append("-o")
                cmd.append(options)
            cmd.append(self._path)
            cmd.append(self._tmppath)
            subprocess.run(cmd, check=True, universal_newlines=True)
        except BaseException:
            os.rmdir(self._tmppath)
            raise

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    @property
    def mountpoint(self):
        return self._tmppath

    def close(self):
        subprocess.run(["umount", self._tmppath], check=True, universal_newlines=True)
        os.rmdir(self._tmppath)
