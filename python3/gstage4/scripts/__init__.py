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


from ._template_script import ScriptFromHostFile
from ._template_script import ScriptFromHostDir
from ._template_script import ScriptFromBuffer
from ._template_script import OneLinerScript
from ._template_script import PlacingFilesScript            # deprecated

from ._template_function import CreateFileFunction
from ._template_function import CopyHostFileFunction
from ._template_function import CreateDirFunction
from ._template_function import CopyHostDirFunction
from ._template_function import CreateSymlinkFunction
from ._template_function import CopyHostSymlinkFunction

from ._common import ScriptInstallPackages
from ._common import ScriptUpdateWorld

__all__ = [
    "ScriptFromHostFile",
    "ScriptFromHostDir",
    "ScriptFromBuffer",
    "OneLinerScript",
    "PlacingFilesScript",
    "CreateFileFunction",
    "CopyHostFileFunction",
    "CreateDirFunction",
    "CopyHostDirFunction",
    "CreateSymlinkFunction",
    "CopyHostSymlinkFunction",
    "ScriptInstallPackages",
    "ScriptUpdateWorld",
]
