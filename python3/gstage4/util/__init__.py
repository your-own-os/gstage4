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

class CloudGentooReleases:
    pass

class CloudGentooSnapshots:
    pass

class CloudGentooReleasesWithCache(CloudGentooReleases):
    pass

class CloudGentooSnapshots(CloudGentooSnapshots):
    pass

class CloudCacheGentooWithCache:

    def __init__(self, cacheDir):
        self._baseUrl = mrget.target_urls("mirror://gentoo", filter_key=lambda x: x["protocol"] in ["http", "https", "ftp"])[0]

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


class CloudGentooReleng:

    class Stage1Spec:
        def __init__(self):
            assert False

    class Stage2Spec:
        def __init__(self):
            assert False

    class Stage3Spec:
        def __init__(self):
            assert False

    class LivecdStage1Spec:
        def __init__(self):
            assert False

    class LivecdStage2Spec:

        def __init__(self, baseDir, arch, subarch, fullfn, buf):
            self.arch = arch
            self.subarch = subarch
            self.profile = None
            self.kernel_sources_pkg_atom = None
            self.kernel_config = None

            for line in buf.split("\n"):
                m = re.fullmatch(r"profile:\s+(.*)", line)
                if m is not None:
                    self.profile = m.group(1)
                    continue
                m = re.fullmatch(r"boot/kernel/gentoo/sources:\s+(.*)", line)
                if m is not None:
                    if m.group(1).startswith("sys-kernel/"):
                        self.kernel_sources_pkg_atom = m.group(1)
                    else:
                        self.kernel_sources_pkg_atom = "sys-kernel/" + m.group(1)
                    continue
                m = re.fullmatch(r"boot/kernel/gentoo/config:\s+(.*)", line)
                if m is not None:
                    fn = m.group(1).replace("@REPO_DIR@/", "")
                    self.kernel_config = pathlib.Path(os.path.join(baseDir, fn)).read_text()
                    continue

            if self.profile is None:
                raise Exception("no key \"profile\" in \"%s\"" % (fullfn))
            if self.kernel_sources_pkg_atom is None:
                raise Exception("no key \"boot/kernel/gentoo/sources\" in \"%s\"" % (fullfn))
            if self.kernel_config is None:
                raise Exception("no key \"boot/kernel/gentoo/config\" in \"%s\"" % (fullfn))

    def __init__(self):
        self._baseUrl = "https://gitweb.gentoo.org/proj/releng.git"

    def get_arch_list(self):
        assert False

    def get_subarch_list(self, arch):
        assert False

    def get_spec(self, arch, subarch, name):
        assert False

    def _parse(self, buf):
        ret = {
            "subarch": None,
            "target": None,
        }
        for line in buf.split("\n"):
            for key in ret.keys():
                m = re.fullmatch(r"%s:\s+(.*)" % (key), line)
                if m is not None:
                    ret[key] = m.group(1)
                    break
        return ret


class CloudGentooRelengWithCache(CloudGentooReleng):

    def __init__(self, cacheDir):
        self._baseUrl = "https://gitweb.gentoo.org/proj/releng.git"
        self._dir = cacheDir

    def sync(self):
        robust_layer.simple_git.pull(self._dir, reclone_on_failure=True, url=self._baseUrl)

    def get_arch_list(self):
        assert self._isSynced()
        list1 = os.listdir(os.path.join(self._dir, "releases", "specs"))
        list2 = os.listdir(os.path.join(self._dir, "releases", "specs-qemu"))
        return sorted(list(set(list1 + list2)))

    def get_subarch_list(self, arch):
        assert self._isSynced()
        assert False

    def get_spec(self, arch, subarch, name):
        assert self._isSynced()
        assert arch in self.get_arch_list()

        if arch == "amd64":
            assert subarch == "amd64"
            specFullfn = os.path.join(self._dir, "releases", "specs", arch, "%s.spec" % (name))
            if not os.path.exists(specFullfn):
                raise FileNotFoundError("no spec file found")
        else:
            assert False

        buf = pathlib.Path(specFullfn).read_text()
        ret = self._parse(buf)

        if ret["subarch"] != subarch:
            raise FileNotFoundError("no spec file found")

        if ret["target"] == "stage1":
            return self.Stage1Spec(self._dir, arch, subarch, specFullfn, buf)
        elif ret["target"] == "stage2":
            return self.Stage2Spec(self._dir, arch, subarch, specFullfn, buf)
        elif ret["target"] == "stage3":
            return self.Stage3Spec(self._dir, arch, subarch, specFullfn, buf)
        elif ret["target"] == "livecd-stage1":
            return self.LivecdStage1Spec(self._dir, arch, subarch, specFullfn, buf)
        elif ret["target"] == "livecd-stage2":
            return self.LivecdStage2Spec(self._dir, arch, subarch, specFullfn, buf)
        else:
            raise Exception("unknown target \"%s\" in \"%s\"" % (ret["target"], specFullfn))

    def _isSynced(self):
        return os.path.exists(os.path.join(self._dir, ".git", "config"))
