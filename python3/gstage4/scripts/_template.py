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
import shutil
from .. import ScriptInChroot
from .._util import Util


class ScriptFromHostFile(ScriptInChroot):

    def __init__(self, script_filepath):
        assert script_filepath is not None

        self._filepath = script_filepath

    def fill_script_dir(self, script_dir_hostpath):
        os.copy(self._filepath, script_dir_hostpath)
        os.chmod(os.path.join(script_dir_hostpath, os.path.basename(self._filepath)), 0o0755)

    def get_script(self):
        return os.path.basename(self._filepath)


class ScriptFromHostDir(ScriptInChroot):

    def __init__(self, dirpath, script_filename):
        assert dirpath is not None
        assert "/" not in script_filename

        self._dirpath = dirpath
        self._filename = script_filename

    def fill_script_dir(self, script_dir_hostpath):
        Util.shellCall("cp %s/* %s" % (self._dirpath, script_dir_hostpath))
        Util.shellCall("find \"%s\" -type f | xargs chmod 644" % (script_dir_hostpath))
        Util.shellCall("find \"%s\" -type d | xargs chmod 755" % (script_dir_hostpath))

    def get_script(self):
        return self._filename


class ScriptFromBuffer(ScriptInChroot):

    def __init__(self, content_buffer):
        assert content_buffer is not None

        self._buf = content_buffer.strip("\n") + "\n"  # remove all redundant carrage returns

    def fill_script_dir(self, script_dir_hostpath):
        fullfn = os.path.join(script_dir_hostpath, _SCRIPT_FILE_NAME)
        with open(fullfn, "w") as f:
            f.write(self._buf)
        os.chmod(fullfn, 0o0755)

    def get_script(self):
        return _SCRIPT_FILE_NAME


class OneLinerScript(ScriptInChroot):

    def __init__(self, cmd, executor="/bin/sh"):
        assert cmd is not None

        self._cmd = cmd
        self._executor = executor

    def fill_script_dir(self, script_dir_hostpath):
        fullfn = os.path.join(script_dir_hostpath, _SCRIPT_FILE_NAME)
        with open(fullfn, "w") as f:
            f.write("#!%s\n" % (self._executor))
            f.write("%s\n" % (self._cmd))
        os.chmod(fullfn, 0o0755)

    def get_script(self):
        return _SCRIPT_FILE_NAME


class PlacingFilesScript(ScriptInChroot):

    def __init__(self):
        self._infoList = []

    def append_file(self, target_filepath, buf, owner=0, group=0, mode=0o644):
        assert target_filepath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= mode <= 0o777
        assert isinstance(buf, str) or isinstance(buf, bytes)

        self._infoList.append(("f", target_filepath, owner, group, mode, buf, None))

    def append_host_file(self, target_filepath, hostpath=None, owner=0, group=0, mode=0o644):
        assert target_filepath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= mode <= 0o777

        if hostpath is None:
            hostpath = target_filepath

        self._infoList.append(("f", target_filepath, owner, group, mode, None, hostpath))

    def append_dir(self, target_dirpath, owner=0, group=0, mode=0o755):
        assert target_dirpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= mode <= 0o777

        self._infoList.append(("d", target_dirpath, owner, group, mode, None, None))

    def append_host_dir(self, target_dirpath, hostpath=None, owner=0, group=0, dmode=0o755, fmode=0o644):
        assert target_dirpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= dmode <= 0o777
        assert 0o000 <= fmode <= 0o777

        if hostpath is None:
            hostpath = target_dirpath

        self._infoList.append(("d", target_dirpath, owner, group, dmode, fmode, hostpath))

    def append_symlink(self, target_linkpath, target, owner=0, group=0):
        assert target_linkpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert target is not None

        self._infoList.append(("s", target_linkpath, owner, group, target, None))

    def append_host_symlink(self, target_linkpath, hostpath=None, owner=0, group=0):
        assert target_linkpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)

        if hostpath is None:
            hostpath = target_linkpath

        self._infoList.append(("s", target_linkpath, owner, group, None, hostpath))

    def fill_script_dir(self, script_dir_hostpath):
        dataDir = os.path.join(script_dir_hostpath, "data")
        os.mkdir(dataDir)

        sbuf = self._scriptContent
        itemId = 1
        for info in self._infoList:
            if info[0] == "f":
                _, target_filepath, owner, group, mode, buf, hostpath = info
                fn, fullfn, itemId = self._fn(dataDir, itemId)
                if buf is not None:
                    assert hostpath is None
                    if isinstance(buf, str):
                        with open(fullfn, "w") as f:
                            f.write(buf)
                    elif isinstance(buf, bytes):
                        with open(fullfn, "wb") as f:
                            f.write(buf)
                    else:
                        assert False
                else:
                    assert hostpath is not None
                    shutil.copy(hostpath, fullfn)
                os.chown(fullfn, owner, group)
                os.chmod(fullfn, mode)
                sbuf += "mv %s %s\n" % (fn, target_filepath)
            elif info[0] == "d":
                _, target_dirpath, owner, group, dmode, fmode, hostpath = info
                fn, fullfn, itemId = self._fn(dataDir, itemId)
                if hostpath is not None:
                    assert fmode is not None
                    self._copytree(hostpath, fullfn, owner, group, dmode, fmode)
                    sbuf += "mv %s %s\n" % (fn, target_dirpath)
                else:
                    assert fmode is None
                    sbuf += "mkdir %s; chown %s:%s %s; chmod %o %s\n" % (target_dirpath, owner, group, target_dirpath, dmode, target_dirpath)
            elif info[0] == "s":
                _, target_linkpath, owner, group, target, hostpath = info
                if target is not None:
                    assert hostpath is None
                    sbuf += "ln -s %s %s; chown %s:%s %s\n" % (target, target_linkpath, owner, group, target_linkpath)
                else:
                    assert hostpath is not None
                    sbuf += "ln -s %s %s; chown %s:%s %s\n" % (os.readlink(hostpath), target_linkpath, owner, group, target_linkpath)
            else:
                assert False

        # create script file
        fullfn = os.path.join(script_dir_hostpath, _SCRIPT_FILE_NAME)
        with open(fullfn, "w") as f:
            f.write(self._scriptContent.strip("\n") + "\n")  # remove all redundant carrage returns
        os.chmod(fullfn, 0o0755)

    def get_script(self):
        return _SCRIPT_FILE_NAME

    def _fn(self, dataDir, itemId):
        fn = "item%d" % (itemId)
        fullfn = os.path.join(dataDir, fn)
        return (fn, fullfn, itemId + 1)

    def _copytree(self, src, dst, owner, group, dmode, fmode):
        os.mkdir(dst)
        os.chown(dst, owner, group)
        os.chmod(dst, dmode)
        for name in os.listdir(src):
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            if os.path.islink(srcname):
                os.symlink(os.readlink(srcname), dstname)
            elif os.path.isdir(srcname):
                self._copytree(srcname, dstname, owner, group, dmode, fmode)
            else:
                shutil.copy(srcname, dstname)
                os.chown(dstname, owner, group)
                os.chmod(dstname, fmode)

    _scriptContent = r"""
#!/bin/bash

DATA_DIR=$(dirname $(realpath $0))/data

# copy directories and files
cd $DATA_DIR
"""


_SCRIPT_FILE_NAME = "main.script"
