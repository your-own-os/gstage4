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
import stat
import robust_layer.simple_fops
from ._errors import WorkDirError


class WorkDir:
    """
    This class manipulates gstage4's working directory.
    """

    def __init__(self, path, chroot_uid_map=None, chroot_gid_map=None):
        assert path is not None

        self._MODE = 0o40700
        self._CURRENT = "cur"

        self._path = path
        if not os.path.exists(self._path):
            os.mkdir(self._path, mode=self._MODE)
        else:
            self._verifyDir(True)
            robust_layer.simple_fops.truncate_dir(self._path)

        if chroot_uid_map is None:
            self._uidMap = None
        else:
            assert chroot_uid_map[0] == os.getuid()
            self._uidMap = chroot_uid_map

        if chroot_gid_map is None:
            assert self._uidMap is None
            self._gidMap = None
        else:
            assert self._uidMap is not None
            assert chroot_gid_map[0] == os.getgid()
            self._gidMap = chroot_gid_map

    @property
    def path(self):
        return self._path

    def has_uid_gid_map(self):
        return self._uidMap is not None

    # @property
    # def chroot_uid_map(self):
    #     assert self._uidMap is not None
    #     return self._uidMap

    # @property
    # def chroot_gid_map(self):
    #     assert self._gidMap is not None
    #     return self._gidMap

    # def chroot_conv_uid(self, uid):
    #     if self._uidMap is None:
    #         return uid
    #     else:
    #         if uid not in self._uidMap:
    #             raise SettingsError("uid %d not found in uid map" % (uid))
    #         else:
    #             return self._uidMap[uid]

    # def chroot_conv_gid(self, gid):
    #     if self._gidMap is None:
    #         return gid
    #     else:
    #         if gid not in self._gidMap:
    #             raise SettingsError("gid %d not found in gid map" % (gid))
    #         else:
    #             return self._gidMap[gid]

    # def chroot_conv_uid_gid(self, uid, gid):
    #     return (self.chroot_conv_uid(uid), self.chroot_conv_gid(gid))

    def _verifyDir(self, raiseException):
        # work directory can be a directory or directory symlink
        # so here we use os.stat() instead of os.lstat()
        s = os.stat(self._path)
        if not stat.S_ISDIR(s.st_mode):
            if raiseException:
                raise WorkDirError("\"%s\" is not a directory" % (self._path))
            else:
                return False
        if s.st_mode != self._MODE:
            print("%o" % (s.st_mode))
            if raiseException:
                raise WorkDirError("invalid mode for \"%s\"" % (self._path))
            else:
                return False
        if s.st_uid != os.getuid():
            if raiseException:
                raise WorkDirError("invalid uid for \"%s\"" % (self._path))
            else:
                return False
        if s.st_gid != os.getgid():
            if raiseException:
                raise WorkDirError("invalid gid for \"%s\"" % (self._path))
            else:
                return False
        return True
