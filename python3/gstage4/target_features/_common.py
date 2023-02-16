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


class UseFakeKernel:

    def update_target_settings(self, target_settings):
        target_settings.kernel_manager = "fake"


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

    def __init__(self, module_flags={}):
        self._mFlagDict = module_flags

    def update_target_settings(self, target_settings):
        assert "10-systemd" not in target_settings.pkg_use_files
        assert "10-systemd" not in target_settings.pkg_mask_files
        assert "10-systemd" not in target_settings.install_mask_files

        target_settings.service_manager = "systemd"

        target_settings.pkg_use_files["10-systemd"] = self._useFileContent.strip("\n") + "\n"

        target_settings.pkg_mask_files["10-systemd"] = self._maskFileContent.strip("\n") + "\n"

        if True:
            td = {}
            flagRecord = set()

            def _updateDict(src):
                for k, v in src.items():
                    if k not in td:
                        td[k] = v
                    td[k] += v

            def _flagExec(flag_name, disable_func=None, exclude_func=None):
                ret = self._mFlagDict.get(flag_name, None)
                if ret is None:
                    pass
                elif ret == "disable":
                    if disable_func is not None:
                        disable_func()
                    else:
                        assert False
                elif ret == "exclude":
                    if exclude_func is not None:
                        exclude_func()
                    else:
                        assert False
                else:
                    assert False
                if True:
                    assert flag_name not in flagRecord
                    flagRecord.add(flag_name)

            _flagExec("systemd-boot", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*bootctl*",
                    "*/systemd-boot.7.bz2",
                    "*systemd-boot-system-token*",
                ],
            }))
            _flagExec("systemd-coredump", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*coredump*",
                ],
            }))
            _flagExec("systemd-hostnamed", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*hostname1*",
                    "*hostnamed*",
                    "*hostnamectl*",
                ],
            }))
            _flagExec("systemd-firstboot", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*firstboot*",
                ],
            }))
            _flagExec("systemd-kexec", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*kexec*",
                ],
            }))
            _flagExec("systemd-localed", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*locale1*",
                    "*localed*",
                    "*localectl*",
                ],
            }))
            _flagExec("systemd-machined", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*machine*",
                    "*nspawn*",
                    "*detect-virt*",
                    "*exit.target",
                    "*systemd-exit.service",
                ],
            }))
            _flagExec("systemd-networkd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*network*",
                    "/lib/systemd/network*",
                    "/etc/systemd/network",
                ],
            }))
            _flagExec("systemd-portabled", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*portable*",
                    "/lib/systemd/portable",
                ],
            }))
            _flagExec("systemd-oomd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*oom1*",
                    "*oomd*",
                    "*oomctl",
                ],
            }))
            _flagExec("systemd-pstore", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*pstore*",
                ],
            }))
            _flagExec("systemd-repart", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*repart*",
                ],
            }))
            _flagExec("systemd-resolvd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*resolv*",
                ],
            }))
            _flagExec("systemd-sysext", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*sysext*",
                ],
            }))
            _flagExec("systemd-sysupdate", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*sysupdate*",
                ],
            }))
            _flagExec("systemd-sysusers", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*systemd-sysusers*",
                ],
            }))
            _flagExec("systemd-timedated", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*timedate*",
                ],
            }))
            _flagExec("systemd-timesyncd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*timesync*",
                    "*ntp*",
                    "/lib/systemd/ntp-units.d*",
                ],
            }))
            _flagExec("systemd-update", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*system-update*",
                    "*update-done*",
                ],
            }))
            _flagExec("systemd-userdbd", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*userdb*",
                ],
            }))
            _flagExec("fstab", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*fstab*",
                ],
            }))
            _flagExec("fs-operations", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*makefs*",
                    "*growfs*",
                    "*mkswap*",
                ],
            }))
            _flagExec("ldconfig.service", exclude_func=lambda: _updateDict({
                "sys-apps/systemd": [
                    "*ldconfig*",
                ],
            }))
            _flagExec("sysvinit", exclude_func=lambda: _updateDict({
                "*/*": [
                    "/etc/init.d",
                    "/etc/conf.d",
                    "/etc/rc.d",
                ],
                "sys-apps/systemd": [
                    "*initctl*",
                    "*runlevel*",
                    "*systemd-sysv-generator*",
                    "*rc-local*",
                ],
            }))
            assert len(set(self._mFlagDict.keys()) - flagRecord) == 0
            if len(td) > 0:
                target_settings.install_mask_files["10-systemd"] = td

    def update_world_set(self, world_set):
        world_set.add("sys-apps/systemd")

    _useFileContent = """
# so that we can use systemd-udev
virtual/libudev                        systemd
"""

    _maskFileContent = """
# don't use other init system
sys-apps/sysvinit
sys-apps/s6-linux-init
sys-apps/openrc

# they are deprecated by systemd-udevd
sys-fs/udev
sys-fs/eudev

# inetd is deprecated by systemd socket activation
virtual/inetd
"""


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

# select between qt4 and qt5
*/*                             -qt4
media-video/smplayer            qt5
net-analyzer/wireshark          qt5
net-p2p/bitcoin-qt              qt5
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

# deprecated by dev-libs/rocm-opencl-runtime
dev-libs/amdgpu-pro-opencl

# zoninfo in python standard library deprecates these since python3.9
#dev-python/pytz                                                                   # FIXME
dev-python/pytzdata

# replaced by net-vpn/i2pd
acct-user/i2p
acct-group/i2p
net-vpn/i2p

# why application relies on old version electon?
<dev-util/electon-6.0.0

# why use the old version openssl?
<dev-libs/openssl-3.0.0
"""


class AcceptAllLicenses:

    def update_target_settings(self, target_settings):
        assert len(target_settings.pkg_license) == 0 and len(target_settings.pkg_license_files) == 0
        target_settings.pkg_license["*/*"] = "*"


class UsrMerge:

    def __init__(self, archLinuxStyle=False):
        self._mergeSbin = archLinuxStyle

    def update_target_settings(self, target_settings):
        if "split-usr" not in target_settings.use_mask:
            target_settings.use_mask.append("split-usr")

    def get_custom_action(self):
        buf = self._scriptFileContent
        if self._mergeSbin:
            buf += self._scriptMergeSbin
        return SimpleCustomAction(ScriptFromBuffer(buf),
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
"""

    _scriptMergeSbin = """
# merge /usr/sbin into /usr/bin
if True:
    subprocess.run("cp -a --remove-destination /usr/sbin/* /usr/bin", shell=True)
    shutil.rmtree("/usr/sbin")
    os.symlink("bin", "/usr/sbin")
"""


class DesktopEnvironmentNeutral:

    def update_target_settings(self, target_settings):
        assert "10-de-neutral" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-de-neutral"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# disable DE related flags as much as possible
*/*                                                                                                       -gnome -kde

# use gnome-base/gsettings-desktop-schemas, which is a good work of gnome, all DEs should accept it
media-libs/libcanberra                                                                                     gnome
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
*/*                 apng exif gif jpeg jpeg2k mng png svg tiff webp wmf
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


class SupportAllGraphicsApi:

    def update_target_settings(self, target_settings):
        assert "10-graphics-api" not in target_settings.pkg_use_files

        target_settings.pkg_use_files["10-graphics-api"] = self._useFileContent.strip("\n") + "\n"

    _useFileContent = """
# graphics api
*/*                                                                                  egl eglfs gles2 gles2-only gles3 vaapi vulkan zink

# we prefer gles, but we also enable opengl when it doesn't conflict with gles
app-emulation/qemu                                                                   opengl
games-emulation/dosbox-staging                                                       opengl
games-engines/scummvm                                                                opengl
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
        assert "10-prefer-wayland" not in target_settings.pkg_mask_files

        buf = self._useFileContent.strip("\n") + "\n"
        if self._xwayland:
            buf += self._xwaylandContent.strip("\n") + "\n"
        target_settings.pkg_use_files["10-prefer-wayland"] = buf

        target_settings.pkg_mask_files["10-prefer-wayland"] = self._maskFileContent.strip("\n") + "\n"

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
#                       4. alsa (bad)
#                       5. pulseaudio -> alsa (bad)
app-emulation/spice                                         gstreamer
app-emulation/wine-vanilla                                  alsa            # gstreamer support in wine is not an alsa replacement, doesn't support pipewire
app-emulation/wine-staging                                  alsa            # gstreamer support in wine is not an alsa replacement, doesn't support pipewire
app-emulation/virtualbox                                    alsa            # does not and should not support gstreamer?
games-emulation/dosbox-staging                              alsa            # doesn't support gstreamer and pipewire
games-engines/scummvm                                       alsa            # doesn't support gstreamer and pipewire
gui-libs/gtk                                                gstreamer
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
media-libs/libcanberra                                      gstreamer
media-sound/spotify                                         pulseaudio      # doesn't support alsa, gstreamer and pipewire
x11-libs/wxGTK                                              gstreamer

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

# don't redirect alsa to sound servers
#media-plugins/alsa-plugins                                                                                                # FIXME
#media-sound/alsa-tools                                                                                                    # FIXME
#media-sound/alsa-utils                                                                                                    # FIXME
"""
