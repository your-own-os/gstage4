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


from ._errors import InvalidChrootInfo


class Target:

    def __init__(self):
        self.arch = None                 # the arch to be built
                                         # default: the same as the host system

        self.variant = None              # the variant to be built

        self.profile = None              # this is the system profile to be used for the live disk
                                         # it is specified as a relative path and must be set to one of the system profiles available at /var/db/repos/gentoo/profiles

        self.overlays = None             # list<Overlay>

        self.packages = None             # list<Package>

        self.build_opts = None

        # ?????
        self.use = None             # list?
        self.unmerge = None         # list?
        self.rm = None              # list?
        self.vol_id = None


class Overlay:

    def __init__(self):
        self.name = None


class Package:

    def __init__(self):
        self.name = None
        self.build_opts = None


class BuildOptions:

    def __init__(self):
        self.common_flags = None
        self.cflags = None
        self.cxxflags = None
        self.fcflags = None
        self.fflags = None
        self.ldflags = None
        self.asflags = None


class HostInfo:

    def __init__(self):
        self.distfiles_dir = None    # distfiles directory in host system, will be bind mounted in target system
                                     # default: None, means there's no such a directory in host system

        self.packages_dir = None     # packages directory in host system

        self.overlays = None         # overlays in host system, will be bind mounted in target system


class HostOverlay:

    def __init__(self):
        self.name = None
        self.dirpath = None


class ChrootInfo:

    def __init__(self):
        self.uid_map = None
        self.gid_map = None

    def conv_uid(self, uid):
        if self.uid_map is None:
            return uid
        else:
            if uid not in self.uid_map:
                raise InvalidChrootInfo("uid %d not found in uid map" % (uid))
            else:
                return self.uid_map[uid]

    def conv_gid(self, gid):
        if self.gid_map is None:
            return gid
        else:
            if gid not in self.gid_map:
                raise InvalidChrootInfo("gid %d not found in gid map" % (gid))
            else:
                return self.gid_map[gid]

    def conv_uid_gid(self, uid, gid):
        return (self.conv_uid(uid), self.conv_gid(gid))



