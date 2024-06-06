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


import mrget


class Gentoo:

    def __init__(self, cacheDir):
        self._baseUrl = mrget.target_urls("mirror://gentoo", protocols=["http", "https", "ftp"])[0]

        self._dir = cacheDir
        self._releasesDir = os.path.join(self._dir, "releases")
        self._snapshotsDir = os.path.join(self._dir, "snapshots")

        self._bSynced = (os.path.exists(self._releasesDir) and len(os.listdir(self._releasesDir)) > 0)

    def sync(self):
        os.makedirs(self._releasesDir, exist_ok=True)
        os.makedirs(self._snapshotsDir, exist_ok=True)

        # fill arch directories
        if True:
            archList = []
            while True:
                try:
                    with urllib.request.urlopen(os.path.join(self._baseUrl, "releases"), timeout=robust_layer.TIMEOUT) as resp:
                        root = lxml.html.parse(resp)
                        for elem in root.xpath(".//a"):
                            if elem.text is None:
                                continue
                            m = re.fullmatch("(\\S+)/", elem.text)
                            if m is None or m.group(1) in [".", ".."]:
                                continue
                            archList.append(m.group(1))
                        break
                except Exception:
                    print("Failed, retrying...")
                    time.sleep(robust_layer.RETRY_WAIT)

            # fill arch directories
            FmUtil.syncDirs(archList, self._releasesDir)

        # fill variant and release directories
        for arch in archList:
            variantList = []
            versionList = []
            while True:
                try:
                    with urllib.request.urlopen(self._getAutoBuildsUrl(arch), timeout=robust_layer.TIMEOUT) as resp:
                        for elem in lxml.html.parse(resp).xpath(".//a"):
                            if elem.text is not None:
                                m = re.fullmatch("current-(\\S+)/", elem.text)
                                if m is not None:
                                    variantList.append(m.group(1))
                                m = re.fullmatch("([0-9]+T[0-9]+Z)/", elem.text)
                                if m is not None:
                                    versionList.append(m.group(1))
                        break
                except Exception:
                    print("Failed, retrying...")
                    time.sleep(robust_layer.RETRY_WAIT)

            # fill variant directories
            archDir = os.path.join(self._releasesDir, arch)
            FmUtil.syncDirs(variantList, archDir)

            # fill release directories in variant directories
            for variant in variantList:
                FmUtil.syncDirs(versionList, os.path.join(archDir, variant))

        # fill snapshots directory
        if True:
            versionList = []
            while True:
                try:
                    with urllib.request.urlopen(os.path.join(self._baseUrl, "snapshots", "squashfs"), timeout=robust_layer.TIMEOUT) as resp:
                        for elem in lxml.html.parse(resp).xpath(".//a"):
                            if elem.text is not None:
                                m = re.fullmatch("gentoo-([0-9]+).xz.sqfs", elem.text)
                                if m is not None:
                                    versionList.append(m.group(1))
                        break
                except Exception:
                    print("Failed, retrying...")
                    time.sleep(robust_layer.RETRY_WAIT)

            # fill snapshots directories
            FmUtil.syncDirs(versionList, self._snapshotsDir)

        self._bSynced = True

    def get_arch_list(self):
        assert self._bSynced
        return os.listdir(self._releasesDir)

    def get_subarch_list(self, arch):
        assert self._bSynced
        ret = set()
        for d in os.listdir(os.path.join(self._releasesDir, arch)):
            ret.add(d.split("-")[1])
        return sorted(list(ret))

    def get_release_variant_list(self, arch):
        assert self._bSynced
        return os.listdir(os.path.join(self._releasesDir, arch))

    def get_release_version_list(self, arch):
        assert self._bSynced
        return os.listdir(os.path.join(self._releasesDir, arch, self.get_release_variant_list(arch)[0]))

    def get_snapshot_version_list(self):
        assert self._bSynced
        return os.listdir(self._snapshotsDir)

    def get_stage3(self, arch, subarch, stage3_release_variant, release_version, cached_only=False):
        assert self._bSynced

        releaseVariant = self._stage3GetReleaseVariant(subarch, stage3_release_variant)

        myDir = os.path.join(self._releasesDir, arch, releaseVariant, release_version)
        if not os.path.exists(myDir):
            raise FileNotFoundError("the specified stage3 does not exist")

        fn, fnDigest = self._getFn(releaseVariant, release_version)
        fullfn = os.path.join(myDir, fn)
        fullfnDigest = os.path.join(myDir, fnDigest)

        url = os.path.join(self._getAutoBuildsUrl(arch), release_version, fn)
        urlDigest = os.path.join(self._getAutoBuildsUrl(arch), release_version, fnDigest)

        if os.path.exists(fullfn) and os.path.exists(fullfnDigest):
            print("Files already downloaded.")
            return (fullfn, fullfnDigest)

        if cached_only:
            raise FileNotFoundError("the specified stage3 does not exist")

        FmUtil.wgetDownload(url, fullfn)
        FmUtil.wgetDownload(urlDigest, fullfnDigest)
        return (fullfn, fullfnDigest)

    def get_latest_stage3(self, arch, subarch, stage3_release_variant, cached_only=False):
        assert self._bSynced

        releaseVariant = self._stage3GetReleaseVariant(subarch, stage3_release_variant)

        variantDir = os.path.join(self._releasesDir, arch, releaseVariant)
        for ver in sorted(os.listdir(variantDir), reverse=True):
            myDir = os.path.join(variantDir, ver)

            fn, fnDigest = self._getFn(releaseVariant, ver)
            fullfn = os.path.join(myDir, fn)
            fullfnDigest = os.path.join(myDir, fnDigest)

            url = os.path.join(self._getAutoBuildsUrl(arch), ver, fn)
            urlDigest = os.path.join(self._getAutoBuildsUrl(arch), ver, fnDigest)

            if os.path.exists(fullfn) and os.path.exists(fullfnDigest):
                print("Files already downloaded.")
                return (fullfn, fullfnDigest)

            if not cached_only:
                if FmUtil.wgetSpider(url):
                    FmUtil.wgetDownload(url, fullfn)
                    FmUtil.wgetDownload(urlDigest, fullfnDigest)
                    return (fullfn, fullfnDigest)

        raise FileNotFoundError("no stage3 found")

    def get_snapshot(self, snapshot_version, cached_only=False):
        assert self._bSynced

        myDir = os.path.join(self._snapshotsDir, snapshot_version)
        if not os.path.exists(myDir):
            raise FileNotFoundError("the specified snapshot does not exist")

        fn = "gentoo-%s.xz.sqfs" % (snapshot_version)
        fullfn = os.path.join(myDir, fn)
        url = os.path.join(self._baseUrl, "snapshots", "squashfs", fn)

        if os.path.exists(fullfn):
            print("Files already downloaded.")
            return fullfn

        if cached_only:
            raise FileNotFoundError("the specified snapshot does not exist")

        FmUtil.wgetDownload(url, fullfn)
        return fullfn

    def get_latest_snapshot(self, cached_only=False):
        assert self._bSynced

        for ver in sorted(os.listdir(self._snapshotsDir), reverse=True):
            myDir = os.path.join(self._snapshotsDir, ver)
            fn = "gentoo-%s.xz.sqfs" % (ver)
            fullfn = os.path.join(myDir, fn)
            url = os.path.join(self._baseUrl, "snapshots", "squashfs", fn)

            if os.path.exists(fullfn):
                print("Files already downloaded.")
                return fullfn

            if not cached_only:
                if FmUtil.wgetSpider(url):
                    FmUtil.wgetDownload(url, fullfn)
                    return fullfn

        raise FileNotFoundError("no snapshot found")

    def _getAutoBuildsUrl(self, arch):
        return os.path.join(self._baseUrl, "releases", arch, "autobuilds")

    def _stage3GetReleaseVariant(self, subarch, stage3ReleaseVariant):
        ret = "stage3-%s" % (subarch)
        if stage3ReleaseVariant != "":
            ret += "-%s" % (stage3ReleaseVariant)
        return ret

    def _getFn(self, releaseVariant, releaseVersion):
        fn = releaseVariant + "-" + releaseVersion + ".tar.xz"
        fnDigest = fn + ".DIGESTS"
        return (fn, fnDigest)
