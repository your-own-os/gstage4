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


from .._errors import SettingsError
from .._prototype import EmergeSyncRepository
from ..cloud_data import OverlayDb


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

    _localData = None

    def __init__(self, overlay_name, rw=False):
        if self._localData is None:
            self._localData = OverlayDb()

        if not self._localData.has_overlay(overlay_name):
            raise SettingsError("overlay \"%s\" does not exist" % (overlay_name))

        self._name = overlay_name
        self._syncType = self._localData.get_overlay_vcs_type(overlay_name)
        self._syncUrl = self._localData.get_overlay_url(overlay_name)
        self._syncDepth = 1 if not rw else None

    def get_name(self):
        return self._name

    def get_datadir_path(self):
        return "/var/db/overlays/%s" % (self._name)

    def get_repos_conf_file_content(self):
        buf = ""
        buf += "[%s]\n" % (self._name)
        buf += "location = %s\n" % (self.get_datadir_path())
        buf += "auto-sync = yes\n"
        buf += "sync-type = %s\n" % (self._syncType)
        buf += "sync-uri = %s\n" % (self._syncUrl)
        if self._syncDepth is not None:
            buf += "sync-depth = %d\n" % (self._syncDepth)
            buf += "clone-depth = %d\n" % (self._syncDepth)
        return buf


class UserDefinedOverlay(EmergeSyncRepository):

    """Unofficial overlay managed by individuals"""

    # FIXME: should change to using kwargs for each sync_type
    def __init__(self, overlay_name, sync_type, sync_url, rw=False):
        validUrlSchemas = {
            "git": ["git", "http", "https"],
        }
        assert sync_type in validUrlSchemas
        assert any(sync_url.startswith(x + "://") for x in validUrlSchemas[sync_type])

        self._name = overlay_name
        self._syncType = sync_type
        self._syncUrl = sync_url
        self._syncDepth = 1 if not rw else None

    def get_name(self):
        return self._name

    def get_datadir_path(self):
        return "/var/db/overlays/%s" % (self._name)

    def get_repos_conf_file_content(self):
        buf = ""
        buf += "[%s]\n" % (self._name)
        buf += "location = %s\n" % (self.get_datadir_path())
        buf += "auto-sync = yes\n"
        buf += "sync-type = %s\n" % (self._syncType)
        buf += "sync-uri = %s\n" % (self._syncUrl)
        if self._syncDepth is not None:
            buf += "sync-depth = %d\n" % (self._syncDepth)
            buf += "clone-depth = %d\n" % (self._syncDepth)
        return buf
