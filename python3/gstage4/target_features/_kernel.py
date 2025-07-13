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


from .._settings import TargetSettings


class UseGenkernel:

    def __init__(self, kernel_config=None, check_kernel_config_version=False):
        if kernel_config is None:
            assert not check_kernel_config_version

        self._kernelCfg = kernel_config
        self._checkVer = check_kernel_config_version

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "genkernel"
        target_settings.kernel_manager_genkernel = {
            "kernel_config": self._kernelCfg,
            "check_kernel_config_version": self._checkVer
        }

    def update_world_set(self, world_set):
        for pkg in TargetSettings._getPackagesForKernelManager("genkernel"):
            world_set.add(pkg)


class UseDistKernel:

    def __init__(self, dracut_args=None):
        self._dracutArgs = dracut_args

    def update_target_settings(self, target_settings):
        assert "10-dist-kernel" not in target_settings.pkg_accept_keywords_files

        target_settings.kernel_manager = "distkernel"
        target_settings.kernel_manager_distkernel = {
            "dracut_args": self._dracutArgs,
        }

        target_settings.pkg_accept_keywords_files["10-dist-kernel"] = self._acceptKeywordsFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        for pkg in TargetSettings._getPackagesForKernelManager("distkernel", dracutArgs=self._dracutArgs):
            world_set.add(pkg)

    _acceptKeywordsFileContent = """
# dist-kernel must use >=app-misc/livecd-tools-2.10
app-misc/livecd-tools ~x86 ~amd64
"""


class UseBbki:

    def update_target_settings(self, target_settings):
        assert "10-bbki" not in target_settings.pkg_use_files
        assert "10-bbki" not in target_settings.pkg_mask_files

        # bbki is a library, it won't be used stand-alone, so we use "none" kernel manager here.
        target_settings.kernel_manager = "none"

        target_settings.pkg_use_files["10-bbki"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-bbki"] = self._maskFileContent.strip("\n") + "\n"
        target_settings.repo_postsync_patch_directories.append("use-bbki")

    _useFileContent = """
"""

    _maskFileContent = """
# we don't use any kernel related package
virtual/linux-sources
sys-kernel/*-sources
sys-kernel/*-kernel
sys-kernel/*-kernel-bin
app-emulation/virtualbox-modules
sys-fs/vhba

# we don't use any firmware related package
net-wireless/wireless-regdb
sys-firmware/*
sys-kernel/*-firmware

# we manage kernel ourself
sys-kernel/installkernel-*
"""


class UseFakeKernel:

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "fake"
        # FIXME: mask kernel related packages?
