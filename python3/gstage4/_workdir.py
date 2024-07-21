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
import pathlib
from ._util import Util


class WorkDir:
    """
    This class manipulates gstage4's working directory.
    """

    def __init__(self, path, chroot_uid_map=None, chroot_gid_map=None, rollback=False):
        assert path is not None

        self._path = path
        Util.forceDelete(self._path)
        os.mkdir(self._path, mode=0o40700)

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

        self._rollback = rollback

        actionDirFullfnList = [x for x in [os.path.join(self._path, x) for x in os.listdir(self._path)] if os.path.isdir(x)]
        self._lastActionIndex = len(actionDirFullfnList) - 1
        if len(actionDirFullfnList) == 0:
            self._lastActionDirFullfn = None
        else:
            assert actionDirFullfnList[-1].startswith("%02d" % (self._lastActionIndex))
            self._lastActionDirFullfn = actionDirFullfnList[-1]

        self._finishFile = os.path.join(self._path, "builder-finished.save")

    @property
    def path(self):
        return self._path

    def has_uid_gid_map(self):
        return self._uidMap is not None

    def can_rollback(self):
        return self._rollback

    def is_finished(self):
        return self._readBuilderFinished() == ""

    def _newBuilderAction(self, action_index, action_name):
        assert action_index == self._lastActionIndex + 1

        fullfn = os.path.join(self._path, "%02d-%s" % (action_index, action_name))
        if self._lastActionIndex == -1:
            os.mkdir(fullfn)
        else:
            if self._rollback:
                subprocess.check_call(["cp", "-r", self._lastActionDirFullfn, fullfn])
            else:
                os.rename(self._lastActionDirFullfn, fullfn)
                os.mkdir(self._lastActionDirFullfn)

        self._lastActionIndex = action_index
        self._lastActionDirFullfn = fullfn

    def _readBuilderHistoryActions(self):
        ret = [x for x in os.listdir(self._path) if os.path.isdir(os.path.join(self._path, x))]
        ret.sort()
        ret = [re.fullmatch("[0-9]+-(.*)").group(1) for x in ret]
        return ret

    def _saveBuilderFinished(self, err):
        assert not os.path.exists(self._finishFile)
        with open(self._finishFile, "w") as f:
            f.write(err)

    def _readBuilderFinished(self):
        if os.path.exists(self._finishFile):
            return pathlib.Path(self._finishFile).read_text()
        else:
            return None

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
