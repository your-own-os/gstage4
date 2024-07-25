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
import stat
import pathlib
from ._util import Util
from ._util import ActionRunner
from ._errors import WorkDirError


class WorkDir:
    """
    This class manipulates gstage4's working directory.
    """

    def __init__(self, path, chroot_uid_map=None, chroot_gid_map=None, reset=False):
        assert path is not None

        self._MODE = 0o40700

        self._path = path

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

        self._tsFile = os.path.join(self._path, "target-settings.save")

        self._persistentStorage = WorkDirPersisentStorage(self)

        if not os.path.exists(self._path):
            os.mkdir(self._path, mode=self._MODE)
        else:
            # work directory can be a directory or directory symlink
            # so here we use os.stat() instead of os.lstat()
            s = os.stat(self._path)
            if not stat.S_ISDIR(s.st_mode):
                raise WorkDirError("\"%s\" is not a directory" % (self._path))
            if s.st_mode != self._MODE:
                raise WorkDirError("invalid mode for \"%s\"" % (self._path))
            if s.st_uid != os.getuid():
                raise WorkDirError("invalid uid for \"%s\"" % (self._path))
            if s.st_gid != os.getgid():
                raise WorkDirError("invalid gid for \"%s\"" % (self._path))

            # clear directory content if needed
            if reset:
                Util.removeDirContentExclude(self._path, [])

    @property
    def path(self):
        return self._path

    def get_latest_action_dirpath(self):
        # can return None
        return self.getLastActionDirIndexName()[0]

    def has_error(self):
        assert not self._persistentStorage.isInUse()
        _, err = self._persistentStorage.initGetCurrentActionInfo()
        return err is not None

    def get_error_message(self):
        assert not self._persistentStorage.isInUse()
        actionName, err = self._persistentStorage.initGetCurrentActionInfo()
        return "action %s failed (%s) for \"%s\"" % (actionName, err, self._path)

    def has_uid_gid_map(self):
        return self._uidMap is not None

    def get_arch(self):
        return pathlib.Path(self._tsFile).read_text().rstrip("\n")

    def is_build_finished(self):
        self._persistentStorage.isFinished()

    def _saveTargetSettings(self, ts):
        with open(self._tsFile, "w") as f:
            f.write(ts.arch + "\n")

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


class WorkDirPersisentStorage(ActionRunner.PersistStorage):

    def __init__(self, parent):
        self._parent = parent
        self._errFile = os.path.join(self._parent.path, "error.save")
        self._finishFile = os.path.join(self._parent.path, "finished.flag")
        self._inUse = False

    def initGetCurrentActionInfo(self):
        actionDir, _, actionName = self.getLastActionDirIndexName()

        error = None
        try:
            error = pathlib.Path(self._errFile).read_text().rstrip("\n")
        except FileNotFoundError:
            pass

        if actionName is not None:
            if error == "":
                error = "crashed"

        return (actionName, error)

    def getLastActionDirIndexName(self):
        fnList = os.listdir(self._parent.path).sort()
        if len(fnList) == 0:
            return (None, None, None)
        else:
            m = re.fullmatch("([0-9])+-(.*)", fnList[-1])
            return (m.group(0), int(m.group(1)), m.group(2))

    def getHistoryActionNames(self):
        ret = []
        for fn in os.listdir(self._parent.path).sort():
            m = re.fullmatch("[0-9]+-(.*)", fn)
            ret.append(m.group(1))
        return ret

    def isFinished(self):
        return os.path.exists(self._finishFile)

    def isInUse(self):
        return self._inUse

    def use(self):
        assert not self._inUse
        self._inUse = True

    def saveActionStart(self, actionName):
        assert self._inUse
        assert not os.path.exists(self._errFile)

        oldActionDir, oldActionIndex, _ = self.getLastActionDirIndexName()
        if oldActionDir is None:
            os.mkdir("00-" + actionName)
        else:
            os.rename(oldActionDir, "%d-%s" % (oldActionIndex + 1, actionName))
            os.mkdir(oldActionDir)

        with open(self._errFile, "w") as f:
            f.write("")

    def saveActionEnd(self, error=None):
        assert self._inUse
        assert os.path.exists(self._errFile)

        if error is None:
            os.unlink(self._errFile)
        else:
            with open(self._errFile, "w") as f:
                f.write(error + "\n")

    def saveFinished(self):
        assert self._inUse
        assert not os.path.exists(self._finishFile)
        with open(self._finishFile, "w") as f:
            f.write("")

    def unUse(self):
        assert self._inUse
        self._inUse = False
