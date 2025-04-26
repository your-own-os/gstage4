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
import asyncio
import asyncio_pool
import aiofiles.os
import aioshutil
import subprocess
from ._util import Util
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

        def __patchListCategoryDir(patchRepoDir):
            if os.path.exists(patchRepoDir):
                ret = os.listdir(patchRepoDir)
                ret = [(x, os.path.join(patchRepoDir, x)) for x in ret if x not in ["README", "eclass", "profiles", "_all_packages"]]
                return ret
            else:
                return []

        def __patchListEbuildDir(patchRepoCategoryDir):
            ret = os.listdir(patchRepoCategoryDir)
            ret = [(x, os.path.join(patchRepoCategoryDir, x)) for x in ret if x not in ["_all_packages"]]
            return ret

        asyncio.set_event_loop(asyncio.new_event_loop())

        for patchDir in patchDirList:
            patchTypeName = os.path.basename(patchDir)                  # /etc/portage/repo.postsync.d/10-patch-repository.d/use-wayland -> "use-wayland"
            patchRepoDir = os.path.join(patchDir, repoName)

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
            dstFullDirList = []
            for categoryDir, fullCategoryDir in __patchListCategoryDir(patchRepoDir):
                for ebuildDir, srcDir in __patchListEbuildDir(fullCategoryDir):
                    dstFullDirList.append(os.path.join(targetDir, categoryDir, ebuildDir))
            asyncio.get_event_loop().run_until_complete(self._doExecPatchScript(patchTypeName, patchRepoDir, srcDir, dstFullDirList, pendingDstDirSet))

            # patch all packages in specific categories
            dstFullDirList = []
            for categoryDir, fullCategoryDir in __patchListCategoryDir(patchRepoDir):
                fullAllDir = os.path.join(fullCategoryDir, "_all_packages")
                if os.path.exists(fullAllDir):
                    for dstEbuildDir, fullDstEbuildDir in Util.repoListEbuildDir(os.path.join(targetDir, categoryDir)):
                        dstFullDirList.append(fullDstEbuildDir)
            asyncio.get_event_loop().run_until_complete(self._doExecPatchScript(patchTypeName, patchRepoDir, fullAllDir, dstFullDirList, pendingDstDirSet))

            # patch all packages
            for fullAllDir in [os.path.join(patchRepoDir, "_all_packages"), os.path.join(patchDir, "_all_packages")]:
                if not os.path.exists(fullAllDir):
                    continue
                dstFullDirList = []
                for dstCategoryDir, fullDstCategoryDir in Util.repoListCategoryDir(targetDir):
                    for dstEbuildDir, fullDstEbuildDir in Util.repoListEbuildDir(fullDstCategoryDir):
                        dstFullDirList.append(fullDstEbuildDir)
                # note: srcBaseDir parameter of self._doExecPatchScript() is not ancestor of fullAllDir for item0 in this loop
                asyncio.get_event_loop().run_until_complete(self._doExecPatchScript(patchTypeName, patchRepoDir, fullAllDir, dstFullDirList, pendingDstDirSet))

        # patch can remove ebuild directories, so category directories can be empty either, remove them
        for dstCategoryDir, fullDstCategoryDir in Util.repoListCategoryDir(targetDir):
            if len(os.listdir(fullDstCategoryDir)) == 0:
                os.rmdir(fullDstCategoryDir)

        # some modified ebuild directories may be removed by later patches, so we need to check again before returning
        return [x for x in pendingDstDirSet if os.path.exists(x)]

    def generateManifest(self, pendingDstDirList):
        # generate manifest for patched packages
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(self._doGenerateEbuildManifest(pendingDstDirList))

    async def _doExecPatchScript(self, patchTypeName, srcBaseDir, srcDir, dstEbuildDirList, pendingDstEbuildDirSet):
        # asyncio_pool.AioPool() needs a running event loop, so this function is needed, sucks
        pool = asyncio_pool.AioPool(size=self._jobNumber)
        futList = []
        for dstEbuildDir in dstEbuildDirList:
            futList.append(pool.spawn_n(self._execPatchScript(patchTypeName, srcBaseDir, srcDir, dstEbuildDir)))
        await pool.join()
        for i, dstEbuildDir in enumerate(dstEbuildDirList):
            if futList[i].result():
                pendingDstEbuildDirSet.add(dstEbuildDir)

    async def _execPatchScript(self, patchTypeName, srcBaseDir, srcDir, dstEbuildDir):
        assert os.path.isabs(srcBaseDir)
        assert os.path.isabs(srcDir)

        modifiedDict = {}
        for fullfn in glob.glob(os.path.join(dstEbuildDir, "*.ebuild")):
            modifiedDict[fullfn] = await aiofiles.os.path.getmtime(fullfn)
        assert len(modifiedDict) > 0

        with TempChdir(dstEbuildDir):
            for fullfn in glob.glob(os.path.join(srcDir, "*")):
                if not await aiofiles.os.path.isfile(fullfn):
                    continue

                if fullfn.endswith(".py"):
                    args = ["python3", fullfn]
                elif fullfn.endswith(".sh"):
                    args = ["sh", fullfn]
                else:
                    assert False

                proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE)
                out, _ = await proc.communicate()
                if proc.returncode != 0:
                    raise subprocess.CalledProcessError(proc.returncode, args)      # use subprocess.CalledProcessError since there's no equivalent in asyncio

                out = out.decode()
                if out == "outdated\n":
                    self._warnOrErrList.append(self.WarnOrErr(True, "patch %s script \"%s\" is outdated." % (patchTypeName, os.path.relpath(fullfn, srcBaseDir))))
                elif out == "":
                    pass
                else:
                    self._warnOrErrList.append(self.WarnOrErr(False, "patch %s script \"%s\" exits with error \"%s\"." % (patchTypeName, os.path.relpath(fullfn, srcBaseDir), out)))

        fullfnList = glob.glob(os.path.join(dstEbuildDir, "*.ebuild"))
        if len(fullfnList) == 0:
            # all ebuild files are deleted, it means this package is removed, no need to regenerate manifest file
            await aioshutil.rmtree(dstEbuildDir)
            return False
        elif len(modifiedDict) != len(fullfnList):
            # some ebuild files are deleted or added, need to regenerate manifest file
            return True
        else:
            # need to regenerate manifest file if any ebuild file is modified
            for fullfn, mtimeOld in modifiedDict.items():
                if not await aiofiles.os.path.exists(fullfn) or await aiofiles.os.path.getmtime(fullfn) != mtimeOld:
                    return True
            return False

    async def _doGenerateEbuildManifest(self, pendingDstDirList):
        # asyncio_pool.AioPool() needs a running event loop, so this function is needed, sucks
        pool = asyncio_pool.AioPool(size=self._jobNumber)
        for dstDir in pendingDstDirList:
            pool.spawn_n(self._generateEbuildManifest(dstDir))
        await pool.join()

    @staticmethod
    async def _generateEbuildManifest(ebuildDir):
        # operating on any ebuild file is enough to generate manifest for the whole ebuild directory
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
