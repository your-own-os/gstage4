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
from ..scripts import ScriptFromBuffer
from ..scripts import PlacingFilesScript


class UsePortage:

    def update_target_settings(self, target_settings):
        target_settings.package_manager = "portage"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/portage")


class UseGenkernel:

    def __init__(self, kernel):
        self._kernel = kernel

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "genkernel"

    def update_world_set(self, world_set):
        world_set.add("sys-kernel/%s" % (self._kernel))
        world_set.add("sys-kernel/genkernel")
        world_set.add("sys-devel/bc")           # kernel build script needs it


class UseBinaryKernel:

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "binary-kernel"

    def update_world_set(self, world_set):
        world_set.add("sys-kernel/gentoo-kernel-bin")


class UseFakeKernel:

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "fake"


class UseOpenrc:

    def update_target_settings(self, target_settings):
        target_settings.service_manager = "openrc"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/openrc")


class UseSystemd:

    def update_target_settings(self, target_settings):
        target_settings.service_manager = "systemd"

    def update_world_set(self, world_set):
        world_set.add("sys-apps/systemd")


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

# media-libs/libdv depends on libsdl-version-1, which is deprecated
*/*                             -dv

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

# select between qt4 and qt5
*/*                             -qt4
media-video/smplayer            qt5
net-analyzer/wireshark          qt5
net-p2p/bitcoin-qt              qt5

# replaced by net-vpn/i2pd
acct-user/i2p
acct-group/i2p
net-vpn/i2p
"""

    _maskFileContent = """
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
sys-fs/fuse:0

# replaced by net-wireless/iwd
net-wireless/wpa_supplicant

# libstdc++ is integrated in gcc
sys-libs/libstdc++-v3

# too old
sys-apps/sysvinit

# deprecated by dev-libs/rocm-opencl-runtime
dev-libs/amdgpu-pro-opencl

# zoninfo in python standard library deprecates these since python 3.9
#dev-python/pytz                                                                   # FIXME
dev-python/pytzdata
"""


class UsrMerge:

    def update_target_settings(self, target_settings):
        if "split-usr" not in target_settings.use_mask:
            target_settings.use_mask.append("split-usr")

    def get_custom_action(self):
        return SimpleCustomAction(ScriptFromBuffer(self._scriptFileContent),
                                  after=["init_confdir", "create_overlays"],
                                  before=["update_world"])

        # UNINSTALL_IGNORE="/bin /lib /lib64 /sbin /usr/sbin"

    _scriptFileContent = """
#!/usr/bin/python

import os
import glob
import shutil
import subprocess

# fix /bin/awk
os.unlink("/bin/awk")

# copy root directories to /usr counterparts and create
# the /usr merge compatibility symlinks
for dir in ["/bin", "/sbin"] + glob.glob("/lib*"):
    subprocess.run("cp -a --remove-destination %s/* /usr/%s" % (dir, dir[1:]), shell=True)
    shutil.rmtree(dir)
    os.symlink("usr/%s" % (dir[1:]), dir)

# merge /usr/sbin into /usr/bin
if True:
    subprocess.run("cp -a --remove-destination /usr/sbin/* /usr/bin", shell=True)
    shutil.rmtree("/usr/sbin")
    os.symlink("bin", "/usr/sbin")
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
        s.append_dir("/etc")
        s.append_dir("/etc/systemd")
        s.append_dir("/etc/systemd/system")
        s.append_dir("/etc/systemd/system/getty@.service.d")
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
*/*                 bluray dv dvb dvd mms mpeg openh264 theora vcd x264 x265 xvid vpx
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
*/*                 a52 aac airplay alac aptx cdda dts flac lame ldac mad mp3 musepack ogg opus sndfile speex vorbis wavpack
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
*/*                 bzip2 gzip lz4 lzma lzo szip xz
"""


class DisablePcSpeaker:

    def get_custom_action(self):
        return SimpleCustomAction(ScriptFromBuffer(self._scriptFileContent),
                                  after=["init_confdir", "create_overlays", "update_world", "install_kernel", "enable_services"])

    _scriptFileContent = """
#!/bin/sh
echo "blacklist pcspkr" > /etc/modprobe.d/disable-pc-speaker.conf
"""


class PreferWayland:

    def __init__(self, xwayland=True):
        self._xwayland = xwayland

    def update_target_settings(self, target_settings):
        assert "10-prefer-wayland" not in target_settings.pkg_use_files

        buf = self._useFileContent.strip("\n") + "\n"
        if self._xwayland:
            buf += self._xwaylandContent.strip("\n") + "\n"
        target_settings.pkg_use_files["10-prefer-wayland"] = buf

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
x11-base/xorg-server						  -suid -systemd -udev -xorg
"""

    _maskFileContent = """
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
#                       4. alsa (bad)
#                       5. pulseaudio -> alsa (bad)
app-emulation/wine-vanilla                                  alsa            # gstreamer support in wine is not an alsa replacement, doesn't support pipewire
app-emulation/wine-staging                                  alsa            # gstreamer support in wine is not an alsa replacement, doesn't support pipewire
app-emulation/virtualbox                                    alsa            # does not and should not support gstreamer?
games-emulation/dosbox-staging                              alsa            # doesn't support gstreamer and pipewire
media-libs/libmikmod                                        -alsa openal    # doesn't support gstreamer and pipewire
media-libs/libsdl                                           alsa            # doesn't support gstreamer and pipewire
media-libs/libsdl2                                          pipewire
media-libs/mediastreamer2                                   alsa            # doesn't support gstreamer and pipewire
media-sound/audacity                                        alsa            # doesn't support gstreamer and pipewire
media-sound/fluidsynth                                      pipewire
media-sound/lmms                                            alsa            # doesn't support gstreamer and pipewire
media-sound/mpg123                                          alsa            # doesn't support gstreamer and pipewire
media-sound/moc                                             alsa            # doesn't support gstreamer and pipewire
media-sound/musescore                                       alsa            # doesn't support gstreamer and pipewire
media-sound/timidity++                                      alsa            # doesn't support gstreamer and pipewire
media-sound/wildmidi                                        -alsa openal    # doesn't support gstreamer and pipewire
media-sound/vkeybd                                          alsa            # doesn't support gstreamer and pipewire
media-video/mpv                                             -alsa pipewire
net-im/zoom                                                 pulseaudio      # doesn't support alsa, gstreamer and pipewire
net-misc/freerdp                                            pulseaudio      # strange, it has USE flag alsa, ffmepg, gstreamer and pulseaudio. It seems disable alsa+pulseaudio would make it route to OSS.
media-sound/spotify                                         pulseaudio      # doesn't support alsa, gstreamer and pipewire

# keep pulseaudio minimal
*/*                                                         -pulseaudio
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
"""
