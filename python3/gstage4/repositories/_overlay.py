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


import functools
import lxml.etree
import urllib.request
from .. import MountRepository
from .. import EmergeSyncRepository


class OverlayFromHost(MountRepository):

    def __init__(self, overlay_name, hostdir):
        self._name = overlay_name
        self._hostDir = hostdir

    def get_name(self):
        return self._name

    def get_datadir_path(self):
        return "/var/db/overlays/%s" % (self._name)

    def get_mount_params(self):
        return (self._hostDir, "bind")


class OverlayFromHostLayman(EmergeSyncRepository):

    def __init__(self, overlay_name):
        self._name = overlay_name

    def get_name(self):
        assert False

    def get_datadir_path(self):
        assert False

    def get_repos_conf_file_content(self):
        assert False


class RegisteredOverlay(EmergeSyncRepository):

    """Overlay in Gentoo Overlay Database (https://api.gentoo.org/overlays/repositories.xml)"""

    _foreignData = (0, None)

    def __init__(self, overlay_name, local_data=None):
        if local_data is not None:
            if self._foreignData[0] == 0:
                self._foreignData = (1, local_data)
            else:
                assert self._foreignData[0] == 1 and self._foreignData[1] == local_data
        else:
            if self._foreignData[0] == 0:
                self._foreignData = (-1, None)
            else:
                assert self._foreignData[0] == -1
            local_data = self._parse()

        self._name = overlay_name
        self._syncType = local_data[overlay_name][0]
        self._syncUrl = local_data[overlay_name][1]

    def get_name(self):
        return self._name

    def get_datadir_path(self):
        return "/var/db/overlays/%s" % (self._name)

    def get_repos_conf_file_content(self):
        buf = ""
        buf += "[%s]\n" % (self._name)
        buf += "auto-sync = yes\n"
        buf += "location = %s\n" % (self.get_datadir_path())
        buf += "sync-type = %s\n" % (self._syncType)
        buf += "sync-uri = %s\n" % (self._syncUrl)
        return buf

    @staticmethod
    @functools.cache
    def _parse():
        cList = [
            ("git", "https", "github.com"),
            ("git", "https", "gitlab.com"),
            ("git", "https", None),
            ("git", "http", None),
            ("git", "git", None),
            ("svn", "https", None),
            ("svn", "http", None),
            ("mercurial", "https", None),
            ("mercurial", "http", None),
            ("rsync", "rsync", None),
        ]

        buf = None
        with urllib.request.urlopen("https://api.gentoo.org/overlays/repositories.xml") as resp:
            buf = resp.read().decode("utf-8")

        ret = dict()
        rootElem = lxml.etree.fromstring(buf).getroot()
        for nameTag in rootElem.xpath(".//repo/name"):
            overlayName = nameTag.text
            if overlayName in ret:
                raise Exception("duplicate overlay \"%s\"" % (overlayName))

            for vcsType, urlProto, urlDomain in cList:
                for sourceTag in nameTag.xpath("../source"):
                    tVcsType = sourceTag.get("type")
                    tUrl = sourceTag.text
                    if tUrl.startswith("git://github.com/"):                            # FIXME: github does not support git:// anymore
                        tUrl = tUrl.replace("git://", "https://")
                    if tVcsType == vcsType:
                        if urlDomain is not None:
                            if tUrl.startswith(urlProto + "://" + urlDomain + "/"):
                                ret[overlayName] = (tVcsType, tUrl)
                                break
                        else:
                            if tUrl.startswith(urlProto + "://"):
                                ret[overlayName] = (tVcsType, tUrl)
                                break
                if overlayName in ret:
                    if ret[overlayName][1].startswith("https://github.com/"):
                        # for github mirror
                        url = ret[overlayName][1]
                        url = url.replace("https://github.com/", "mirror://github/")
                        ret[overlayName] = (ret[overlayName][0], url)
                    break

            if overlayName not in ret:
                raise Exception("no appropriate source for overlay \"%s\"" % (overlayName))

        return ret


class UserDefinedOverlay(EmergeSyncRepository):

    """Unofficial overlay managed by individuals"""

    def __init__(self, overlay_name, sync_type, sync_url):      # FIXME: should change to using kwargs for each sync_type
        validUrlSchemas = {
            "git": ["git", "http", "https"],
        }
        assert sync_type in validUrlSchemas
        assert any([sync_url.startswith(x + "://") for x in validUrlSchemas[sync_type]])

        self._name = overlay_name
        self._syncType = sync_type
        self._syncUrl = sync_url

    def get_name(self):
        return self._name

    def get_datadir_path(self):
        return "/var/db/overlays/%s" % (self._name)

    def get_repos_conf_file_content(self):
        buf = ""
        buf += "[%s]\n" % (self._name)
        buf += "auto-sync = yes\n"
        buf += "location = %s\n" % (self.get_datadir_path())
        buf += "sync-type = %s\n" % (self._syncType)
        buf += "sync-uri = %s\n" % (self._syncUrl)
        return buf
