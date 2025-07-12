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


from ..scripts import OneLinerScript


class MemTest:

    def update_target_settings(self, target_settings):
        assert "10-memtest" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-memtest"] = self._useFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/memtest86+")

    _useFileContent = """
# don't install files into /boot
sys-apps/memtest86+                   -boot
"""


class SshServer:

    def update_world_set(self, world_set):
        world_set.add("net-misc/openssh")

    def update_service_list(self, service_list):
        if "sshd" not in service_list:
            service_list.append("sshd")

    def get_custom_action(self):
        # FIXME
        pass


class Chrony:

    def __init__(self, exclusive=False):
        self._exclusive = exclusive

    def update_target_settings(self, target_settings):
        assert "10-chrony" not in target_settings.pkg_mask_files

        if self._exclusive:
            target_settings.pkg_mask_files["10-chrony"] = self._maskFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("net-misc/chrony")

    def update_service_list(self, service_list):
        if "chronyd" not in service_list:
            service_list.append("chronyd")

    _maskFileContent = """
# we use net-misc/chrony only
net-misc/ntp
net-misc/ntpsec
net-misc/openntpd
"""


class NetworkManager:

    def __init__(self, wifi=False, exclusive=False):
        self._wifi = wifi
        self._exclusive = exclusive

    def update_target_settings(self, target_settings):
        assert "10-networkmanager" not in target_settings.pkg_use_files
        assert "10-networkmanager" not in target_settings.pkg_mask_files
        assert "10-networkmanager" not in target_settings.install_mask_files

        if self._wifi:
            target_settings.pkg_use_files["10-networkmanager"] = self._useFileContentWifiEnable.strip("\n") + "\n"
        else:
            target_settings.pkg_use_files["10-networkmanager"] = self._useFileContentWifiDisable.strip("\n") + "\n"

        if self._exclusive:
            target_settings.pkg_mask_files["10-networkmanager"] = self._maskFileContent.strip("\n") + "\n"
            target_settings.install_mask_files["10-networkmanager"] = {
                "*/*": [
                    "/lib/netifrc",         # removing net-misc/netifrc scripts
                ],
            }

    def update_world_set(self, world_set):
        world_set.add("net-misc/networkmanager")
        if self._wifi:
            # net-misc/networkmanager has already pulls in net-wireless/iwd
            # but we think explicily add it into @world is good
            world_set.add("net-wireless/iwd")

    def update_service_list(self, service_list):
        if "NetworkManager" not in service_list:
            service_list.append("NetworkManager")
        if self._wifi:
            if "iwd" not in service_list:
                service_list.append("iwd")

    _useFileContentWifiDisable = """
# networkmanager enables wifi by default, we have to disable wifi explicitly
net-misc/networkmanager                                                     -wext -wifi
"""

    _useFileContentWifiEnable = """
# we don't use deprecated wifi features (wext and -iwd)
net-misc/networkmanager                                                     -wext iwd wifi
"""

    _maskFileContent = """
# we don't use static network configuration scripts
net-misc/netifrc
"""


class UseZeroConf:

    @staticmethod
    def get_all_related_packages():
        return [
            "net-dns/avahi",
            "sys-auth/nss-mdns",
        ]

    def __init__(self, service):
        assert service == "avahi"

    def update_target_settings(self, target_settings):
        assert "10-zeroconf" not in target_settings.pkg_use_files
        assert "10-zeroconf" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-zeroconf"] = self._useFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("net-dns/avahi")
        world_set.add("sys-auth/nss-mdns")

    def update_service_list(self, service_list):
        if "avahi-daemon" not in service_list:
            service_list.append("avahi-daemon")

    def get_modify_nsswitch_script(self):
        return OneLinerScript("sed -iE '/^hosts:/ { /mdns_minimal( +.*)? +dns/! s/dns/mdns_minimal &/ }' /etc/nsswitch.conf")

    _useFileContent = """
*/*                     zeroconf
media-video/pipewire    -zeroconf          # what zeroconf in pipewire is for?
"""


class NotUseZeroConf:

    def update_target_settings(self, target_settings):
        assert "10-no-zeroconf" not in target_settings.pkg_use_files
        assert "10-no-zeroconf" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-no-zeroconf"] = self._maskFileContent.strip("\n") + "\n"

    _maskFileContent = """
net-dns/avahi
sys-auth/nss-mdns
"""


class UseBluetooth:

    @staticmethod
    def get_all_related_packages():
        return [
            "net-wireless/bluez"
        ]

    def __init__(self, service):
        assert service == "bluez"

    def update_target_settings(self, target_settings):
        assert "10-bluetooth" not in target_settings.pkg_use_files
        assert "10-bluetooth" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-no-bluetooth"] = self._useFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("net-wireless/bluez")

    def update_service_list(self, service_list):
        if "bluetooth" not in service_list:
            service_list.append("bluetooth")

    _useFileContent = """
*/*                         bluetooth
net-misc/networkmanager     -bluetooth          # what bluetooth in networkmanager is for?
"""


class NotUseBluetooth:

    def update_target_settings(self, target_settings):
        assert "10-no-bluetooth" not in target_settings.pkg_use_files
        assert "10-no-bluetooth" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-no-bluetooth"] = "\n".join(UseBluetooth.get_all_related_packages()) + "\n"


class UsePrinting:

    @staticmethod
    def get_all_related_packages():
        return [
            "net-print/cups",
            "net-print/cups-browsed",
            "net-print/cups-filters",
            "net-print/cups-meta",
        ]

    def __init__(self, service):
        assert service == "cups"

    def update_target_settings(self, target_settings):
        assert "10-printing" not in target_settings.pkg_use_files
        assert "10-printing" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-printing"] = self._useFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("net-print/cups-meta")

    def update_service_list(self, service_list):
        if "cups" not in service_list:
            service_list.append("cups")

    _useFileContent = """
*/*     cups
"""


class NotUsePrinting:

    def update_target_settings(self, target_settings):
        assert "10-no-printing" not in target_settings.pkg_use_files
        assert "10-no-printing" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-no-printing"] = "\n".join(UsePrinting.get_all_related_packages()) + "\n"


class UseAllQemuTargets:

    def update_target_settings(self, target_settings):
        assert "10-qemu-all-targets" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-qemu-all-targets"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
app-emulation/qemu  tci
app-emulation/qemu  QEMU_SOFTMMU_TARGETS: *
app-emulation/qemu  QEMU_USER_TARGETS: *
"""


class NotUseLogrotate:

    def update_target_settings(self, target_settings):
        assert "10-no-logrotate" not in target_settings.pkg_mask_files
        assert "10-no-logrotate" not in target_settings.install_mask_files

        target_settings.pkg_mask_files["10-no-logrotate"] = self._maskFileContent.strip("\n") + "\n"

        target_settings.install_mask_files["10-no-logrotate"] = {
            "*/*": [
                "/etc/logrotate.d",
            ],
        }

    _maskFileContent = """
app-admin/logrotate
sec-policy/selinux-logrotate
"""


class Kmscon:

    def update_target_settings(self, target_settings):
        assert target_settings.service_manager == "systemd"
        assert "10-kmscon" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-kmscon"] = self._useFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/kmscon")

    def update_service_list(self, service_list):
        # display-manager service should not be enabled, but we are not able to check it
        if "kmscon" not in service_list:
            service_list.append("kmscon")

    _useFileContent = """
sys-apps/kmscon systemd
"""
