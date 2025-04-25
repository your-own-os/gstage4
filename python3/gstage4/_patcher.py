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

    def __init__(self, settings=None, jobNumber=None, loadAverage=None):
        if settings is not None:
            assert jobNumber is None and loadAverage is None
            if settings.host_cooling_level <= 1:
                jobNumber = 1
                loadAverage = 1
            else:
                jobNumber = settings.host_cpu_core_count + 2
                loadAverage = settings.host_cpu_core_count
        else:
            assert jobNumber is not None

        self._jobNumber = jobNumber
        self._loadAverage = loadAverage
        self._warnOrErrList = []

    @property
    def warn_or_err_list(self):
        # this is a clumsy exception mechanism
        return self._warnOrErrList

    def filter_patch_dir_list(self, patchDirList, targetDirRepoName):
        ret = []
        for patchDir in patchDirList:
            if os.path.isdir(os.path.join(patchDir, "_all_packages")) or os.path.isdir(os.path.join(patchDir, targetDirRepoName)):
                ret.append(patchDir)
        return ret

    def patch(self, targetDir, patchDirList, repoName):
        pendingDstDirSet = set()
        for patchDir in patchDirList:
            pendingDstDirSet |= self._patchRepository(targetDir, patchDir, repoName)
        return pendingDstDirSet

    def generateManifest(self, pendingDstDirSet):
        # generate manifest for patched packages
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self._doWork(pendingDstDirSet))

    def _patchRepository(self, targetDir, patchDir, repoName):
        patchTypeName = os.path.basename(patchDir)                  # /etc/portage/repo.postsync.d/10-patch-repository.d/use-wayland -> "use-wayland"
        patchRepoDir = os.path.join(patchDir, repoName)
        pendingDstDirSet = set()

        # patch eclass files
        eclassDir = os.path.join(patchRepoDir, "eclass")
        if os.path.exists(eclassDir):
            dstFullDir = os.path.join(targetDir, "eclass")
            self._execPatchScript(patchTypeName, patchRepoDir, eclassDir, dstFullDir)

        # patch profile files
        profilesDir = os.path.join(patchRepoDir, "profiles")
        if os.path.exists(profilesDir):
            dstFullDir = os.path.join(targetDir, "profiles")
            self._execPatchScript(patchTypeName, patchRepoDir, profilesDir, dstFullDir)

        # patch specific packages
        if os.path.exists(patchRepoDir):
            for categoryDir in os.listdir(patchRepoDir):
                if categoryDir in ["README", "eclass", "profiles", "_all_packages"]:
                    continue
                fullCategoryDir = os.path.join(patchRepoDir, categoryDir)
                for ebuildDir in os.listdir(fullCategoryDir):
                    if ebuildDir in ["_all_packages"]:
                        continue
                    srcDir = os.path.join(fullCategoryDir, ebuildDir)
                    dstDir = os.path.join(categoryDir, ebuildDir)
                    dstFullDir = os.path.join(targetDir, dstDir)
                    if self._execPatchScript(patchTypeName, patchRepoDir, srcDir, dstFullDir):
                        pendingDstDirSet.add(dstDir)

        # patch all packages in specific categories
        if os.path.exists(patchRepoDir):
            for categoryDir in os.listdir(patchRepoDir):
                if categoryDir in ["README", "eclass", "profiles", "_all_packages"]:
                    continue
                fullAllDir = os.path.join(patchRepoDir, categoryDir, "_all_packages")
                if os.path.exists(fullAllDir):
                    fullDstCategoryDir = os.path.join(targetDir, categoryDir)
                    for dstEbuildDir in os.listdir(fullDstCategoryDir):
                        fullDstEbuildDir = os.path.join(fullDstCategoryDir, dstEbuildDir)
                        if os.path.isdir(fullDstEbuildDir):
                            if self._execPatchScript(patchTypeName, patchRepoDir, fullAllDir, fullDstEbuildDir):
                                pendingDstDirSet.add(fullDstEbuildDir)

        # patch all packages
        for fullAllDir in [os.path.join(patchRepoDir, "_all_packages"), os.path.join(patchDir, "_all_packages")]:
            if os.path.exists(fullAllDir):
                for dstCategoryDir in os.listdir(targetDir):
                    fullDstCategoryDir = os.path.join(targetDir, dstCategoryDir)
                    if os.path.isdir(fullDstCategoryDir) and (dstCategoryDir == "virtual" or "-" in dstCategoryDir):
                        for dstEbuildDir in os.listdir(fullDstCategoryDir):
                            fullDstEbuildDir = os.path.join(fullDstCategoryDir, dstEbuildDir)
                            if os.path.isdir(fullDstEbuildDir):
                                if self._execPatchScript(patchTypeName, patchRepoDir, fullAllDir, fullDstEbuildDir):        # note: srcBaseDir is not ancestor of fullAllDir for item0 in this loop
                                    pendingDstDirSet.add(fullDstEbuildDir)

        # patch can remove ebuild directories, so category directories can be empty either, remove them
        for dstCategoryDir in os.listdir(targetDir):
            fullDstCategoryDir = os.path.join(targetDir, dstCategoryDir)
            if os.path.isdir(fullDstCategoryDir) and (dstCategoryDir == "virtual" or "-" in dstCategoryDir):
                if len(os.listdir(fullDstCategoryDir)) == 0:
                    os.rmdir(fullDstCategoryDir)

        return pendingDstDirSet

    def _execPatchScript(self, patchTypeName, srcBaseDir, srcDir, dstEbuildDir):
        assert os.path.isabs(srcBaseDir)
        assert os.path.isabs(srcDir)

        modifiedDict = {}
        for fullfn in glob.glob(os.path.join(dstEbuildDir, "*.ebuild")):
            modifiedDict[fullfn] = os.path.getmtime(fullfn)
        assert len(modifiedDict) > 0

        with TempChdir(dstEbuildDir):
            for fullfn in glob.glob(os.path.join(srcDir, "*")):
                if not os.path.isfile(fullfn):
                    continue

                out = None
                if fullfn.endswith(".py"):
                    out = subprocess.check_output(["python3", fullfn], text=True)
                elif fullfn.endswith(".sh"):
                    out = subprocess.check_output(["sh", fullfn], text=True)
                else:
                    assert False

                if out == "outdated":
                    self._warnOrErrList.append(self.WarnOrErr(True, "patch %s script \"%s\" is outdated." % (patchTypeName, os.path.relpath(fullfn, srcBaseDir))))
                elif out == "":
                    pass
                else:
                    self._warnOrErrList.append(self.WarnOrErr((False, "patch %s script \"%s\" exits with error \"%s\"." % (patchTypeName, os.path.relpath(fullfn, srcBaseDir), out))))

        fullfnList = glob.glob(os.path.join(dstEbuildDir, "*.ebuild"))
        if len(modifiedDict) != len(fullfnList):
            return True
        elif len(fullfnList) == 0:
            # all ebuild files are deleted, it means this package is removed
            shutil.rmtree(dstEbuildDir)
            return False
        else:
            for fullfn, mtimeOld in modifiedDict.items():
                if not os.path.exists(fullfn) or os.path.getmtime(fullfn) != mtimeOld:
                    return True
            return False

    @classmethod
    async def _doWork(self, pendingDstDirSet, jobNumber):
        # asyncio_pool.AioPool() needs a running event loop, so this function is needed, sucks
        pool = asyncio_pool.AioPool(size=self._jobNumber)
        for dstDir in pendingDstDirSet:
            pool.spawn_n(self._generateEbuildManifest(dstDir))
        await pool.join()

    @staticmethod
    async def _generateEbuildManifest(ebuildDir):
        # operate on any ebuild file generates manifest for the whole ebuild directory
        try:
            fn = glob.glob(os.path.join(ebuildDir, "*.ebuild"))[0]
        except IndexError:
            print(ebuildDir)
            raise
        args = ["ebuild", fn, "manifest"]
        proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.DEVNULL)
        retcode = await proc.wait()
        if retcode != 0:
            raise subprocess.CalledProcessError(retcode, args)      # use subprocess.CalledProcessError since there's no equivalent in asyncio
