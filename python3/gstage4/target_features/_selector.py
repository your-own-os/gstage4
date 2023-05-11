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

class SetTargetUseFlagsBase:

    class SelectOnlyLatestVersion:
        pass

    class FilterByStableVersion:
        def __init__(self, select_newer_versions=False):
            self._equalAndAbove = select_newer_versions

    class FilterByUserSelection:
        def __init__(self, select_newer_versions=False):
            self._equalAndAbove = select_newer_versions

    class FilterByGentooRepository:
        pass

    class FilterByOverlays:
        def __init__(self, overlay_list):
            self._overlayList = overlay_list

    class FilterByPackages:
        def __init__(self, package_list):
            self._packageList = package_list


class SetPythonTargetUseFlags(SetTargetUseFlagsBase):
    pass

    # def __init__(self, name, filters, getDefaultTargetsUseFlag, cmpTargetsUseFlag, checkMainPackageOfTargetUseFlag):
    #     self._name = name
    #     self._filters = filters
    #     self._usefn = os.path.join(FmConst.portageCfgUseDir, "10-%s-targets" % (name))
    #     self._getDefaultTargetsUseFlag = getDefaultTargetsUseFlag
    #     self._cmpTargetsUseFlag = cmpTargetsUseFlag
    #     self._checkMainPackageOfTargetUseFlag = checkMainPackageOfTargetUseFlag

    # def update_target_settings(self, target_settings):
    #     assert self._usefn not in target_settings.pkg_use_files

    #     # default use flag
    #     defaultUse = self._getDefaultTargetsUseFlag()
    #     if defaultUse is None:
    #         if checkOrRefresh:
    #             if os.path.exists(usefn):
    #                 raise Exception("\"%s\" should not exist" % (usefn))
    #         else:
    #             robust_layer.simple_fops.rm(usefn)
    #     else:
    #         ret, mainPackage = self._checkMainPackageOfTargetUseFlag(defaultUse)
    #         if not ret:
    #             raise Exception("main package \"%s\" for USE flag \"%s\" is masked" % (mainPackage, defaultUse))

    #         fnContent = ""
    #         fnContent += "# default version\n"
    #         fnContent += "*/* %s\n" % (defaultUse)

    #         # use flag of higher versions
    #         if True:
    #             useSet = set()
    #             if True:
    #                 for repoName in self.repoman.getRepositoryList():
    #                     repoDir = self.repoman.getRepoDir(repoName)
    #                     fn = os.path.join(repoDir, "profiles", "desc", "%s_targets.desc" % (name))
    #                     if os.path.exists(fn):
    #                         useSet |= set(self.__getTargetsUseFlagList(fn))
    #                 for overlayName in self.layman.getOverlayList():
    #                     fn = os.path.join(self.layman.getOverlayDir(overlayName), "profiles", "desc", "%s_targets.desc" % (name))
    #                     if os.path.exists(fn):
    #                         useSet |= set(self.__getTargetsUseFlagList(fn))
    #             fnContent += "\n"
    #             fnContent += "# higher versions\n"
    #             if True:
    #                 line = ""
    #                 for u in sorted(list(useSet)):
    #                     if not checkMainPackageOfTargetUseFlag(u)[0]:
    #                         continue
    #                     if cmpTargetsUseFlag(useSet, u, defaultUse) <= 0:
    #                         continue
    #                     line += " " + u
    #                 if line != "":
    #                     fnContent += "*/*%s\n" % (line)
    #                 else:
    #                     fnContent += "\n"

    #         # operate configuration file
    #         if checkOrRefresh:
    #             if not os.path.exists(usefn):
    #                 raise Exception("\"%s\" does not exist" % (usefn))
    #             with open(usefn, "r") as f:
    #                 if fnContent != f.read():
    #                     raise Exception("\"%s\" has invalid content" % (usefn))
    #         else:
    #             with open(usefn, "w") as f:
    #                 f.write(fnContent)


class SetRubyTargetUseFlags(SetTargetUseFlagsBase):

    class SelectOnlyLatestVersion:
        pass

    class FilterByStableVersion:
        def __init__(self, select_newer_versions=False):
            self._equalAndAbove = select_newer_versions

    class FilterByUserSelection:
        def __init__(self, select_newer_versions=False):
            self._equalAndAbove = select_newer_versions

    class FilterByGentooRepository:
        pass

    class FilterByOverlays:
        def __init__(self, overlay_list):
            self._overlayList = overlay_list

    class FilterByPackages:
        def __init__(self, package_list):
            self._packageList = package_list

    def __init__(self):
        pass
