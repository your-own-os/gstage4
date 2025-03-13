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


class UseGogMirror:

    def update_target_settings(self, target_settings):
        assert "10-use-mirror-gog" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-use-mirror-gog"] = self._useFileContent.strip("\n") + "\n"

        target_settings.repo_postsync_patch_directories.append("use-mirror-gog")

    _useFileContent = """
games-fps/duke3d-data      -demo gog
"""


class UseHbMirror:

    def update_target_settings(self, target_settings):
        target_settings.repo_postsync_patch_directories.append("use-mirror-hb")


class UseHuggingFaceMirror:

    def update_target_settings(self, target_settings):
        target_settings.repo_postsync_patch_directories.append("use-mirror-huggingface")
