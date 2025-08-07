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

from ._common import FixBugs

from ._common import UsePortage

from ._kernel import UseGenkernel
from ._kernel import UseDistKernel
from ._kernel import UseBbki

from ._common import UseOpenrc
from ._common import UseSystemd

from ._common import UseVT
from ._common import DontUseVT

from ._common import UseGnomeKeyring
from ._common import UseKeePassXc

from ._common import UseIbus
from ._common import UseFcitx

from ._common import AcceptAllLicenses
from ._common import DontUseDeprecatedPackagesAndFunctions
from ._common import DesktopEnvironmentNeutral
from ._common import UseCapability

from ._common import PreferGnuAndGpl
from ._common import PreferBinaryPackage
from ._common import PreferSourcePackage
from ._common import PreferSystemComponent
from ._common import PreferWayland
from ._common import PreferPipewire
from ._common import PreferBlockDeviceUAccess
from ._common import PreferWget2
from ._common import PreferLibtorrentRasterbar
from ._common import PreferPythonMagic

from ._common import DisablePcSpeaker
from ._common import DisableFstab
from ._common import DisableUtmp
from ._common import DisableWtmpBtmpLastlog
from ._common import DontUsePypy
from ._common import RemoveDoc

from ._common import SupportAllVideoFormat
from ._common import SupportAllAudioFormat
from ._common import SupportAllImageFormat
from ._common import SupportAllDocumentFormat
from ._common import SupportAllCompressFormat
from ._common import SupportAllHashFormat
from ._common import SupportAllGraphicsApi
from ._common import SupportAllTermType

from ._common import GettyAutoLogin

from ._tailor import TailorBaselayout
from ._tailor import TailorUtilLinux
from ._tailor import TailorSystemd
from ._tailor import TailorShadow
from ._tailor import TailorPam
from ._tailor import TailorAvahi
from ._tailor import TailorEselect
from ._tailor import TailorGit
from ._tailor import TailorWget
from ._tailor import TailorRsync
from ._tailor import TailorLmSensors
from ._tailor import TailorQemu
from ._tailor import TailorWine

from ._pam import PamSuWheelOk

from ._mirror import UseGithubMirror
from ._mirror import UseGogMirror
from ._mirror import UseHbMirror
from ._mirror import UseItchMirror
from ._mirror import UseHuggingFaceMirror

from ._new_use import AddSystemServiceUseFlag

from ._priviledge import DontUsePolicyKit
from ._priviledge import DontUseSudo
from ._priviledge import UniversalWheelGroup

from ._application import UseAllQemuTargets
from ._application import UseAllLlvmTargets
from ._application import DontUseLogrotate

from ._application import MemTest
from ._application import SshServer
from ._application import Chrony
from ._application import NetworkManager
from ._application import Kmscon

from ._application import UseZeroConf
from ._application import DontUseZeroConf

from ._application import UseBluetooth
from ._application import DontUseBluetooth

from ._application import UsePrinting
from ._application import DontUsePrinting


__all__ = [
    "FixBugs",
    "UsePortage",
    "UseGenkernel",
    "UseDistKernel",
    "UseBbki",
    "UseOpenrc",
    "UseSystemd",
    "UseVT",
    "DontUseVT",
    "UseGnomeKeyring",
    "UseKeePassXc",
    "UseIbus",
    "UseFcitx",
    "AcceptAllLicenses",
    "DontUseDeprecatedPackagesAndFunctions",
    "DesktopEnvironmentNeutral",
    "UseCapability",
    "PreferGnuAndGpl",
    "PreferBinaryPackage",
    "PreferSourcePackage",
    "PreferSystemComponent",
    "PreferWayland",
    "PreferPipewire",
    "PreferBlockDeviceUAccess",
    "PreferWget2",
    "PreferLibtorrentRasterbar",
    "PreferPythonMagic",
    "DisablePcSpeaker",
    "DisableFstab",
    "DontUsePypy",
    "RemoveDoc",
    "SupportAllVideoFormat",
    "SupportAllAudioFormat",
    "SupportAllImageFormat",
    "SupportAllDocumentFormat",
    "SupportAllCompressFormat",
    "SupportAllHashFormat",
    "SupportAllGraphicsApi",
    "SupportAllTermType",
    "GettyAutoLogin",
    "TailorBaselayout",
    "TailorUtilLinux",
    "TailorSystemd",
    "TailorShadow",
    "TailorPam",
    "TailorAvahi",
    "TailorEselect",
    "TailorGit",
    "TailorWget",
    "TailorRsync",
    "TailorLmSensors",
    "TailorQemu",
    "TailorWine",
    "PamSuWheelOk",
    "UseGithubMirror",
    "UseGogMirror",
    "UseHbMirror",
    "UseItchMirror",
    "UseHuggingFaceMirror",
    "AddSystemServiceUseFlag",
    "DontUsePolicyKit",
    "DontUseSudo",
    "UniversalWheelGroup",
    "UseAllQemuTargets",
    "UseAllLlvmTargets",
    "DontUseLogrotate",
    "MemTest",
    "SshServer",
    "Chrony",
    "NetworkManager",
    "Kmscon",
    "UseZeroConf",
    "DontUseZeroConf",
    "UseBluetooth",
    "DontUseBluetooth",
    "UsePrinting",
    "DontUsePrinting",
]
