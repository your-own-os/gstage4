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
import multiprocessing
from ._errors import SettingsError


class Settings:

    def __init__(self):
        self.program_name = None

        self.log_dir = None

        self.verbose_level = 1

        # computing power
        self.host_cpu_core_count = None
        self.host_memory_size = None               # in byte
        self.host_cooling_level = None             # 1-10, less is weaker

        # repo.postsync.d patch directory in host system
        self.host_repo_postsync_patch_source_dir = None

        # distfiles directory in host system, will be bind mounted in target system
        self.host_distfiles_dir = None

        # packages directory in host system
        self.host_packages_dir = None

        # ccache directory in host system
        self.host_ccache_dir = None

    def auto_fill_computing_power(self):
        # cpu_core_count
        self.host_cpu_core_count = multiprocessing.cpu_count()

        # memory_size
        with open("/proc/meminfo", "r") as f:
            # Since the memory size shown in /proc/meminfo is always a
            # little less than the real size because various sort of
            # reservation, so we do a "+1GB"
            m = re.search("^MemTotal:\\s+(\\d+)", f.read())
            self.host_memory_size = (int(m.group(1)) // 1024 // 1024 + 1) * 1024 * 1024

        # cooling_level
        self.host_cooling_level = 5

    @classmethod
    def check_object(cls, obj, raise_exception=None):
        assert raise_exception is not None

        if not isinstance(obj, cls):
            if raise_exception:
                raise SettingsError("invalid object type")
            else:
                return False

        if not isinstance(obj.program_name, str):
            if raise_exception:
                raise SettingsError("invalid value for key \"program_name\"")
            else:
                return False

        if obj.log_dir is not None and not isinstance(obj.log_dir, str):
            if raise_exception:
                raise SettingsError("invalid value for key \"log_dir\"")
            else:
                return False

        if not (0 <= obj.verbose_level <= 2):
            if raise_exception:
                raise SettingsError("invalid value for key \"verbose_level\"")
            else:
                return False

        if obj.host_cpu_core_count <= 0:
            if raise_exception:
                raise SettingsError("invalid value of \"host_cpu_core_count\"")
            else:
                return False

        if obj.host_memory_size <= 0:
            if raise_exception:
                raise SettingsError("invalid value of \"host_memory_size\"")
            else:
                return False

        if not (1 <= obj.host_cooling_level <= 10):
            if raise_exception:
                raise SettingsError("invalid value of \"host_cooling_level\"")
            else:
                return False

        if obj.host_repo_postsync_patch_source_dir is not None and not os.path.isdir(obj.host_repo_postsync_patch_source_dir):
            if raise_exception:
                raise SettingsError("invalid value for key \"host_repo_postsync_patch_source_dir\"")
            else:
                return False

        if obj.host_distfiles_dir is not None and not os.path.isdir(obj.host_distfiles_dir):
            if raise_exception:
                raise SettingsError("invalid value for key \"host_distfiles_dir\"")
            else:
                return False

        if obj.host_packages_dir is not None and not os.path.isdir(obj.host_packages_dir):
            if raise_exception:
                raise SettingsError("invalid value for key \"host_packages_dir\"")
            else:
                return False

        if obj.host_ccache_dir is not None and not os.path.isdir(obj.host_ccache_dir):
            if raise_exception:
                raise SettingsError("invalid value for key \"host_ccache_dir\"")
            else:
                return False

        return True


class TargetSettings:

    def __init__(self):
        self.arch = None
        self.profile = None

        self.package_manager = "portage"              # "portage"
        self.kernel_manager = "none"                  # "none", "genkernel", "distkernel"
        self.service_manager = "none"                 # "none", "openrc", "systemd"

        self.pkg_use = dict()                         # dict<package-wildcard, use-flag-list>
        self.pkg_mask = []                            # list<package-wildcard>
        self.pkg_unmask = []                          # list<package-wildcard>
        self.pkg_accept_keywords = dict()             # dict<package-wildcard, accept-keyword-list>
        self.pkg_license = dict()                     # dict<package-wildcard, license-list>

        self.pkg_use_files = dict()                   # dict<file-name, file-content>
        self.pkg_mask_files = dict()                  # dict<file-name, file-content>
        self.pkg_unmask_files = dict()                # dict<file-name, file-content>
        self.pkg_accept_keywords_files = dict()       # dict<file-name, file-content>
        self.pkg_license_files = dict()               # dict<file-name, file-content>

        self.install_mask = dict()                    # dict<package-wildcard, list<install-mask>>
        self.install_mask_files = dict()              # dict<file-name, dict<package-wildcard, list<install-mask>>>

        self.repo_postsync_patch_directories = []     # list<patch-directory>

        self.fetch_command = None                     # tuple(fetch-command, resume-command)
        self.git_fetch_command = None                 # tuple(clone-command, pull-command)

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

            if obj.arch not in ["alpha", "amd64", "arm", "arm64", "hppa", "ia64", "m68k", "mips", "ppc", "riscv", "s390", "sh", "sparc", "x86"]:
                raise SettingsError("invalid value for \"arch\"")

            if obj.profile is not None and not isinstance(obj.profile, str):
                raise SettingsError("invalid value for \"profile\"")

            # if obj.package_manager not in ["portage", "pkgcore", "pkgwh"]:
            if obj.package_manager not in ["portage"]:
                raise SettingsError("invalid value of \"package_manager\"")

            if obj.kernel_manager not in ["none", "genkernel", "distkernel"]:
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

            if obj.repo_postsync_patch_directories is None or not isinstance(obj.repo_postsync_patch_directories, list):
                raise SettingsError("invalid value for \"repo_postsync_patch_directories\"")

            if obj.fetch_command is not None and (not isinstance(obj.fetch_command, tuple) or len(obj.fetch_command) != 2):
                raise SettingsError("invalid value for \"fetch_command\"")

            if obj.git_fetch_command is not None and (not isinstance(obj.git_fetch_command, tuple) or len(obj.git_fetch_command) != 2):
                raise SettingsError("invalid value for \"git_fetch_command\"")

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

    @staticmethod
    def _getPackagesForKernelManager(kernel_manager, **kwargs):
        if kernel_manager == "genkernel":
            return [
                "sys-kernel/gentoo-sources",
                "sys-kernel/genkernel",
                "sys-devel/bc",           # kernel build script needs it
            ]

        if kernel_manager == "distkernel":
            ret = [
                "sys-kernel/gentoo-kernel-bin",
                "sys-kernel/dracut",
                "app-portage/gentoolkit",
            ]

            if kwargs["dracutArgs"] is not None and re.search(r"\B-a dmsquash-live\b", kwargs["dracutArgs"]) is not None:
                # FIXME: what package does it need?
                pass

            if kwargs["dracutArgs"] is not None and re.search(r"\B-a mdraid\b", kwargs["dracutArgs"]) is not None:
                ret.append("sys-fs/mdadm")

            if kwargs["dracutArgs"] is not None and re.search(r"\B-i /lib/keymaps /lib/keymaps\b", kwargs["dracutArgs"]) is not None:
                ret.append("app-misc/livecd-tools")

            if kwargs["dracutArgs"] is not None and re.search(r"\B-I busybox\b", kwargs["dracutArgs"]) is not None:
                ret.append("sys-apps/busybox")

            return ret

        assert False


class TargetSettingsBuildOpts:

    def __init__(self, name):
        self.name = name

        self.common_flags = None      # can be None or like ["-O2", "-pipe"], None means no common flags
        self.cflags = None            # same as above, None means using default value in profile
        self.cxxflags = None          # same as above
        self.fcflags = None           # same as above
        self.fflags = None            # same as above
        self.ldflags = None           # same as above
        self.asflags = None           # same as above

        self.ccache = None

    @classmethod
    def check_object(cls, obj, raise_exception=None):
        assert raise_exception is not None

        if not isinstance(obj, cls):
            if raise_exception:
                raise SettingsError("invalid object type")
            else:
                return False

        if obj.common_flags is not None and not isinstance(obj.common_flags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"common_flags\" of %s" % (obj.name))
            else:
                return False

        if obj.cflags is not None and not isinstance(obj.cflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"cflags\" of %s" % (obj.name))
            else:
                return False

        if obj.cxxflags is not None and not isinstance(obj.cxxflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"cxxflags\" of %s" % (obj.name))
            else:
                return False

        if obj.fcflags is not None and not isinstance(obj.fcflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"fcflags\" of %s" % (obj.name))
            else:
                return False

        if obj.fflags is not None and not isinstance(obj.fflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"fflags\" of %s" % (obj.name))
            else:
                return False

        if obj.ldflags is not None and not isinstance(obj.ldflags, list):
            if raise_exception:
                raise SettingsError("invalid value for \"ldflags\" of %s" % (obj.name))
            else:
                return False

        if obj.asflags is not None and not isinstance(obj.asflags, list):
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
