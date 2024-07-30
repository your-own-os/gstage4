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
import glob
import shutil
import asyncio
import asyncio_pool
import subprocess
from ._util import TempChdir


class RepoPatcher:

    class WarnOrErr:

        def __init__(self, warnOrErr, msg):
            self.warn_or_err = warnOrErr
            self.msg = msg

    def __init__(self):
        self._jobNumber = 1
        self._warnOrErrList = []

    @property
    def warn_or_err_list(self):
        # this is a clumsy exception mechanism
        return self._warnOrErrList

    def filter_and_convert_patch_dir_list(self, patchDirList, targetDirRepoName):
        ret = []
        for patchDir in patchDirList:
            patchDir = os.path.join(patchDir, targetDirRepoName)
            if os.path.isdir(patchDir):
                ret.append(patchDir)
        return ret

    def patch(self, targetDir, patchDirList):
        pendingDstDirSet = set()
        for patchDir in patchDirList:
            pendingDstDirSet |= self._patchRepository(targetDir, patchDir)
        return pendingDstDirSet

    def generateManifest(self, targetDir, pendingDstDirSet):
        # generate manifest for patched packages
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self._doWork(targetDir, pendingDstDirSet, self._jobNumber))

    def _patchRepository(self, targetDir, patchDir):
        # patch eclass files
        eclassDir = os.path.join(patchDir, "eclass")
        if os.path.exists(eclassDir):
            dstFullDir = os.path.join(targetDir, "eclass")
            self._execPatchScript(patchDir, eclassDir, dstFullDir)

        # patch profile files
        profilesDir = os.path.join(patchDir, "profiles")
        if os.path.exists(profilesDir):
            dstFullDir = os.path.join(targetDir, "profiles")
            self._execPatchScript(patchDir, profilesDir, dstFullDir)

        # patch packages
        pendingDstDirList = []
        for categoryDir in os.listdir(patchDir):
            if categoryDir in ["README", "eclass", "profiles"]:
                continue
            fullCategoryDir = os.path.join(patchDir, categoryDir)
            for ebuildDir in os.listdir(fullCategoryDir):
                srcDir = os.path.join(fullCategoryDir, ebuildDir)
                dstDir = os.path.join(categoryDir, ebuildDir)
                dstFullDir = os.path.join(targetDir, dstDir)
                self._execPatchScript(patchDir, srcDir, dstFullDir)
                if len(glob.glob(os.path.join(dstFullDir, "*.ebuild"))) == 0:
                    # all ebuild files are deleted, it means this package is removed
                    shutil.rmtree(dstFullDir)
                    if len(os.listdir(fullCategoryDir)) == 0:
                        os.rmdir(fullCategoryDir)
                    continue
                pendingDstDirList.append(dstDir)

        return set(pendingDstDirList)

    def _execPatchScript(self, patchDir, srcDir, dstDir):
        patchTypeName = os.path.basename(patchDir)

        for fullfn in glob.glob(os.path.join(srcDir, "*")):
            if not os.path.isfile(fullfn):
                continue
            if not os.path.exists(dstDir):
                self._warnOrErrList.append(self.WarnOrErr(True, "patch %s script \"%s\" is outdated." % (patchTypeName, fullfn[len(patchDir) + 1:])))
                continue
            out = None
            with TempChdir(dstDir):
                if fullfn.endswith(".py"):
                    out = subprocess.check_output(["python3", fullfn], text=True)
                elif fullfn.endswith(".sh"):
                    out = subprocess.check_output(["sh", fullfn], text=True)
                else:
                    assert False
            if out == "outdated":
                self._warnOrErrList.append(self.WarnOrErr(True, "patch %s script \"%s\" is outdated." % (patchTypeName, fullfn[len(patchDir) + 1:])))
            elif out == "":
                pass
            else:
                self._warnOrErrList.append(self.WarnOrErr((False, "patch %s script \"%s\" exits with error \"%s\"." % (patchTypeName, fullfn[len(patchDir) + 1:], out))))

    @classmethod
    async def _doWork(cls, targetDir, pendingDstDirSet, jobNumber):
        # asyncio_pool.AioPool() needs a running event loop, so this function is needed, sucks
        if jobNumber is None:
            pool = asyncio_pool.AioPool()
        else:
            pool = asyncio_pool.AioPool(size=jobNumber)
        for dstDir in pendingDstDirSet:
            dstFullDir = os.path.join(targetDir, dstDir)
            pool.spawn_n(cls._generateEbuildManifest(dstFullDir))
        await pool.join()

    @staticmethod
    async def _generateEbuildManifest(ebuildDir):
        # operate on any ebuild file generates manifest for the whole ebuild directory
        fn = glob.glob(os.path.join(ebuildDir, "*.ebuild"))[0]
        args = ["ebuild", fn, "manifest"]
        proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL)
        retcode = await proc.wait()
        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, args)      # use subprocess.CalledProcessError since there's no equivalent in asyncio
