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
from ._util import ActionRunner


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

        self._persistentStorage = WorkDirPersisentStorage(self._path)

    @property
    def path(self):
        return self._path

    def has_uid_gid_map(self):
        return self._uidMap is not None

    def is_build_finished(self):
        self._persistentStorage.isFinished()

    def has_error(self):
        actionName, _ = self._persistentStorage.getCurrentActionInfo()
        if actionName is not None:
            return True
        return False

    def get_error_message(self):
        actionName, err = self._persistentStorage.getCurrentActionInfo()
        if actionName is not None:
            return "action %s failed (%s) for \"%s\"" % (actionName, err, self._path)
        assert False

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


class WorkDirPersisentStorage(ActionRunner.PersistStorage, ActionRunner.PersistStorageWithFinishedFlagFile):

    def __init__(self, path):
        super(ActionRunner.PersistStorageWithFinishedFlagFile, self).__init__(os.path.join(path, "builder-finished.flag"))

        self._path = path
        self._errFile = os.path.join(self._path, "error.save")
        self._runFlag = False      # FIXME: should be changed to a lock

    def getCurrentActionInfo(self):
        oldDir, _, oldActionName = self._getLastActionDirIndexName()
        if oldDir is not None:
            if os.path.exists(self._errFile):
                assert not self.__runFlag
                return (oldActionName, pathlib.Path(self._errFile).read_text())
            elif not self.__runFlag:
                return (oldActionName, "crashed")
            else:
                return (oldActionName, None)     # action is running
        else:
            return (None, None)

    def getHistoryActions(self):
        ret = []
        for fn in os.listdir(self.__path).sort():
            m = re.fullmatch("[0-9]+-(.*)", fn)
            ret.append(m.group(1))
        return ret

    def saveActionStart(self, actionName):
        assert not os.path.exists(self._errFile)
        oldDir, oldIndex, _ = self._getLastActionDirIndexName()
        if oldDir is None:
            os.mkdir("00-" + actionName)
        else:
            os.rename(oldDir, "%d-%s" % (oldIndex + 1, actionName))
            os.mkdir(oldDir)
        self._runFlag = True

    def saveActionEnd(self, error=None):
        assert not os.path.exists(self._errFile)
        if error is not None:
            with open(self._errFile, "w") as f:
                f.write(error + "\n")
        self._runFlag = False

    def saveNewHistoryAction(self, actionName):
        assert actionName == self._getLastActionDirIndexName()[2]

    def _getLastActionDirIndexName(self):
        fnList = os.listdir(self.__path).sort()
        if len(fnList) == 0:
            return (None, None, None)
        else:
            m = re.fullmatch("([0-9])+-(.*)", fnList[-1])
            return (m.group(0), int(m.group(1)), m.group(2))
