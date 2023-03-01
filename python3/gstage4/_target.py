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


import re
from ._errors import SettingsError


class TargetSettings:

    def __init__(self):
        self.profile = None

        self.package_manager = "portage"              # "portage"
        self.kernel_manager = "none"                  # "none", "genkernel", "binary-kernel", "fake"
        self.service_manager = "none"                 # "none", "openrc", "systemd"

        self.pkg_use = dict()                         # dict<package-wildcard, use-flag-list>
        self.pkg_mask = []                            # list<package-wildcard>
        self.pkg_unmask = []                          # list<package-wildcard>
        self.pkg_accept_keywords = dict()             # dict<package-wildcard, accept-keyword-list>
        self.pkg_license = dict()                     # dict<package-wildcard, license-list>
        self.use_mask = []                            # list<use-flag>

        self.pkg_use_files = dict()                   # dict<file-name, file-content>
        self.pkg_mask_files = dict()                  # dict<file-name, file-content>
        self.pkg_unmask_files = dict()                # dict<file-name, file-content>
        self.pkg_accept_keywords_files = dict()       # dict<file-name, file-content>
        self.pkg_license_files = dict()               # dict<file-name, file-content>

        self.install_mask = []                        # dict<package-wildcard, list<install-mask>>
        self.install_mask_files = dict()              # dict<file-name, dict<package-wildcard, list<install-mask>>>

        self.repo_postsync_scripts = dict()           # dict<file-name, file-content>
        self.repo_postsync_patch_directories = []     # list<patch-directory>

        self.build_opts = TargetSettingsBuildOpts("build_opts")
        self.build_opts.ccache = False

        self.kern_build_opts = TargetSettingsBuildOpts("kern_build_opts")

        self.pkg_build_opts = dict()

    @classmethod
    def check_object(cls, obj, raise_exception=None):
        assert raise_exception is not None

        def __checkFilenames(filenames, name):
            for fn in filenames:
                if re.fullmatch(r'[0-8][0-9]-\S+', fn) is None:
                    raise SettingsError("invalid filename \"%s\" for %s" % (fn, name))

        try:
            if not isinstance(obj, cls):
                raise SettingsError("invalid object type")

            if obj.profile is not None and not isinstance(obj.profile, str):
                raise SettingsError("invalid value for \"profile\"")

            # if obj.package_manager not in ["portage", "pkgcore", "pkgwh"]:
            if obj.package_manager not in ["portage"]:
                raise SettingsError("invalid value of \"package_manager\"")

            # if obj.kernel_manager not in ["none", "genkernel", "binary-kernel", "fake"]:
            if obj.kernel_manager not in ["none", "genkernel", "binary-kernel", "fake"]:
                raise SettingsError("invalid value of \"kernel_manager\"")

            if obj.service_manager not in ["none", "openrc", "systemd"]:
                raise SettingsError("invalid value of \"service_manager\"")

            if obj.pkg_use is None or not isinstance(obj.pkg_use, dict):
                raise SettingsError("invalid value for \"pkg_use\"")
            if obj.pkg_mask is None or not isinstance(obj.pkg_mask, list):
                raise SettingsError("invalid value for \"pkg_mask\"")
            if obj.pkg_unmask is None or not isinstance(obj.pkg_unmask, list):
                raise SettingsError("invalid value for \"pkg_unmask\"")
            if obj.pkg_accept_keywords is None or not isinstance(obj.pkg_accept_keywords, dict):
                raise SettingsError("invalid value for \"pkg_accept_keywords\"")
            if obj.pkg_license is None or not isinstance(obj.pkg_license, dict):
                raise SettingsError("invalid value for \"pkg_license\"")
            if obj.use_mask is None or not isinstance(obj.use_mask, list):
                raise SettingsError("invalid value for \"use_mask\"")

            if not isinstance(obj.pkg_use_files, dict):
                raise SettingsError("invalid value for \"pkg_use_files\"")
            __checkFilenames(obj.pkg_use_files.keys(), "pkg_use_files")

            if not isinstance(obj.pkg_mask_files, dict):
                raise SettingsError("invalid value for \"pkg_mask_files\"")
            __checkFilenames(obj.pkg_mask_files.keys(), "pkg_mask_files")

            if not isinstance(obj.pkg_unmask_files, dict):
                raise SettingsError("invalid value for \"pkg_unmask_files\"")
            __checkFilenames(obj.pkg_unmask_files.keys(), "pkg_unmask_files")

            if not isinstance(obj.pkg_accept_keywords_files, dict):
                raise SettingsError("invalid value for \"pkg_accept_keywords_files\"")
            __checkFilenames(obj.pkg_accept_keywords_files.keys(), "pkg_accept_keywords_files")

            if not isinstance(obj.pkg_license_files, dict):
                raise SettingsError("invalid value for \"pkg_license_files\"")
            __checkFilenames(obj.pkg_license_files.keys(), "pkg_license_files")

            if obj.install_mask is None or not isinstance(obj.install_mask, dict):
                raise SettingsError("invalid value for \"install_mask\"")
            if obj.install_mask_files is None or not isinstance(obj.install_mask_files, dict):
                raise SettingsError("invalid value for \"install_mask_files\"")
            __checkFilenames(obj.install_mask_files.keys(), "install_mask_files")

            if obj.repo_postsync_scripts is None or not isinstance(obj.repo_postsync_scripts, dict):
                raise SettingsError("invalid value for \"repo_postsync_scripts\"")
            if obj.repo_postsync_patch_directories is None or not isinstance(obj.repo_postsync_patch_directories, list):
                raise SettingsError("invalid value for \"repo_postsync_patch_directories\"")
            __checkFilenames(obj.repo_postsync_scripts.keys(), "repo_postsync_scripts")

            if obj.build_opts is None or not TargetSettingsBuildOpts.check_object(obj.build_opts, raise_exception=raise_exception):
                raise SettingsError("invalid value for \"build_opts\"")
            if obj.build_opts.ccache is None:
                raise SettingsError("invalid value for key \"ccache\" in \"build_opts\"")

            if obj.kern_build_opts is None or not TargetSettingsBuildOpts.check_object(obj.kern_build_opts, raise_exception=raise_exception):
                raise SettingsError("invalid value for \"kern_build_opts\"")
            if obj.kern_build_opts.ccache is not None:
                raise SettingsError("invalid value for key \"ccache\" in \"kern_build_opts\"")  # FIXME: currrently ccache is only allowed in global build options

            if obj.pkg_build_opts is None or not isinstance(obj.pkg_build_opts, dict):
                raise SettingsError("invalid value for \"pkg_build_opts\"")
            for k, v in obj.pkg_build_opts.items():
                if v is None or not TargetSettingsBuildOpts.check_object(v, raise_exception=raise_exception):
                    raise SettingsError("invalid value for \"build_opts\" of package %s" % (k))
                if v.ccache is not None:
                    raise SettingsError("invalid value for key \"ccache\" in build_opts of package %s" % (k))  # FIXME: currrently ccache is only allowed in global build options

            return True
        except SettingsError:
            if raise_exception:
                raise
            else:
                return False


class TargetSettingsBuildOpts:

    def __init__(self, name):
        self.name = name

        self.common_flags = []
        self.cflags = []
        self.cxxflags = []
        self.fcflags = []
        self.fflags = []
        self.ldflags = []
        self.asflags = []

        self.ccache = None

    @classmethod
    def check_object(cls, obj, raise_exception=None):
        assert raise_exception is not None

        if not isinstance(obj, cls):
            if raise_exception:
                raise SettingsError("invalid object type")
            else:
                return False

        if obj.common_flags is None or not isinstance(obj.common_flags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"common_flags\" of %s" % (obj.name))
            else:
                return False

        if obj.cflags is None or not isinstance(obj.cflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"cflags\" of %s" % (obj.name))
            else:
                return False

        if obj.cxxflags is None or not isinstance(obj.cxxflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"cxxflags\" of %s" % (obj.name))
            else:
                return False

        if obj.fcflags is None or not isinstance(obj.fcflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"fcflags\" of %s" % (obj.name))
            else:
                return False

        if obj.fflags is None or not isinstance(obj.fflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"fflags\" of %s" % (obj.name))
            else:
                return False

        if obj.ldflags is None or not isinstance(obj.ldflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"ldflags\" of %s" % (obj.name))
            else:
                return False

        if obj.asflags is None or not isinstance(obj.asflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"asflags\" of %s" % (obj.name))
            else:
                return False

        if obj.ccache is not None and not isinstance(obj.ccache, bool):
            if raise_exception:
                raise SettingsError("invalid value for \"ccache\" of %s" % (obj.name))
            else:
                return False

        return True
