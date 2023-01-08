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


from ..scripts import ScriptFromBuffer


class ScriptInstallPackages(ScriptFromBuffer):

    def __init__(self, pkgList, verbose_level):
        buf = self._scriptContentFirstHalf
        if verbose_level == 0:
            buf += self._scriptContentSecondHalfVerboseLv0
        elif verbose_level == 1:
            buf += self._scriptContentSecondHalfVerboseLv1
        elif verbose_level == 2:
            buf += self._scriptContentSecondHalfVerboseLv2
        else:
            assert False
        buf = buf.replace("@@PKG_NAME@@", " ".join(pkgList))

        super().__init__(buf)

    _scriptContentFirstHalf = """
#!/bin/bash

export EMERGE_WARNING_DELAY=0
export CLEAN_DELAY=0
export EBEEP_IGNORE=0
export EPAUSE_IGNORE=0
export CONFIG_PROTECT="-* .x"
"""

    _scriptContentSecondHalfVerboseLv0 = """
emerge --color=y -1 @@PKG_NAME@@ > /var/log/portage/run-merge.log 2>&1 || exit 1
"""

    _scriptContentSecondHalfVerboseLv1 = """
# using grep to only show:
#   >>> Emergeing ...
#   >>> Installing ...
#   >>> Uninstalling ...
emerge --color=y -1 @@PKG_NAME@@ 2>&1 | tee /var/log/portage/run-merge.log | grep -E --color=never "^>>> .*\\(.*[0-9]+.*of.*[0-9]+.*\\)"
test ${PIPESTATUS[0]} -eq 0 || exit 1
"""

    _scriptContentSecondHalfVerboseLv2 = """
emerge --color=y -1 @@PKG_NAME@@ 2>&1 | tee /var/log/portage/run-update.log
test ${PIPESTATUS[0]} -eq 0 || exit 1
"""


class ScriptUpdateWorld(ScriptFromBuffer):

    def __init__(self, verbose_level):
        buf = self._scriptContentFirstHalf
        if verbose_level == 0:
            buf += self._scriptContentSecondHalfVerboseLv0
        elif verbose_level == 1:
            buf += self._scriptContentSecondHalfVerboseLv1
        elif verbose_level == 2:
            buf += self._scriptContentSecondHalfVerboseLv2
        else:
            assert False
        buf += self._scriptContentThirdHalf

        super().__init__(buf)

    _scriptContentFirstHalf = """
#!/bin/bash

die() {
    echo "$1"
    exit 1
}

export EMERGE_WARNING_DELAY=0
export CLEAN_DELAY=0
export EBEEP_IGNORE=0
export EPAUSE_IGNORE=0
export CONFIG_PROTECT="-* .x"
"""

    _scriptContentSecondHalfVerboseLv0 = """
emerge --color=y -uDN --with-bdeps=y @world > /var/log/portage/run-update.log 2>&1 || exit 1
"""

    _scriptContentSecondHalfVerboseLv1 = """
# using grep to only show:
#   >>> Emergeing ...
#   >>> Installing ...
#   >>> Uninstalling ...
#   >>> No outdated packages were found on your system.
emerge --color=y -uDN --with-bdeps=y @world 2>&1 | tee /var/log/portage/run-update.log | grep -E --color=never "^>>> (.*\\(.*[0-9]+.*of.*[0-9]+.*\\)|No outdated packages .*)"
test ${PIPESTATUS[0]} -eq 0 || exit 1
"""

    _scriptContentSecondHalfVerboseLv2 = """
emerge --color=y -uDN --with-bdeps=y @world 2>&1 | tee /var/log/portage/run-update.log
test ${PIPESTATUS[0]} -eq 0 || exit 1
"""

    _scriptContentThirdHalf = """
perl-cleaner --pretend --all >/dev/null 2>&1 || die "perl cleaning is needed, your seed stage is too old"
"""
