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


from ..custom_actions import SimpleCustomAction
from ..scripts import OneLinerScript
from ..scripts import PlacingFilesScript


class FixBugs:

    def update_target_settings(self, target_settings):
        target_settings.repo_postsync_patch_directories.append("bugfix")


class UsePortage:

    def update_target_settings(self, target_settings):
        target_settings.package_manager = "portage"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/portage")


class UseGenkernel:

    def __init__(self, kernel_sources_pkg_atom="sys-kernel/gentoo-sources", kernel_config=None, check_kernel_config_version=False):
        if kernel_config is None:
            assert not check_kernel_config_version

        self._kernelPkg = kernel_sources_pkg_atom
        self._kernelCfg = kernel_config
        self._checkVer = check_kernel_config_version

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "genkernel"
        target_settings.kernel_manager_genkernel = {
            "kernel_config": self._kernelCfg,
            "check_kernel_config_version": self._checkVer
        }

    def update_world_set(self, world_set):
        world_set.add("sys-kernel/genkernel")
        world_set.add("sys-devel/bc")           # kernel build script needs it
        world_set.add(self._kernelPkg)


class UseBinaryKernel:

    def __init__(self, kernel_pkg_atom="sys-kernel/gentoo-kernel-bin"):
        self._kernelPkg = kernel_pkg_atom

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "binary-kernel"

    def update_world_set(self, world_set):
        world_set.add(self._kernelPkg)


class UseBbki:

    def update_target_settings(self, target_settings):
        assert "10-bbki" not in target_settings.pkg_use_files
        assert "10-bbki" not in target_settings.pkg_mask_files

        # bbki is a library, it won't be used stand-alone, so we use "none" kernel manager here.
        target_settings.kernel_manager = "none"

        target_settings.pkg_use_files["10-bbki"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-bbki"] = self._maskFileContent.strip("\n") + "\n"
        target_settings.repo_postsync_patch_directories.append("use-bbki")

    def remove_actions(self, builder):
        if builder.has_action("install_kernel"):
            builder.remove_action("install_kernel")

    _useFileContent = """
"""

    _maskFileContent = """
# we don't use any kernel & firmware related package
virtual/linux-sources
sys-kernel/*-sources
sys-kernel/*-kernel
sys-kernel/*-kernel-bin
net-wireless/wireless-regdb
app-emulation/virtualbox-modules
sys-fs/vhba

# we manage kernel ourself
sys-kernel/installkernel-*
"""


class UseFakeKernel:

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "fake"
        # FIXME: mask kernel related packages?


class UseOpenrc:

    def update_target_settings(self, target_settings):
        assert "10-openrc" not in target_settings.pkg_use_files
        assert "10-openrc" not in target_settings.pkg_mask_files

        target_settings.service_manager = "openrc"

        target_settings.pkg_use_files["10-openrc"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-openrc"] = self._maskFileContent.strip("\n") + "\n"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/sysvinit")              # FIXME: maybe we should make it "openrc+sysvinit" and "openrc+s6-linux-init"
        world_set.add("sys-apps/openrc")

    _useFileContent = """
"""

    _maskFileContent = """
# don't use other init system
sys-apps/s6-linux-init
sys-apps/systemd
"""


class UseSystemd:

    def update_target_settings(self, target_settings):
        assert "10-systemd" not in target_settings.pkg_use_files
        assert "10-systemd" not in target_settings.pkg_mask_files
        assert "10-systemd" not in target_settings.install_mask_files

        target_settings.service_manager = "systemd"

        target_settings.pkg_use_files["10-systemd"] = self._useFileContent.strip("\n") + "\n"

        target_settings.pkg_mask_files["10-systemd"] = self._maskFileContent.strip("\n") + "\n"

        target_settings.install_mask_files["10-systemd"] = {
            "*/*": [
                "/etc/init.d",
                "/etc/conf.d",
                "/etc/rc.d",
            ],
            "sys-apps/systemd": [
                "*initctl*",                    # FIXME: no initctl for >=systemd-253-r1?
                "*runlevel*",
                "*systemd-sysv-generator*",
                "*rc-local*",
            ],
        }

        target_settings.repo_postsync_patch_directories.append("systemd-remove-sysvinit")               # we don't use sys-apps/sysvinit anymore
        target_settings.repo_postsync_patch_directories.append("systemd-remove-udev-init-scripts")      # package sys-fs/udev-init-scripts only install files into /etc/init.d and /etc/conf.d, but we don't use these 2 directories, so we remove this dependency

    def update_world_set(self, world_set):
        world_set.add("sys-apps/systemd")

    def get_custom_action_set_machine_id(self, machine_id):
        return SimpleCustomAction(OneLinerScript('echo "%s" > /etc/machine-id'), after=["unpack"])

    def get_custom_action_set_random_machine_id(self):
        return SimpleCustomAction(OneLinerScript('echo $(cat /dev/urandom | tr -dc "a-f0-9" | fold -w 32 | head -n 1) > /etc/machine-id'), after=["unpack"])

    _useFileContent = """
# system component should use systemd
sys-apps/util-linux                                                  systemd          # I'm not sure, but I think it'd better to enable it
sys-libs/glibc                                                       systemd          # I'm not sure, but I think it'd better to enable it
sys-apps/dbus                                                        systemd          # I'm not sure, but I think it'd better to enable it
sys-auth/seatd                                                       systemd          # so that libseat can communicate with systemd

# so that we can use systemd-udev
virtual/libudev                                                      systemd
virtual/udev                                                         systemd
virtual/tmpfiles                                                     systemd

# so that it does not depends on gui-libs/display-manager-init
x11-base/xorg-server                                                 systemd

# install systemd service files
media-video/pipewire                                                 systemd
media-video/wireplumber                                              systemd
net-print/cups                                                       systemd
net-wireless/bluez                                                   systemd
"""

    _maskFileContent = """
# don't use other init system
sys-apps/sysvinit
sys-apps/s6-linux-init
sys-apps/openrc

# mask all openrc thing
sys-apps/systemd-utils
sys-fs/udev-init-scripts

# they are deprecated by systemd-udevd
sys-fs/udev
sys-fs/eudev

# inetd is deprecated by systemd socket activation
virtual/inetd

# it depends on sys-apps/sysvinit
gui-libs/display-manager-init
"""


class UseVT:
    pass


class NotUseVT:
    # makes userspace be ready for CONFIG_VT=n, we don't manipulate kernel config file

    def update_target_settings(self, target_settings):
        assert "10-no-vt" not in target_settings.install_mask_files

        target_settings.install_mask_files["10-no-vt"] = {
            "sys-apps/systemd": [
                "*vconsole*",
                "*getty*",
                "*autovt*",
                "/etc/systemd/system/getty.target.wants",
            ],
        }

        target_settings.repo_postsync_patch_directories.append("kill-config-vt")


class NotUseDeprecatedPackagesAndFunctions:

    def update_target_settings(self, target_settings):
        assert "10-no-deprecated" not in target_settings.pkg_use_files
        assert "10-no-deprecated" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-no-deprecated"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-no-deprecated"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# disable deprecated functions
*/*                             -deprecated
*/*                             -fallback

# media-libs/libquvi depends on dev-lang/lua[deprecated]
*/*                             -quvi

# framebuffer device is deprecated by DRM
*/*                             -fbdev

# "wpa_supplicant" is deprecated by "iwd", "nss" is deprecated by "gnutls", "wext" is deprecated
net-misc/networkmanager         iwd gnutls -nss -wext

# don't use python2.x
*/*                             -python_targets_python2_7
*/*                             -python_single_target_python2_7

# select between gtk2 and gtk3
*/*                             -gtk2
net-misc/spice-gtk              gtk3

# select between qt4, qt5 and qt6
*/*                             -qt4 qt5
media-video/smplayer            qt5
net-analyzer/wireshark          qt5
net-p2p/bitcoin-qt              qt5
"""

    _maskFileContent = """
# don't use python2.x
<dev-lang/python-3.0.0

# deprecated gnome libs
gnome-base/gconf

# app-cdr/mirage2iso deprecates the following packages
app-cdr/bchunk
app-cdr/ccd2iso
app-cdr/nrg2iso

# not active developed and "equery hasuse -p" can do its job
app-portage/euses

# these packages depends on dev-lang/lua[deprecated]
media-libs/libquvi
media-libs/libquvi-scripts

# FUSE2 is deprecated
#sys-fs/fuse:0              FIXME

# replaced by net-wireless/iwd
net-wireless/wpa_supplicant

# libstdc++ is integrated in gcc
sys-libs/libstdc++-v3

# modern laptop uses SSD, so it is deprecated?
app-laptop/laptop-mode-tools

# replaced by games-emulation/dosbox-staging
games-emulation/dosbox

# dev-db/mariadb deprecates dev-db/mysql
dev-db/mysql

# deprecated by dev-libs/rocm-opencl-runtime
dev-libs/amdgpu-pro-opencl

# zoneinfo in python standard library deprecates these since python3.9
#dev-python/pytz                                                                   # FIXME
dev-python/pytzdata

# replaced by net-vpn/i2pd
acct-user/i2p
acct-group/i2p
net-vpn/i2p

# why application relies on old version electron?
<dev-util/electon-6.0.0

# why use the old version openssl?
<dev-libs/openssl-3.0.0
"""


class AcceptAllLicenses:

    def update_target_settings(self, target_settings):
        assert len(target_settings.pkg_license) == 0 and len(target_settings.pkg_license_files) == 0
        target_settings.pkg_license["*/*"] = "*"


class DesktopEnvironmentNeutral:

    def update_target_settings(self, target_settings):
        assert "10-desktop-environment-neutral" not in target_settings.pkg_use_files
        assert "10-desktop-environment-neutral" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-desktop-environment-neutral"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-desktop-environment-neutral"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# disable DE related flags as much as possible
*/*                                                                                                       -gnome -kde

# use gnome-base/gsettings-desktop-schemas, which is a good work of gnome, all DEs should accept it
media-libs/libcanberra                                                                                     gnome

# don't use "XDG user dir", for example ~/Desktop or ~/Downloads
dev-perl/File-HomeDir                                                                                      -xdg
"""

    _maskFileContent = """
# we don't use "XDG user dir", for example ~/Desktop or ~/Downloads
x11-misc/xdg-user-dirs
"""


class UseCapability:

    def update_target_settings(self, target_settings):
        assert "10-capability" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-capability"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# don't enable caps globally, at least sys-auth/pambase, sys-apps/smartmontools has some complexity with it
app-crypt/pinentry                                                                                              caps
app-misc/pax-utils                                                                                              caps
net-misc/iputils                                                                                                caps
sys-apps/coreutils                                                                                              caps
sys-apps/iproute2                                                                                               caps
sys-apps/util-linux                                                                                             caps
sys-libs/basu                                                                                                   caps
sys-libs/glibc                                                                                                  caps
"""


class UseGnomeKeyring:

    def update_target_settings(self, target_settings):
        assert "10-gnome-keyring" not in target_settings.pkg_use_files
        assert "10-gnome-keyring" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-gnome-keyring"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-gnome-keyring"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# don't enable gnome-keyring globally, at least sys-auth/pambase has some complexity with it
app-crypt/pinentry                                                                                gnome-keyring
app-text/evince                                                                                   gnome-keyring
dev-vcs/git                                                                                       gnome-keyring
dev-vcs/subversion                                                                                gnome-keyring
gnome-base/gvfs                                                                                   gnome-keyring
net-libs/webkit-gtk                                                                               gnome-keyring
x11-libs/wxGTK                                                                                    gnome-keyring
"""

    _maskFileContent = """
# we use app-admin/gnome-keyring
app-admin/keepassxc
"""


class UseKeePassXc:

    def update_target_settings(self, target_settings):
        assert "10-keepassxc" not in target_settings.pkg_use_files
        assert "10-keepassxc" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-keepassxc"] = UseGnomeKeyring._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-keepassxc"] = self._maskFileContent.strip("\n") + "\n"

        # FIXME: keepassxc has no pam integration?
        assert False

    _maskFileContent = """
# we use app-admin/keepassxc
app-admin/gnome-keyring
"""


class UseIbus:

    def update_target_settings(self, target_settings, for_wayland, for_x11):
        assert "10-ibus" not in target_settings.pkg_use_files
        assert "10-ibus" not in target_settings.pkg_mask_files

        assert for_wayland and not for_x11

        target_settings.pkg_use_files["10-ibus"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-ibus"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# no need to use functions other than wayland integration
app-i18n/ibus                                                      -X -gtk2 -gtk3 -gtk4
"""

    _maskFileContent = """
# we use app-i18n/ibus
app-i18n/*fcitx*
"""


class UseFcitx:

    def update_target_settings(self, target_settings, for_wayland, for_x11):
        assert "10-fcitx" not in target_settings.pkg_use_files
        assert "10-fcitx" not in target_settings.pkg_mask_files

        assert for_wayland and not for_x11

        target_settings.pkg_use_files["10-fcitx"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-fcitx"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# no need to use functions other than wayland integration?
app-i18n/fcitx                                                     -X
app-i18n/fcitx-qt                                                  -qt5 qt6
app-i18n/fcitx-gtk                                                 -gtk2 gtk3 gtk4
app-i18n/fcitx-chinese-addons                                      -qt5 qt6
"""

    _maskFileContent = """
# we use app-i18n/fcitx
app-i18n/ibus
app-i18n/ibus-*

# don't use old fcitx version anymore
<app-i18n/fcitx-5.0.0
"""


class PreferWget2:

    def update_target_settings(self, target_settings):
        assert "10-prefer-wget2" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-prefer-wget2"] = self._maskFileContent.strip("\n") + "\n"

    _maskFileContent = """
# we use net-misc/wget2
net-misc/wget
"""


class PreferLibtorrentRasterbar:

    def update_target_settings(self, target_settings):
        assert "10-prefer-libtorrent-rasterbar" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-prefer-libtorrent-rasterbar"] = self._maskFileContent.strip("\n") + "\n"

    _maskFileContent = """
# we use net-libs/libtorrent-rasterbar
net-libs/libtorrent
"""


class PreferPythonMagic:

    def update_target_settings(self, target_settings):
        assert "10-prefer-python-magic" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-prefer-python-magic"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# use dev-python/python-magic instead
sys-apps/file       -python
"""


class PreferGnuAndGpl:

    def update_target_settings(self, target_settings):
        assert "10-prefer-gnu-and-gpl" not in target_settings.pkg_use_files
        assert "10-prefer-gnu-and-gpl" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-prefer-gnu-and-gpl"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-prefer-gnu-and-gpl"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# no need to use dev-libs/libedit
*/*         readline

# use sys-libs/ncurses, why sys-libs/slang?
*/*         -slang
"""

    _maskFileContent = """
# use free java implementation
dev-java/oracle-jdk-bin
dev-java/oracle-jre-bin
dev-java/ibm-jdk-bin
dev-java/ibm-jre-bin
"""


class PreferBinaryPackage:

    def update_target_settings(self, target_settings):
        assert "10-prefer-binary-package" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-prefer-binary-package"] = self._maskFileContent.strip("\n") + "\n"

    _maskFileContent = """
# we prefer dev-lang/rust-bin
dev-lang/rust

# we prefer sys-firmware/edk2-ovmf-bin
sys-firmware/edk2-ovmf
"""


class PreferSourcePackage:

    def update_target_settings(self, target_settings):
        assert "10-prefer-source-package" not in target_settings.pkg_mask_files

        target_settings.pkg_mask_files["10-prefer-source-package"] = self._maskFileContent.strip("\n") + "\n"

    _maskFileContent = """
# we prefer dev-lang/rust
dev-lang/rust-bin

# we prefer sys-firmware/edk2-ovmf
sys-firmware/edk2-ovmf-bin
"""


class PreferSystemComponent:

    def update_target_settings(self, target_settings):
        assert "10-prefer-system-component" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-prefer-system-component"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# don't use package built-in component
app-editors/vscode                             system-electron system-ripgrep
net-libs/nodejs                                system-icu
net-im/zoom                                    -bundled-qt
"""


class GettyAutoLogin:

    def get_custom_action(self):
        s = PlacingFilesScript()
        s.append_file("/etc/systemd/system/getty@.service.d/getty-autologin.conf",
                      self._fileContent.strip("\n") + "\n")  # remove all redundant carrage returns)
        return SimpleCustomAction(s, after=["init_confdir", "create_overlays", "update_world", "install_kernel", "enable_services"])

    _fileContent = """
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
"""


class SupportAllVideoFormat:

    def update_target_settings(self, target_settings):
        assert "10-video-formats" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-video-formats"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# video formats
*/*                 bluray dv dvb dvd mms mpeg mpeg2 openh264 theora vcd x264 x265 xvid vpx
"""


class SupportAllAudioFormat:

    def update_target_settings(self, target_settings):
        assert "10-audio-formats" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-audio-formats"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# audio formats
*/*                 a52 aac airplay alac aptx cdda dts flac lame ldac mad mp3 musepack ogg opus sndfile speex vorbis wavpack
"""


class SupportAllImageFormat:

    def update_target_settings(self, target_settings):
        assert "10-image-formats" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-image-formats"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# image formats
*/*                 apng exif gif jpeg jpeg2k jpegxl mng openexr png svg tiff webp wmf xpm
"""


class SupportAllDocumentFormat:

    def update_target_settings(self, target_settings):
        assert "10-document-formats" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-document-formats"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# document formats
*/*                 djvu xps
"""


class SupportAllCompressFormat:

    def update_target_settings(self, target_settings):
        assert "10-compress-formats" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-compress-formats"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# compress formats
*/*                 7zip bzip2 gzip lz4 lzma lzo szip xz zstd
"""


class SupportAllGraphicsApi:

    def update_target_settings(self, target_settings):
        assert "10-graphics-api" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-graphics-api"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# graphics api
*/*                                                                                  egl eglfs gles gles2 gles3 vaapi vulkan zink

# we prefer gles, but we also enable opengl when it doesn't conflict with gles
*/*                                                                                  -opengl
app-emulation/qemu                                                                   opengl
app-emulation/wine-vanilla                                                           opengl
app-emulation/wine-staging                                                           opengl
dev-lang/fbc                                                                         opengl
dev-qt/qtbase                                                                        opengl
dev-qt/qtdeclarative                                                                 opengl
dev-qt/qttools                                                                       opengl
games-emulation/dosbox-staging                                                       opengl
games-engines/scummvm                                                                opengl
"""


class SupportAllTermType:

    def update_world_set(self, world_set):
        world_set.add("sys-libs/ncurses")                  # FIXME: should ensure USE flag installs all terminfo
        world_set.add("x11-terms/kitty-terminfo")


class DisablePcSpeaker:

    def get_custom_action(self):
        return SimpleCustomAction(OneLinerScript('echo "blacklist pcspkr" > /etc/modprobe.d/disable-pc-speaker.conf'),
                                  after=["init_confdir", "create_overlays", "update_world", "install_kernel", "enable_services"])


class DisableFstab:

    def update_target_settings(self, target_settings):
        target_settings.repo_postsync_patch_directories.append("remove-fstab")


class RemoveDoc:

    def update_target_settings(self, target_settings):
        assert "10-remove-doc" not in target_settings.pkg_use_files
        assert "10-remove-doc" not in target_settings.install_mask_files

        target_settings.pkg_use_files["10-remove-doc"] = self._useFileContent.strip("\n") + "\n"

        target_settings.install_mask_files["10-remove-doc"] = {
            "*/*": [
                "/usr/share/doc",
                "/usr/share/info",
                "/usr/share/man",
            ],
        }

    _useFileContent = """
# remove all document
*/*                     -doc
"""


class PreferWayland:

    def __init__(self, xwayland=True):
        self._xwayland = xwayland

    def update_target_settings(self, target_settings):
        assert "10-prefer-wayland" not in target_settings.pkg_use_files
        assert "10-prefer-wayland" not in target_settings.pkg_mask_files

        buf = self._useFileContent.strip("\n") + "\n"
        if self._xwayland:
            buf += self._xwaylandContent.strip("\n") + "\n"
        target_settings.pkg_use_files["10-prefer-wayland"] = buf

        target_settings.pkg_mask_files["10-prefer-wayland"] = self._maskFileContent.strip("\n") + "\n"

        target_settings.repo_postsync_patch_directories.append("use-wayland")
        if not self._xwayland:
            target_settings.repo_postsync_patch_directories.append("remove-x11")

    _useFileContent = """
# we use wayland
*/*                                           wayland
*/*                                           -X
*/*                                           INPUT_DEVICES: -* libinput
"""

    _xwaylandContent = """
# of course, we also use X when we have to
app-emulation/wine-vanilla                    X                               # wine has no wayland support, it has to use Xwayland
app-emulation/wine-staging                    X
dev-util/electron                             X -wayland                      # electron wayland support needs ozone which is broken now
gui-wm/wayfire                                X                               # enable Xwayland
app-misc/ddcutil                              X                               # drm needs X?

# keep X minimal
x11-base/xorg-server                          -elogind                        # why it enables by default?
x11-base/xorg-server						  -suid -udev -xorg
"""

    _maskFileContent = """
# vdpau is from NVIDIA (it does not support pure wayland yet), use vaapi is enough
x11-libs/libvdpau
x11-libs/libva-vdpau-driver
x11-misc/vdpauinfo
"""


class PreferPipewire:

    def __init__(self, with_pulseaudio=True, with_jack=True, with_direct_alsa=True):
        assert with_pulseaudio                     # FIXME
        assert not with_jack                       # FIXME
        assert with_direct_alsa                    # FIXME

        self._pulseaudio = with_pulseaudio
        self._jack = with_jack
        self._alsa = with_direct_alsa

    def update_target_settings(self, target_settings):
        assert "10-prefer-pipewire" not in target_settings.pkg_use_files
        assert "10-prefer-pipewire" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-prefer-pipewire"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-prefer-pipewire"] = self._maskFileContent.strip("\n") + "\n"

    _useFileContent = """
# prefered sound route: 1. pipewire -> alsa
#                       2. gstreamer -> pipewire -> alsa
#                       3. openal -> pipewire -> alsa
#                       4. fluidsynth -> pipewire -> alsa
#                       5. pulseaudio -> pipewire -> alsa (bad)
#                       6. jack -> pipewire -> alsa (forbidden)
#                       7. alsa -> pipewire -> alsa (forbidden)
#                       8. alsa (forbidden)
app-emulation/qemu                                          -alsa pipewire                # sound route 1
app-emulation/spice                                         gstreamer                     # sound route 2
app-emulation/wine-vanilla                                  -alsa pulseaudio              # sound route 5 (bad), gstreamer support in wine is not what we image
app-emulation/wine-staging                                  -alsa pulseaudio              # sound route 5 (bad), gstreamer support in wine is not what we image
app-emulation/virtualbox                                    -alsa pulseaudio              # sound route 5 (bad)
games-emulation/dosbox-staging                              -alsa fluidsynth              # sound route 4
games-engines/scummvm                                       -alsa fluidsynth              # sound route 4
games-fps/serioussam-tfe                                    -alsa pipewire                # sound route 1
games-fps/serioussam-tfe-vk                                 -alsa pipewire                # sound route 1
games-fps/serioussam-tse                                    -alsa pipewire                # sound route 1
games-fps/serioussam-tse-vk                                 -alsa pipewire                # sound route 1
gui-libs/gtk                                                gstreamer                     # sound route 2
media-gfx/blender                                           openal                        # sound route 3
media-libs/libmikmod                                        -alsa openal                  # sound route 3
media-libs/libsdl                                           -alsa                         # sound route 1, support pipewire through media-libs/libsdl2
media-libs/libsdl2                                          -alsa pipewire                # sound route 1
media-libs/openal                                           -alsa pipewire                # sound route 1
media-libs/mediastreamer2                                   -alsa pulseaudio              # sound route 5 (bad)
media-sound/fluidsynth                                      -alsa pipewire                # sound route 1
media-sound/lmms                                            -alsa pulseaudio              # sound route 5 (bad)
media-sound/mpg123                                          -alsa pulseaudio              # sound route 5 (bad)
media-sound/sonic-visualiser                                pulseaudio                    # sound route 5 (bad)
media-sound/wildmidi                                        -alsa openal                  # sound route 3
media-video/mpv                                             -alsa pipewire                # sound route 1
net-im/zoom                                                 pulseaudio                    # sound route 5 (bad), doesn't support alsa, gstreamer and pipewire
net-misc/freerdp                                            -alsa gstreamer pulseaudio    # sound route 5 (bad), strange, it has USE flag alsa, ffmepg, gstreamer and pulseaudio. It seems disable both alsa and pulseaudio would make it route to OSS.
net-wireless/gqrx                                           pulseaudio                    # sound route 5 (bad)
media-libs/libcanberra                                      -alsa gstreamer               # sound route 2
media-sound/spotify                                         pulseaudio                    # sound route 5 (bad), doesn't support alsa, gstreamer and pipewire
www-client/firefox-bin                                      -alsa pulseaudio              # sound route 5 (bad), doesn't support alsa, gstreamer and pipewire, it's alsa flag is for medis-sound/apulse
www-client/chromium                                         pulseaudio                    # sound route 5 (bad), doesn't support alsa, gstreamer and pipewire
x11-libs/wxGTK                                              gstreamer                     # sound route 2

# disable sound route 7
media-video/pipewire                                        -pipewire-alsa

# keep pulseaudio minimal
*/*                                                         -pulseaudio         # note: */* USE flag has a lower priority than package specific USE flags above
media-sound/pulseaudio                                      -*
"""

    _maskFileContent = """
# we prefer the following paradim:
#   App --> Pipewire --> ALSA
#              |
#              +-------> Bluetooth
media-sound/bluez-alsa

# use pipewire instead of pulseaudio (media-sound/pulseaudio is still needed, see package.use)
media-plugins/gst-plugins-pulse
media-sound/apulse

# use pipewire, only limited package can access camera directly
media-plugins/gst-plugins-v4l2

# use pipewire, instead of jack
virtual/jack
media-sound/jack2
media-sound/jack-audio-connection-kit

# don't redirect alsa to sound servers
media-plugins/alsa-plugins
media-sound/alsa-tools
media-sound/alsa-utils

# packages only support sound route 6, 7, 8
media-sound/audacity                                        # sound route 7
media-sound/moc                                             # sound route 7
media-sound/musescore                                       # sound route 6
media-sound/timidity++                                      # sound route 6
media-sound/vkeybd                                          # sound route 7
"""


class PreferBlockDeviceUAccess:

    def update_target_settings(self, target_settings):
        assert "10-prefer-block-device-uaccess" not in target_settings.pkg_use_files
        assert "10-prefer-block-device-uaccess" not in target_settings.pkg_mask_files

        target_settings.pkg_use_files["10-prefer-block-device-uaccess"] = self._useFileContent.strip("\n") + "\n"
        target_settings.pkg_mask_files["10-prefer-block-device-uaccess"] = self._maskFileContent.strip("\n") + "\n"

        target_settings.repo_postsync_patch_directories.append("block-device-uaccess")

    _useFileContent = """
*/*     -udisks
"""

    _maskFileContent = """
sys-fs/udisks
"""
