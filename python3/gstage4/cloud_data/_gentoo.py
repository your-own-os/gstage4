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
import mrget
import lxml.html
from .._util import Util


class GentooReleases:

    def __init__(self):
        self._baseUrl = mrget.target_urls("mirror://gentoo", protocols=["http", "https", "ftp"])[0]
        self._releasesUrl = os.path.join(self._baseUrl, "releases")

        self._archList = None
        self._variantDict = dict()
        self._versionDict = dict()

    def get_url(self):
        return self._releasesUrl

    def get_arch_list(self):
        self._ensureArchList()
        return self._archList

    def get_subarch_list(self, arch):
        self._ensureArchList()
        self._ensureVariantDictAndVersionDict(arch)

        ret = set()
        for d in self._variantDict[arch]:
            ret.add(d.split("-")[1])
        return sorted(list(ret))

    def get_release_variant_list(self, arch):
        self._ensureArchList()
        self._ensureVariantDictAndVersionDict(arch)

        return self._variantDict[arch]

    def get_release_version_list(self, arch):
        self._ensureArchList()
        self._ensureVariantDictAndVersionDict(arch)

        return self._versionDict[arch]

    def gen_stage3_fn(self, arch, release_variant, release_version):
        assert release_variant.startswith("stage3-")
        fn = release_variant + "-" + release_version + ".tar.xz"
        fnDigest = fn + ".DIGESTS"
        return (fn, fnDigest)

    def gen_stage3_url(self, arch, release_variant, release_version):
        fn, fnDigest = self.gen_stage3_fn(arch, release_variant, release_version)
        url = os.path.join(self.__getAutoBuildsUrl(self._baseUrl, arch), release_version, fn)
        urlDigest = os.path.join(self.__getAutoBuildsUrl(self._baseUrl, arch), release_version, fnDigest)
        return (url, urlDigest)

    def get_latest_stage3_release_version(self, arch):
        self._ensureArchList()
        self._ensureVariantDictAndVersionDict(arch)

        return sorted(self._versionDict[arch], reverse=True)[0]

    def get_latest_stage3_url(self, arch, subarch, release_variant):
        releaseVersion = self.get_latest_stage3_release_version(arch)
        return self.gen_stage3_url(arch, subarch, release_variant, releaseVersion)

    def _ensureArchList(self):
        if self._archList is not None:
            return

        self._archList = []
        for resp in Util.robustUrlOpen(os.path.join(self._baseUrl, "releases")):
            root = lxml.html.parse(resp)
            for elem in root.xpath(".//a"):
                if elem.text is None:
                    continue
                m = re.fullmatch("(\\S+)/", elem.text)
                if m is None or m.group(1) in [".", ".."]:
                    continue
                self._archList.append(m.group(1))

    def _ensureVariantDictAndVersionDict(self, arch):
        if arch in self._variantDict and arch in self._versionDict:
            return

        variantList = []
        versionList = []
        for resp in Util.robustUrlOpen(self.__getAutoBuildsUrl(self._baseUrl, arch)):
            for elem in lxml.html.parse(resp).xpath(".//a"):
                if elem.text is not None:
                    m = re.fullmatch("current-(\\S+)/", elem.text)
                    if m is not None:
                        variantList.append(m.group(1))
                    m = re.fullmatch("([0-9]+T[0-9]+Z)/", elem.text)
                    if m is not None:
                        versionList.append(m.group(1))

        self._variantDict[arch] = variantList
        self._versionDict[arch] = versionList

    @staticmethod
    def __getAutoBuildsUrl(baseUrl, arch):
        return os.path.join(baseUrl, "releases", arch, "autobuilds")


class GentooSnapshots:

    def __init__(self):
        self._baseUrl = mrget.target_urls("mirror://gentoo", protocols=["http", "https", "ftp"])[0]
        self._snapshotsUrl = os.path.join(self._baseUrl, "snapshots")
        self._snapshotList = None

    def get_url(self):
        return self._snapshotsUrl

    def get_snapshot_version_list(self):
        self._ensureSnapshotList()

        return self._snapshotList

    def gen_snapshot_fn(self, snapshot_version):
        return "gentoo-%s.xz.sqfs" % (snapshot_version)

    def gen_snapshot_url(self, snapshot_version):
        return os.path.join(self._baseUrl, "snapshots", "squashfs", self.gen_snapshot_fn(snapshot_version))

    def get_latest_snapshot_url(self):
        self._ensureSnapshotList()

        snapshot_version = sorted(self._snapshotList, reverse=True)[0]
        return self.gen_snapshot_url(snapshot_version)

    def _ensureSnapshotList(self):
        if self._snapshotList is not None:
            return

        self._snapshotList = []
        for resp in Util.robustUrlOpen(os.path.join(self._baseUrl, "snapshots", "squashfs")):
            for elem in lxml.html.parse(resp).xpath(".//a"):
                if elem.text is not None:
                    m = re.fullmatch("gentoo-([0-9]+).xz.sqfs", elem.text)
                    if m is not None:
                        self._snapshotList.append(m.group(1))
