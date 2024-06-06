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


class CloudCacheGentooReleng:

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

