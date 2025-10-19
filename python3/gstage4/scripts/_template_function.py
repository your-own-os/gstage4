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
from .._prototype import FunctionInChroot


class CreateFileFunction(FunctionInChroot):

    def __init__(self, target_filepath, buf, owner=0, group=0, mode=0o644):
        assert target_filepath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= mode <= 0o777
        assert isinstance(buf, str) or isinstance(buf, bytes)

        self._info = (target_filepath, owner, group, mode, buf)

    def execute(self, chroot_dir_hostpath):
        target_filepath, owner, group, mode, buf = self._info
        fullfn = os.path.join(chroot_dir_hostpath, target_filepath[1:])

        if isinstance(buf, str):
            with open(fullfn, "w") as f:
                f.write(buf)
        elif isinstance(buf, bytes):
            with open(fullfn, "wb") as f:
                f.write(buf)
        else:
            assert False
        os.chown(fullfn, owner, group)
        os.chmod(fullfn, mode)


class CopyHostFileFunction(FunctionInChroot):
    def __init__(self, target_filepath, hostpath, owner=0, group=0, mode=0o644):
        assert target_filepath.startswith("/")
        assert hostpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= mode <= 0o777

        self._info = (target_filepath, owner, group, mode, hostpath)

    def execute(self, chroot_dir_hostpath):
        target_filepath, owner, group, mode, hostpath = self._info
        fullfn = os.path.join(chroot_dir_hostpath, target_filepath[1:])

        shutil.copy(hostpath, fullfn)
        os.chown(fullfn, owner, group)
        os.chmod(fullfn, mode)


class CreateDirFunction(FunctionInChroot):

    def __init__(self, target_dirpath, owner=0, group=0, mode=0o755):
        assert target_dirpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= mode <= 0o777

        self._info = (target_dirpath, owner, group, mode)

    def execute(self, chroot_dir_hostpath):
        target_dirpath, owner, group, mode = self._info
        fullfn = os.path.join(chroot_dir_hostpath, target_dirpath[1:])

        os.mkdir(fullfn)
        os.chown(fullfn, owner, group)
        os.chmod(fullfn, mode)


class CopyHostDirFunction(FunctionInChroot):

    def __init__(self, target_dirpath, hostpath, owner=0, group=0, dmode=0o755, fmode=0o644):
        assert target_dirpath.startswith("/")
        assert hostpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)
        assert 0o000 <= dmode <= 0o777
        assert 0o000 <= fmode <= 0o777

        self._info = (target_dirpath, owner, group, dmode, fmode, hostpath)

    def execute(self, chroot_dir_hostpath):
        target_dirpath, owner, group, dmode, fmode, hostpath = self._info
        fullfn = os.path.join(chroot_dir_hostpath, target_dirpath[1:])
        self._copytree(hostpath, fullfn, owner, group, dmode, fmode)

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


class CreateSymlinkFunction(FunctionInChroot):
    def __init__(self, target_linkpath, target, owner=0, group=0):
        assert target_linkpath.startswith("/")
        assert target.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)

        self._info = (target_linkpath, target, owner, group)

    def execute(self, chroot_dir_hostpath):
        target_linkpath, target, owner, group = self._info
        fullfn = os.path.join(chroot_dir_hostpath, target_linkpath[1:])

        os.symlink(target, fullfn)
        os.chown(fullfn, owner, group)


class CopyHostSymlinkFunction(FunctionInChroot):
    def __init__(self, target_linkpath, hostpath, owner=0, group=0):
        assert target_linkpath.startswith("/")
        assert hostpath.startswith("/")
        assert isinstance(owner, int)
        assert isinstance(group, int)

        self._info = (target_linkpath, hostpath, owner, group)

    def execute(self, chroot_dir_hostpath):
        target_linkpath, hostpath, owner, group = self._info
        fullfn = os.path.join(chroot_dir_hostpath, target_linkpath[1:])

        target = os.readlink(hostpath)
        os.symlink(target, fullfn)
        os.chown(fullfn, owner, group)
