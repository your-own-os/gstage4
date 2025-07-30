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


class DontUsePolicyKit:

    def update_target_settings(self, target_settings):
        assert "10-no-policykit" not in target_settings.pkg_use_files
        assert "10-no-policykit" not in target_settings.pkg_mask_files
        assert "10-no-policykit" not in target_settings.install_mask_files

        target_settings.pkg_use_files["10-no-policykit"] = self._useFileContent.strip("\n") + "\n"

        target_settings.pkg_mask_files["10-no-policykit"] = self._maskFileContent.strip("\n") + "\n"

        target_settings.install_mask_files["10-no-policykit"] = {
            "*/*": [
                "/usr/share/polkit-1",
            ],
        }

    _useFileContent = """
*/*     -policykit
"""

    _maskFileContent = """
sys-auth/polkit
"""


class DontUseSudo:

    def update_target_settings(self, target_settings):
        assert "10-no-sudo" not in target_settings.pkg_mask_files
        assert "10-no-sudo" not in target_settings.install_mask_files

        target_settings.pkg_mask_files["10-no-sudo"] = self._maskFileContent.strip("\n") + "\n"

        target_settings.install_mask_files["10-no-sudo"] = {
            "*/*": [
                "/etc/sudoers.d",
            ],
        }

    _maskFileContent = """
app-admin/sudo
sec-keys/openpgp-keys-sudo
sec-policy/selinux-sudo
"""


class UniversalWheelGroup:

    def update_target_settings(self, target_settings):
        assert "10-universal-wheel-group" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-universal-wheel-group"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# cupsd should consider wheel group and lpadmin group equal
net-print/cups     pam
"""
