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
from ._errors import HostInfoError


class HostInfo:

    def __init__(self):
        # computing power
        self.cpu_core_count = None
        self.memory_size = None             # in byte
        self.cooling_level = None           # 1-10, less is weaker

        # repo.postsync.d patch framework
        self.repo_postsync_patch_script = "/usr/libexec/gstage4/patch-repository"
        self.repo_postsync_patch_source_dir = "/usr/libexec/gstage4/patch-repository.d"

        # distfiles directory in host system, will be bind mounted in target system
        self.distfiles_dir = None

        # packages directory in host system
        self.packages_dir = None

        # ccache directory in host system
        self.ccache_dir = None

    def auto_fill_computing_power(self):
        # cpu_core_count
        self.cpu_core_count = multiprocessing.cpu_count()

        # memory_size
        with open("/proc/meminfo", "r") as f:
            # Since the memory size shown in /proc/meminfo is always a
            # little less than the real size because various sort of
            # reservation, so we do a "+1GB"
            m = re.search("^MemTotal:\\s+(\\d+)", f.read())
            self.memory_size = (int(m.group(1)) // 1024 // 1024 + 1) * 1024 * 1024

        # cooling_level
        self.cooling_level = 5

    @classmethod
    def check_object(cls, obj, raise_exception=None):
        assert raise_exception is not None

        if not isinstance(obj, cls):
            if raise_exception:
                raise HostInfoError("invalid object type")
            else:
                return False

        if obj.cpu_core_count <= 0:
            if raise_exception:
                raise HostInfoError("invalid value of \"cpu_core_count\"")
            else:
                return False

        if obj.memory_size <= 0:
            if raise_exception:
                raise HostInfoError("invalid value of \"memory_size\"")
            else:
                return False

        if not (1 <= obj.cooling_level <= 10):
            if raise_exception:
                raise HostInfoError("invalid value of \"cooling_level\"")
            else:
                return False

        if obj.distfiles_dir is not None and not os.path.isdir(obj.distfiles_dir):
            if raise_exception:
                raise HostInfoError("invalid value for key \"distfiles_dir\"")
            else:
                return False

        if obj.packages_dir is not None and not os.path.isdir(obj.packages_dir):
            if raise_exception:
                raise HostInfoError("invalid value for key \"packages_dir\"")
            else:
                return False

        if obj.ccache_dir is not None and not os.path.isdir(obj.ccache_dir):
            if raise_exception:
                raise HostInfoError("invalid value for key \"ccache_dir\"")
            else:
                return False

        return True
