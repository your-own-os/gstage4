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


import lxml.etree
import urllib.request
from datetime import datetime
from .._errors import UpstreamError


class OverlayDb:

    URL = "https://api.gentoo.org/overlays/repositories.xml"

    def __init__(self, strict=False, prefer_mirror=True):
        self._bStrict = strict
        self._bPreferMirror = prefer_mirror
        self._data = None
        self._lastModifiedTime = None

    def get_last_modified_time(self):
        self._ensureLastModifiedTime()
        return self._lastModifiedTime

    def get_overlays(self):
        self._ensureData()
        return self._data.keys()

    def has_overlay(self, overlay_name):
        self._ensureData()
        return overlay_name in self._data

    def get_overlay_vcs_type(self, overlay_name):
        self._ensureData()
        return self._data[overlay_name][0]

    def get_overlay_url(self, overlay_name):
        self._ensureData()
        return self._data[overlay_name][1]

    def export_data(self):
        self._ensureData()
        return self._data

    def _ensureLastModifiedTime(self):
        if self._lastModifiedTime is not None:
            return

        with urllib.request.urlopen(urllib.request.Request(self.URL, method="HEAD")) as resp:
            self._lastModifiedTime = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")

    def _ensureData(self):
        if self._data is not None:
            return

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

        with urllib.request.urlopen(self.URL) as resp:
            ret = dict()

            rootElem = lxml.etree.fromstring(resp.read())
            for nameTag in rootElem.xpath(".//repo/name"):
                overlayName = nameTag.text
                if overlayName in ret:
                    raise UpstreamError("duplicate overlay \"%s\"" % (overlayName))

                for vcsType, urlProto, urlDomain in cList:
                    for sourceTag in nameTag.xpath("../source"):
                        tVcsType = sourceTag.get("type")
                        tUrl = sourceTag.text
                        if tUrl.startswith("git://github.com/"):
                            if self._bStrict:
                                raise UpstreamError("git://github.com in URL of overlay \"%s\" is not supported anymore" % (overlayName))
                            else:
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
                        break

                if overlayName not in ret:
                    raise UpstreamError("no appropriate source for overlay \"%s\"" % (overlayName))

            if self._bPreferMirror:
                for overlayName in ret.keys():
                    # for github mirror
                    if ret[overlayName][1].startswith("https://github.com/"):
                        ret[overlayName] = (ret[overlayName][0], ret[overlayName][1].replace("https://github.com/", "mirror://github/"))

            self._data = ret
            self._lastModifiedTime = datetime.strptime(resp.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z")
