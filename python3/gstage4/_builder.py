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


import os
import re
import abc
import glob
import pathlib
from ._util import Util
from ._util import ActionRunner
from ._prototype import SeedStage
from ._prototype import ManualSyncRepository
from ._prototype import EmergeSyncRepository
from ._prototype import ScriptInChroot
from ._errors import SettingsError
from ._errors import BuildError
from ._errors import CustomActionError
from ._settings import Settings
from ._settings import TargetSettings
from ._patcher import RepoPatcher
from ._runner import Runner
from .scripts import ScriptFromBuffer
from .scripts import ScriptInstallPackages
from .scripts import ScriptUpdateWorld


class Builder(ActionRunner):
    """
    This class does all of the chroot setup, copying of files, etc.
    It is the driver class for pretty much everything that gstage4 does.
    """

    def __init__(self, settings, target_settings, work_dir):
        assert Settings.check_object(settings, raise_exception=False)
        assert TargetSettings.check_object(target_settings, raise_exception=False)

        self._s = settings
        if self._s.log_dir is not None:
            os.makedirs(self._s.log_dir, mode=0o750, exist_ok=True)

        self._ts = target_settings
        if self._ts.build_opts.ccache:
            assert self._s.host_ccache_dir is not None
        if len(self._ts.repo_postsync_patch_directories) > 0:
            assert self._s.host_repo_postsync_patch_source_dir is not None

        self._workDirObj = work_dir

        self._actionStorage = {
            "arch": None,                   # target arch
            "repo": None,                   # gentoo repository information
            "overlays": {},                 # overlay information
        }

        actionList = [
            self.action_unpack,
            self.action_create_gentoo_repository,
            self.action_init_confdir,
            self.action_create_overlays,
            self.action_update_world,
            self.action_install_kernel,
            self.action_enable_services,
            self.action_cleanup,
        ]

        def x(self, action_name, action):
            with _MyChrooter(self) as m:
                for s in action.custom_scripts:
                    m.script_exec(s, quiet=self._getQuiet())

        super().__init__(self._workDirObj._persistentStorage, actionList, x, BuildError)

    @property
    def verbose_level(self):
        return self._s.verbose_level

    @ActionRunner.Action()
    def action_unpack(self, seed_stage):
        assert isinstance(seed_stage, SeedStage)
        assert seed_stage.get_arch() == self._ts.arch

        self._workDirObj._saveTargetSettings(self._ts)
        curPath = self._workDirObj.get_latest_action_dirpath()

        seed_stage.unpack(curPath)

        t = TargetFilesAndDirs(curPath)
        t.make_dir_by_hostpath("logdir", exist_ok=True)
        t.make_dir_by_hostpath("distdir", exist_ok=True)
        t.make_dir_by_hostpath("binpkgdir", exist_ok=True)
        if self._ts.build_opts.ccache:
            t.make_dir_by_hostpath("ccachedir")
        with t.open_file_for_write_by_hostpath("world_file") as f:
            f.write("")

        self._actionStorage["arch"] = seed_stage.get_arch()

    @ActionRunner.Action(after=["unpack"])
    def action_create_gentoo_repository(self, repo):
        assert repo.get_name() == "gentoo"

        curPath = self._workDirObj.get_latest_action_dirpath()

        # create repository
        if isinstance(repo, ManualSyncRepository):
            myRepo = _MyRepoUtil.createFromManuSyncRepo(repo, True, curPath)
            repo.sync(os.path.join(curPath, repo.get_datadir_path()[1:]))
        elif isinstance(repo, EmergeSyncRepository):
            myRepo = _MyRepoUtil.createFromEmergeSyncRepo(repo, True, curPath)
            assert myRepo.get_sync_type() == "rsync"
            with _MyChrooter(self) as m:
                m.script_exec(ScriptSync(), quiet=self._getQuiet())
        else:
            assert False

        # patch using host patch-repository.d
        if len(self._ts.repo_postsync_patch_directories) > 0:
            pendingDstDirSet = myRepo.patch([os.path.join(self._s.host_repo_postsync_patch_source_dir, x) for x in self._ts.repo_postsync_patch_directories])
            with _MyChrooter(self) as m:
                # FIXME: it a bit hard to parallelize the following code
                for dstDir in pendingDstDirSet:
                    ebuildDir = os.path.join(myRepo.datadir_path, dstDir)
                    fn = glob.glob(os.path.join(ebuildDir, "*.ebuild"))[0]
                    m.shell_exec("ebuild %s manifest" % (fn))

        self._actionStorage["repo"] = repo

    @ActionRunner.Action(after=["create_gentoo_repository"])
    def action_init_confdir(self):
        curPath = self._workDirObj.get_latest_action_dirpath()

        tp = TargetConfDirParser(curPath)
        tw = TargetConfDirWriter(self._s, self._ts, curPath)

        # set profile
        if self._ts.profile is not None:                                            # using profile specified by caller
            with _MyChrooter(self) as m:
                m.shell_call("", "eselect profile set %s" % (self._ts.profile))
        elif tp.get_profile() is not None:                                          # profile already exists
            pass
        else:                                                                       # select first stable profile in list as the default profile
            with _MyChrooter(self) as m:
                out = m.shell_call("", "eselect profile list")
                profile = re.search(r"\[([0-9]+)\] .* \(stable\)", out, re.M).group(1)
                m.shell_call("", "eselect profile set %s" % (profile))

        # write /etc/portage
        tw.write_make_conf()
        tw.write_package_use()
        tw.write_package_mask()
        tw.write_package_unmask()
        tw.write_package_accept_keywords()
        tw.write_package_license()
        tw.write_package_env()
        tw.write_use_mask()
        # FIXME: should put files in patch-repository.d into config dir, so that target system can patch after every syncing
        #        but not all repositories and overlays use "emerge --sync"

    @ActionRunner.Action(after=["init_confdir"])
    def action_create_overlays(self, overlay_list):
        assert all([Util.isInstanceList(x, ManualSyncRepository, EmergeSyncRepository) for x in overlay_list])
        assert not any([x.get_name() == "gentoo" for x in overlay_list])
        assert len([x.get_name() for x in overlay_list]) == len(set([x.get_name() for x in overlay_list]))        # no duplication

        curPath = self._workDirObj.get_latest_action_dirpath()
        overlayRecord = dict()

        # create overlays
        myRepoDict = dict()
        pkgSet = set()
        for overlay in overlay_list:
            if isinstance(overlay, ManualSyncRepository):
                myRepo = _MyRepoUtil.createFromManuSyncRepo(overlay, False, curPath)
            elif isinstance(overlay, EmergeSyncRepository):
                myRepo = _MyRepoUtil.createFromEmergeSyncRepo(overlay, False, curPath)
                syncType = myRepo.get_sync_type()
                if syncType == "rsync":
                    pass
                elif syncType == "git":
                    pkgSet.add("dev-vcs/git")
                else:
                    assert False
                overlayRecord[overlay.get_name()] = syncType
            else:
                assert False
            myRepoDict[overlay.get_name()] = myRepo

        # install sync tools + sync some overlays
        if any([isinstance(repo, EmergeSyncRepository) for repo in overlay_list]):
            with _MyChrooter(self) as m:
                installList = [x for x in pkgSet if not Util.portageIsPkgInstalled(curPath, x)]
                m.script_exec(ScriptInstallPackages(installList, False, self._s.verbose_level), quiet=self._getQuiet())

                if any([isinstance(repo, EmergeSyncRepository) for repo in overlay_list]):
                    m.script_exec(ScriptSync(), quiet=self._getQuiet())

        # sync other overlays
        for overlay in overlay_list:
            if isinstance(overlay, ManualSyncRepository):
                overlay.sync(os.path.join(curPath, overlay.get_datadir_path()[1:]))

        # patch using host patch-repository.d
        if len(self._ts.repo_postsync_patch_directories) > 0:
            for overlay in overlay_list:
                myRepo = myRepoDict[overlay.get_name()]
                patchDirList = [os.path.join(self._s.host_repo_postsync_patch_source_dir, x) for x in self._ts.repo_postsync_patch_directories]
                pendingDstDirSet = myRepo.patch(patchDirList)
                with _MyChrooter(self) as m:
                    # FIXME: it a bit hard to parallelize the following code
                    for dstDir in pendingDstDirSet:
                        ebuildDir = os.path.join(myRepo.datadir_path, dstDir)
                        fn = glob.glob(os.path.join(ebuildDir, "*.ebuild"))[0]
                        m.shell_exec("ebuild %s manifest" % (fn))

        self._actionStorage["overlays"] = overlayRecord

    @ActionRunner.Action(after=["init_confdir", "create_overlays"])
    def action_update_world(self, world_set):
        curPath = self._workDirObj.get_latest_action_dirpath()

        def __worldNeeded(pkg):
            if pkg not in world_set:
                raise SettingsError("package %s is needed" % (pkg))

        # check
        if True:
            if self._ts.package_manager == "portage":
                __worldNeeded("sys-apps/portage")
            else:
                assert False
        if True:
            if self._ts.kernel_manager == "none":
                pass
            elif self._ts.kernel_manager == "genkernel":
                __worldNeeded("sys-kernel/genkernel")
            elif self._ts.kernel_manager == "binary-kernel":
                __worldNeeded("sys-kernel/gentoo-kernel-bin")
            elif self._ts.kernel_manager == "fake":
                pass
            else:
                assert False
        if True:
            if self._ts.service_manager == "none":
                pass
            elif self._ts.service_manager == "openrc":
                __worldNeeded("sys-apps/sysvinit")
                __worldNeeded("sys-apps/openrc")
            elif self._ts.service_manager == "systemd":
                __worldNeeded("sys-apps/systemd")
            else:
                assert False
        if True:
            if self._ts.build_opts.ccache:
                __worldNeeded("dev-util/ccache")
        if True:
            if "git" in self._actionStorage.get("overlays", {}).values():
                __worldNeeded("dev-vcs/git")
        if True:
            # many *-9999 packages needs them to fetch files
            __worldNeeded("dev-vcs/git")
            __worldNeeded("dev-vcs/subversion")

        # write world file
        t = TargetFilesAndDirs(curPath)
        with t.open_file_for_write_by_hostpath("world_file") as f:
            for pkg in sorted(list(world_set)):
                f.write("%s\n" % (pkg))

        # we need to install some packages before others
        preInstallList = [
            "dev-util/ccache",
            "dev-vcs/git",
            "dev-vcs/subversion",
        ]
        for i in reversed(range(0, len(preInstallList))):
            if preInstallList[i] not in world_set or Util.portageIsPkgInstalled(curPath, preInstallList[i]):
                preInstallList.pop(i)

        # install packages & update world
        with _MyChrooter(self) as m:
            if len(preInstallList) > 0:
                m.script_exec(ScriptInstallPackages(preInstallList, False, self._s.verbose_level), quiet=self._getQuiet())

            # we don't install packages seperately
            # many packages change global USE flag when installing, such as python_targets_XXX, so it needs to be combined with updating world to solve conflicts
            m.script_exec(ScriptUpdateWorld(self._s.verbose_level), quiet=self._getQuiet())

    @ActionRunner.Action(after=["init_confdir", "update_world"])
    def action_install_kernel(self):
        curPath = self._workDirObj.get_latest_action_dirpath()

        if self._ts.kernel_manager == "genkernel":
            t = TargetConfDirParser(curPath)
            tj = t.get_make_conf_make_opts_jobs()
            tl = t.get_make_conf_load_average()

            with _MyChrooter(self) as m:
                m.shell_call("", "eselect kernel set 1")

                if self._ts.kernel_manager_genkernel["kernel_config"] is not None:
                    customDotConfigFile = "/usr/src/custom-kernel-config"
                    with open(os.path.join(curPath, customDotConfigFile[1:]), "w") as f:
                        f.write(self._ts.kernel_manager_genkernel["kernel_config"])
                else:
                    customDotConfigFile = None
                m.script_exec(ScriptGenkernel(self._s.verbose_level, tj, tl, self._ts.build_opts.ccache, customDotConfigFile), quiet=self._getQuiet())

            return

        if self._ts.kernel_manager == "binary-kernel":
            # FIXME
            return

        if self._ts.kernel_manager == "fake":
            bootDir = os.path.join(curPath, "boot")
            os.makedirs(bootDir, exist_ok=True)
            with open(os.path.join(bootDir, "vmlinuz"), "w") as f:
                f.write("fake kernel")
            with open(os.path.join(bootDir, "initramfs.img"), "w") as f:
                f.write("fake initramfs")
            return

        assert False

    @ActionRunner.Action(after=["init_confdir", "update_world", "install_kernel"])
    def action_enable_services(self, service_list):
        if len(service_list) == 0:
            return

        if self._ts.service_manager == "openrc":
            with _MyChrooter(self) as m:
                for s in service_list:
                    m.shell_exec("", "rc-update add %s default > /dev/null" % (s))
        elif self._ts.service_manager == "systemd":
            with _MyChrooter(self) as m:
                for s in service_list:
                    m.shell_exec("", "systemctl enable %s -q" % (s))
        else:
            assert False

    @ActionRunner.Action(after=["init_confdir", "update_world", "install_kernel", "enable_services"])
    def action_cleanup(self, degentoo=False):
        curPath = self._workDirObj.get_latest_action_dirpath()

        with _MyChrooter(self) as m:
            m.shell_call("", "eselect news read all")
            m.script_exec(ScriptDepClean(self._s.verbose_level), quiet=self._getQuiet())

            if degentoo:
                # FIXME
                # m.shell_exec("", "%s/run-merge.sh -C sys-devel/gcc" % (scriptDirPath))
                # m.shell_exec("", "%s/run-merge.sh -C sys-apps/portage" % (scriptDirPath))
                pass

        t = TargetConfDirCleaner(curPath)
        t.cleanup_repos_conf_dir()
        t.cleanup_make_conf()

        if degentoo:
            # FIXME
            Util.forceDelete(t.confdir_hostpath)
            Util.forceDelete(t.statedir_hostpath)
            Util.forceDelete(t.pkgdbdir_hostpath)
            Util.forceDelete(t.srcdir_hostpath)
            Util.forceDelete(t.logdir_hostpath)
            Util.forceDelete(t.distdir_hostpath)
            Util.forceDelete(t.binpkgdir_hostpath)

    def _getQuiet(self):
        return (self._s.verbose_level == 0)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.dispose()


class CustomAction(abc.ABC):

    @property
    @abc.abstractmethod
    def custom_scripts(self):
        pass

    @property
    @abc.abstractmethod
    def after(self):
        pass

    @property
    @abc.abstractmethod
    def before(self):
        pass

    @classmethod
    def check_object(cls, obj, raise_exception=None):
        assert raise_exception is not None

        if not isinstance(obj, cls):
            if raise_exception:
                raise CustomActionError("invalid object type")
            else:
                return False

        if len(obj.custom_scripts) == 0 or any([not isinstance(s, ScriptInChroot) for s in obj.custom_scripts]):
            if raise_exception:
                raise CustomActionError("invalid value for key \"custom_scripts\"")
            else:
                return False

        if any([not re.fullmatch("[0-9a-z_]+", x) for x in obj.after]):
            if raise_exception:
                raise CustomActionError("invalid value for key \"after\"")
            else:
                return False

        if any([not re.fullmatch("[0-9a-z_]+", x) for x in obj.before]):
            if raise_exception:
                raise CustomActionError("invalid value for key \"before\"")
            else:
                return False

        return True


class _MyRepoUtil:

    @classmethod
    def createFromManuSyncRepo(cls, repo, repoOrOverlay, chrootDir):
        assert isinstance(repo, ManualSyncRepository)

        buf = ""
        buf += "[%s]\n" % (repo.get_name())
        buf += "auto-sync = no\n"
        buf += "location = %s\n" % (repo.get_datadir_path())

        myRepo = _MyRepo(chrootDir, cls._getReposConfFilename(repo, repoOrOverlay))
        myRepo.write_repos_conf_file(buf)
        os.makedirs(myRepo.datadir_hostpath, exist_ok=True)

        return myRepo

    @classmethod
    def createFromEmergeSyncRepo(cls, repo, repoOrOverlay, chrootDir):
        assert isinstance(repo, EmergeSyncRepository)

        buf = repo.get_repos_conf_file_content()

        myRepo = _MyRepo(chrootDir, cls._getReposConfFilename(repo, repoOrOverlay))
        myRepo.write_repos_conf_file(buf)
        os.makedirs(myRepo.datadir_hostpath, exist_ok=True)

        return myRepo

    @classmethod
    def scanReposConfDir(cls, chrootDir):
        return [_MyRepo(chrootDir, x) for x in os.listdir(cls._getReposConfDir(chrootDir))]

    @classmethod
    def cleanupReposConfDir(cls, chrootDir):
        Util.shellCall("sed '/mount-params = /d' %s/*" % (cls._getReposConfDir(chrootDir)))

    @staticmethod
    def _getReposConfDir(chrootDir):
        return os.path.join(chrootDir, "etc/portage/repos.conf")

    @staticmethod
    def _getReposConfFilename(repo, repoOrOverlay):
        if repoOrOverlay:
            fullname = repo.get_name()
        else:
            fullname = "overlay-" + repo.get_name()
        return fullname + ".conf"


class _MyRepo:

    def __init__(self, chroot_dir, repos_conf_file_name):
        self._chroot_path = chroot_dir
        self._repos_conf_file_name = repos_conf_file_name

    @property
    def repos_conf_file_hostpath(self):
        return os.path.join(self._chroot_path, self.repos_conf_file_path[1:])

    @property
    def datadir_hostpath(self):
        return os.path.join(self._chroot_path, self.datadir_path[1:])

    @property
    def repos_conf_file_path(self):
        return "/etc/portage/repos.conf/%s" % (self._repos_conf_file_name)

    @property
    def datadir_path(self):
        return re.search(r'location = (\S+)', pathlib.Path(self.repos_conf_file_hostpath).read_text(), re.M).group(1)

    def write_repos_conf_file(self, buf):
        os.makedirs(os.path.dirname(self.repos_conf_file_hostpath), exist_ok=True)
        with open(self.repos_conf_file_hostpath, "w") as f:
            f.write(buf)

    def get_repo_name(self):
        m = re.search("^\\[(.*)\\]$", pathlib.Path(self.repos_conf_file_hostpath).read_text(), re.M)
        return m.group(1)

    def get_sync_type(self):
        m = re.search(r'sync-type = (\S+)', pathlib.Path(self.repos_conf_file_hostpath).read_text(), re.M)
        return m.group(1) if m is not None else None

    def get_mount_params(self):
        m = re.search(r'mount-params = "(.*)","(.*)"', pathlib.Path(self.repos_conf_file_hostpath).read_text(), re.M)
        return (m.group(1), m.group(2)) if m is not None else None

    def patch(self, patchDirList):
        patcher = RepoPatcher()
        patchDirList = patcher.filter_and_convert_patch_dir_list(patchDirList, self.get_repo_name())
        if len(patchDirList) > 0:
            pendingDstDirSet = patcher.patch(self.datadir_hostpath, patchDirList)
            for x in patcher.warn_or_err_list:
                if x.warn_or_err:
                    print("Warning: %s" % (x.msg))
                else:
                    raise BuildError(x.msg)
            return pendingDstDirSet
        else:
            return set()

class _MyChrooter(Runner):

    def __init__(self, parent):
        super().__init__(parent._workDirObj.get_latest_action_dirpath())
        self._s = parent._s
        self._extraBindMountList = []

    def bind(self):
        super().bind()
        try:
            t = TargetFilesAndDirs(self._dir)

            # log directory mount point
            if self._s.log_dir is not None:
                assert os.path.exists(t.logdir_hostpath) and not Util.isMount(t.logdir_hostpath)
                Util.shellCall("mount --bind \"%s\" \"%s\"" % (self._s.log_dir, t.logdir_hostpath))
                self._extraBindMountList.append(t.logdir_hostpath)

            # distdir mount point
            if self._s.host_distfiles_dir is not None:
                assert os.path.exists(t.distdir_hostpath) and not Util.isMount(t.distdir_hostpath)
                Util.shellCall("mount --bind \"%s\" \"%s\"" % (self._s.host_distfiles_dir, t.distdir_hostpath))
                self._extraBindMountList.append(t.distdir_hostpath)

            # pkgdir mount point
            if self._s.host_packages_dir is not None:
                assert os.path.exists(t.binpkgdir_hostpath) and not Util.isMount(t.binpkgdir_hostpath)
                Util.shellCall("mount --bind \"%s\" \"%s\"" % (self._s.host_packages_dir, t.binpkgdir_hostpath))
                self._extraBindMountList.append(t.binpkgdir_hostpath)

            # ccachedir mount point
            if self._s.host_ccache_dir is not None and os.path.exists(t.ccachedir_hostpath):
                assert not Util.isMount(t.ccachedir_hostpath)
                Util.shellCall("mount --bind \"%s\" \"%s\"" % (self._s.host_ccache_dir, t.ccachedir_hostpath))
                self._extraBindMountList.append(t.ccachedir_hostpath)
        except BaseException:
            self.unbind(remove_scripts=False)
            raise

    def unbind(self):
        for fullfn in reversed(self._extraBindMountList):
            Util.cmdCall("umount", "-l", fullfn)
        self._extraBindMountList = []
        super().unbind()


class TargetFilesAndDirs:

    def __init__(self, chrootDir):
        self._chroot_path = chrootDir

    @property
    def confdir_path(self):
        return "/etc/portage"

    @property
    def statedir_path(self):
        return "/var/lib/portage"

    @property
    def pkgdbdir_path(self):
        return "/var/db/pkg"

    @property
    def logdir_path(self):
        return "/var/log/portage"

    @property
    def distdir_path(self):
        return "/var/cache/distfiles"

    @property
    def binpkgdir_path(self):
        return "/var/cache/binpkgs"

    @property
    def ccachedir_path(self):
        return "/var/tmp/ccache"

    @property
    def srcdir_path(self):
        return "/usr/src"

    @property
    def world_file_path(self):
        return os.path.join(self.statedir_path, "world")

    @property
    def confdir_metadata(self):
        return ("root", "root", 0o40755)

    @property
    def statedir_metadata(self):
        return ("root", "portage", 0o42755)        # rwxr-sr-x

    @property
    def pkgdbdir_metadata(self):
        return ("root", "root", 0o40755)

    @property
    def logdir_metadata(self):
        return ("portage", "portage", 0o42755)     # rwxr-sr-x

    @property
    def distdir_metadata(self):
        return ("root", "portage", 0o40755)

    @property
    def binpkgdir_metadata(self):
        return ("root", "root", 0o40755)           # FIXME

    @property
    def ccachedir_metadata(self):
        return ("root", "root", 0o40755)           # FIXME

    @property
    def srcdir_metadata(self):
        return ("root", "root", 0o40755)           # FIXME

    @property
    def world_file_metadata(self):
        return ("root", "portage", 0o40644)

    @property
    def confdir_hostpath(self):
        return os.path.join(self._chroot_path, self.confdir_path[1:])

    @property
    def statedir_hostpath(self):
        return os.path.join(self._chroot_path, self.statedir_path[1:])

    @property
    def pkgdbdir_hostpath(self):
        return os.path.join(self._chroot_path, self.pkgdbdir_path[1:])

    @property
    def logdir_hostpath(self):
        return os.path.join(self._chroot_path, self.logdir_path[1:])

    @property
    def distdir_hostpath(self):
        return os.path.join(self._chroot_path, self.distdir_path[1:])

    @property
    def binpkgdir_hostpath(self):
        return os.path.join(self._chroot_path, self.binpkgdir_path[1:])

    @property
    def ccachedir_hostpath(self):
        return os.path.join(self._chroot_path, self.ccachedir_path[1:])

    @property
    def srcdir_hostpath(self):
        return os.path.join(self._chroot_path, self.srcdir_path[1:])

    @property
    def world_file_hostpath(self):
        return os.path.join(self._chroot_path, self.world_file_path[1:])

    def make_dir_by_hostpath(self, path_id, exist_ok=False):
        path = getattr(self, path_id + "_hostpath")
        owner, group, mode = getattr(self, path_id + "_metadata")
        owner, group = self._convertOwner(owner), self._convertGroup(group)

        if os.path.exists(path):
            if not exist_ok:
                raise FileExistsError("%s exists" % (path))
            else:
                st = os.stat(path)
                if st.st_uid != owner:
                    raise FileExistsError("existing directory %s has invalid owner %d" % (path, st.st_uid))
                if st.st_gid != group:
                    if path_id == "distdir":
                        # FIXME: it seems gentoo stage3 has a bug that /var/cache/distfiles has wrong mode
                        os.chown(path, owner, group)
                    else:
                        raise FileExistsError("existing directory %s has invalid group %d" % (path, st.st_gid))
                if st.st_mode != mode:
                    if path_id == "logdir":
                        # FIXME: it seems gentoo stage3 has a bug that /var/log/portage has wrong mode
                        os.chmod(path, mode)
                    else:
                        raise FileExistsError("existing directory %s has invalid mode 0o%o" % (path, st.st_mode))
        else:
            os.mkdir(path)
            os.chown(path, owner, group)
            os.chmod(path, mode)

    def open_file_for_write_by_hostpath(self, path_id):
        return TargetFilesAndDirsOpenFileForWrite(self, path_id)

    def _convertOwner(self, owner):
        if owner == "root":
            return 0
        else:
            passwd_file = os.path.join(self._chroot_path, "etc", "passwd")
            data = self._parsePasswdOrGroup(passwd_file)
            return data[owner]

    def _convertGroup(self, group):
        if group == "root":
            return 0
        else:
            group_file = os.path.join(self._chroot_path, "etc", "group")
            data = self._parsePasswdOrGroup(group_file)
            return data[group]

    def _parsePasswdOrGroup(self, path):
        ret = dict()
        for line in pathlib.Path(path).read_text().split("\n"):
            if line == "" or line.startswith("#"):
                continue
            t = line.split(":")
            ret[t[0]] = int(t[2])      # <username, user-id> or <group-name, group-id>
        return ret


class TargetFilesAndDirsOpenFileForWrite:

    def __init__(self, parent, path_id):
        self._path = getattr(parent, path_id + "_hostpath")
        self._owner, self._group, self._mode = getattr(parent, path_id + "_metadata")
        self._owner, self._group = parent._convertOwner(self._owner), parent._convertGroup(self._group)

    def write(self, *kargs):
        self._f.write(*kargs)

    def __enter__(self):
        self._f = open(self._path, "w")
        return self

    def __exit__(self, type, value, traceback):
        self._f.close()
        del self._f
        os.chown(self._path, self._owner, self._group)
        os.chmod(self._path, self._mode)


class TargetConfDirParser:

    def __init__(self, chrootDir):
        self._dir = TargetFilesAndDirs(chrootDir).confdir_hostpath

    def get_profile(self):
        fullfn = os.path.join(self._dir, "make.profile")
        if not os.path.exists(fullfn):
            return None

        profileDir = os.readlink(fullfn)
        assert os.path.exists(os.path.join(self._dir, profileDir))

        idx = profileDir.index("profiles/")
        return profileDir[idx + len("profiles/")]

    def get_make_conf_make_opts_jobs(self):
        buf = pathlib.Path(os.path.join(self._dir, "make.conf")).read_text()

        m = re.search("MAKEOPTS=\".*--jobs=([0-9]+).*\"", buf, re.M)
        if m is not None:
            return int(m.group(1))

        m = re.search("MAKEOPTS=\".*-j([0-9]+).*\"", buf, re.M)
        if m is not None:
            return int(m.group(1))

        assert False

    def get_make_conf_load_average(self):
        buf = pathlib.Path(os.path.join(self._dir, "make.conf")).read_text()
        m = re.search("EMERGE_DEFAULT_OPTS=\".*--load-average=([0-9]+).*\"", buf, re.M)
        if m is not None:
            return int(m.group(1))
        assert False


class TargetConfDirWriter:

    def __init__(self, settings, targetSettings, chrootDir):
        self._s = settings
        self._ts = targetSettings
        self._dir = TargetFilesAndDirs(chrootDir).confdir_hostpath

    def write_make_conf(self):
        # determine parallelism parameters
        paraMakeOpts = None
        paraEmergeOpts = None
        if True:
            if self._s.host_cooling_level <= 1:
                jobcountMake = 1
                jobcountEmerge = 1
                loadavg = 1
            else:
                if self._s.host_memory_size >= 24 * 1024 * 1024 * 1024:       # >=24G
                    jobcountMake = self._s.host_cpu_core_count + 2
                    jobcountEmerge = self._s.host_cpu_core_count
                    loadavg = self._s.host_cpu_core_count
                else:
                    jobcountMake = self._s.host_cpu_core_count
                    jobcountEmerge = self._s.host_cpu_core_count
                    loadavg = max(1, self._s.host_cpu_core_count - 1)

            paraMakeOpts = ["--jobs=%d" % (jobcountMake), "--load-average=%d" % (loadavg), "-j%d" % (jobcountMake), "-l%d" % (loadavg)]     # for bug 559064 and 592660, we need to add -j and -l, it sucks
            paraEmergeOpts = ["--jobs=%d" % (jobcountEmerge), "--load-average=%d" % (loadavg)]

        # define helper functions
        def __flagsWrite(flags, value):
            if value is None:
                if self._ts.build_opts.common_flags is None:
                    pass
                else:
                    myf.write('%s="${COMMON_FLAGS}"\n' % (flags))
            else:
                if isinstance(value, list):
                    myf.write('%s="%s"\n' % (flags, ' '.join(value)))
                else:
                    myf.write('%s="%s"\n' % (flags, value))

        # modify and write out make.conf (in chroot)
        makepath = os.path.join(self._dir, "make.conf")
        with open(makepath, "w") as myf:
            myf.write("# These settings were set by %s that automatically built this stage.\n" % (self._s.program_name))
            myf.write("# Please consult /usr/share/portage/config/make.conf.example for a more detailed example.\n")
            myf.write("\n")

            # features
            featureList = []
            if self._ts.build_opts.ccache:
                featureList.append("ccache")
            if len(featureList) > 0:
                myf.write('FEATURES="%s"\n' % (" ".join(featureList)))
                myf.write('\n')

            # flags
            if self._ts.build_opts.common_flags is not None:
                myf.write('COMMON_FLAGS="%s"\n' % (' '.join(self._ts.build_opts.common_flags)))
            __flagsWrite("CFLAGS", self._ts.build_opts.cflags)
            __flagsWrite("CXXFLAGS", self._ts.build_opts.cxxflags)
            __flagsWrite("FCFLAGS", self._ts.build_opts.fcflags)
            __flagsWrite("FFLAGS", self._ts.build_opts.fflags)
            __flagsWrite("LDFLAGS", self._ts.build_opts.ldflags)
            __flagsWrite("ASFLAGS", self._ts.build_opts.asflags)
            myf.write('\n')

            # set default locale for system responses. #478382
            myf.write('LC_MESSAGES=C\n')
            myf.write('\n')

            # set MAKEOPTS and EMERGE_DEFAULT_OPTS
            myf.write('MAKEOPTS="%s"\n' % (' '.join(paraMakeOpts)))
            myf.write('EMERGE_DEFAULT_OPTS="--quiet-build=y --autounmask --autounmask-write --autounmask-continue --autounmask-license=y --backtrack=100 %s"\n' % (' '.join(paraEmergeOpts)))
            myf.write('\n')

    def write_package_use(self):
        # modify and write out package.use (in chroot)
        fpath = os.path.join(self._dir, "package.use")
        Util.forceDelete(fpath)

        # generate main file content
        # buf = "*/* compile-locales\n"   # compile all locales
        buf = ""
        for pkg_wildcard, use_flag_list in self._ts.pkg_use.items():
            if "compile-locales" in use_flag_list:
                raise SettingsError("USE flag \"compile-locales\" is not allowed")
            if "-compile-locales" in use_flag_list:
                raise SettingsError("USE flag \"-compile-locales\" is not allowed")
            buf += "%s %s\n" % (pkg_wildcard, " ".join(use_flag_list))

        if len(self._ts.pkg_use_files) > 0:
            # create directory
            os.mkdir(fpath)
            for file_name, file_content in self._ts.pkg_use_files.items():
                with open(os.path.join(fpath, file_name), "w") as myf:
                    myf.write(file_content)
            with open(os.path.join(fpath, "90-main"), "w") as myf:
                # create this file even if content is empty
                myf.write(buf)
            with open(os.path.join(fpath, "99-autouse"), "w") as myf:
                myf.write("")
        else:
            # create file
            with open(fpath, "w") as myf:
                myf.write(buf)

    def write_package_mask(self):
        # modify and write out package.mask (in chroot)
        fpath = os.path.join(self._dir, "package.mask")
        Util.forceDelete(fpath)

        # generate main file content
        buf = ""
        for pkg_wildcard in self._ts.pkg_mask:
            buf += "%s\n" % (pkg_wildcard)

        if len(self._ts.pkg_mask_files) > 0:
            # create directory
            os.mkdir(fpath)
            for file_name, file_content in self._ts.pkg_mask_files.items():
                with open(os.path.join(fpath, file_name), "w") as myf:
                    myf.write(file_content)
            with open(os.path.join(fpath, "90-main"), "w") as myf:
                # create this file even if content is empty
                myf.write(buf)
            with open(os.path.join(fpath, "99-bugmask"), "w") as myf:
                myf.write("")
        else:
            # create file
            with open(fpath, "w") as myf:
                myf.write(buf)

    def write_package_unmask(self):
        # modify and write out package.unmask (in chroot)
        fpath = os.path.join(self._dir, "package.unmask")
        Util.forceDelete(fpath)

        # generate main file content
        buf = ""
        for pkg_wildcard in self._ts.pkg_unmask:
            buf += "%s\n" % (pkg_wildcard)

        if len(self._ts.pkg_unmask_files) > 0:
            # create directory
            os.mkdir(fpath)
            for file_name, file_content in self._ts.pkg_unmask_files.items():
                with open(os.path.join(fpath, file_name), "w") as myf:
                    myf.write(file_content)
            with open(os.path.join(fpath, "90-main"), "w") as myf:
                # create this file even if content is empty
                myf.write(buf)
        else:
            # create file
            with open(fpath, "w") as myf:
                myf.write(buf)

    def write_package_accept_keywords(self):
        # modify and write out package.accept_keywords (in chroot)
        fpath = os.path.join(self._dir, "package.accept_keywords")
        Util.forceDelete(fpath)

        # generate main file content
        buf = ""
        for pkg_wildcard, keyword_list in self._ts.pkg_accept_keywords.items():
            buf += "%s %s\n" % (pkg_wildcard, " ".join(keyword_list))

        if len(self._ts.pkg_accept_keywords_files) > 0:
            # create directory
            os.mkdir(fpath)
            for file_name, file_content in self._ts.pkg_accept_keywords_files.items():
                with open(os.path.join(fpath, file_name), "w") as myf:
                    myf.write(file_content)
            with open(os.path.join(fpath, "90-main"), "w") as myf:
                # create this file even if content is empty
                myf.write(buf)
            with open(os.path.join(fpath, "99-autokeyword"), "w") as myf:
                myf.write("")
        else:
            # create this file only if content is not empty
            with open(fpath, "w") as myf:
                myf.write(buf)

    def write_package_license(self):
        # modify and write out package.license (in chroot)
        fpath = os.path.join(self._dir, "package.license")
        Util.forceDelete(fpath)

        # generate main file content
        buf = ""
        for pkg_wildcard, license_list in self._ts.pkg_license.items():
            buf += "%s %s\n" % (pkg_wildcard, " ".join(license_list))

        if len(self._ts.pkg_license_files) > 0:
            # create directory
            os.mkdir(fpath)
            for file_name, file_content in self._ts.pkg_license_files.items():
                with open(os.path.join(fpath, file_name), "w") as myf:
                    myf.write(file_content)
            with open(os.path.join(fpath, "90-main"), "w") as myf:
                # create this file even if content is empty
                myf.write(buf)
            with open(os.path.join(fpath, "99-autolicense"), "w") as myf:
                myf.write("")
        else:
            # create this file only if content is not empty
            if buf != "":
                with open(fpath, "w") as myf:
                    myf.write(buf)

    def write_package_env(self):
        # modify and write out package.env and env directory (in chroot)
        fpath = os.path.join(self._dir, "package.env")
        fpath2 = os.path.join(self._dir, "env")
        Util.forceDelete(fpath)

        data = self._ts.install_mask_files.copy()
        assert "00-common" not in data
        if len(self._ts.install_mask) > 0:
            data["00-common"] = {
                "*/*": self._ts.install_mask
            }

        if len(data) > 0:
            os.mkdir(fpath)
            os.makedirs(fpath2, exist_ok=True)
            for file_name, obj in data.items():
                assert len(obj) >= 1
                innerFnDict = dict()
                for pkgWildcard, installMaskList in obj.items():
                    if len(obj) > 1:
                        innerFn = "%s-%d.env" % (file_name, len(innerFnDict) + 1)
                    else:
                        innerFn = "%s.env" % (file_name)
                    with open(os.path.join(fpath2, innerFn), "w") as f:
                        for x in installMaskList:
                            f.write('INSTALL_MASK="${INSTALL_MASK} %s"\n' % (x))
                    innerFnDict[pkgWildcard] = innerFn
                with open(os.path.join(fpath, file_name), "w") as f:
                    for pkgWildcard in obj.keys():
                        f.write('%s %s\n' % (pkgWildcard, innerFnDict[pkgWildcard]))

    def write_repo_postsync(self):
        # modify and write out repo.postsync.d (in chroot)
        fpath = os.path.join(self._dir, "repo.postsync.d")
        Util.forceDelete(fpath)

        # FIXME
        assert False

    def write_use_mask(self):
        # modify and write out use.mask (in chroot)
        if len(self._ts.use_mask) > 0:
            fpath = os.path.join(self._dir, "profile", "use.mask")
            os.makedirs(os.path.dirname(fpath), exist_ok=True)
            with open(fpath, "w") as myf:
                for use_flag in self._ts.use_mask:
                    myf.write("%s\n" % (use_flag))


class TargetConfDirCleaner:

    def __init__(self, chrootDir):
        self._dir = TargetFilesAndDirs(chrootDir).confdir_hostpath

    def cleanup_repos_conf_dir(self):
        Util.shellCall("sed -i '/mount-params = /d' %s/repos.conf/*" % (self._dir))

    def cleanup_make_conf(self):
        # FIXME: remove remaining spaces
        Util.shellCall("sed -i 's/--autounmask-continue//g' %s/make.conf" % (self._dir))
        Util.shellCall("sed -i 's/--autounmask-license=y//g' %s/make.conf" % (self._dir))
        Util.shellCall("sed -i 's/--autounmask//g' %s/make.conf" % (self._dir))


class ScriptSync(ScriptFromBuffer):

    def __init__(self):
        super().__init__(self._scriptContent)

    _scriptContent = """
#!/bin/bash

export EMERGE_WARNING_DELAY=0
export CLEAN_DELAY=0
export EBEEP_IGNORE=0
export EPAUSE_IGNORE=0

emerge --sync || exit 1
"""


class ScriptGenkernel(ScriptFromBuffer):

    def __init__(self, verbose_level, tj, tl, ccache, customDotConfigFile):
        buf = "#!/bin/bash\n"
        buf += "\n"

        if ccache:
            buf += "export CCACHE_DIR=/var/tmp/ccache\n"
            buf += "\n"

        cmd = ""
        if True:
            cmd += "genkernel --color --no-mountboot "
            if customDotConfigFile is not None:
                cmd += "--kernel-config=%s " % (customDotConfigFile)
            cmd += "--kernel-filename=vmlinuz --initramfs-filename=initramfs.img --kernel-config-filename=kernel-config "
            cmd += "--all-ramdisk-modules "
            cmd += "--makeopts='-j%d -l%d' " % (tj, tl)
            if ccache:
                cmd += "--kernel-cc=/usr/lib/ccache/bin/gcc --utils-cc=/usr/lib/ccache/bin/gcc "
            cmd += "all"

        if verbose_level == 0:
            buf += cmd + " > /var/log/portage/genkernel.log 2>&1\n"
        elif verbose_level in [1, 2]:
            buf += cmd + " 2>&1 | tee /var/log/portage/genkernel.log\n"
        else:
            assert False

        super().__init__(buf)


class ScriptDepClean(ScriptFromBuffer):

    def __init__(self, verbose_level):
        buf = self._scriptContent
        if verbose_level == 0:
            buf = buf.replace("%OUTPUT%", "> /var/log/portage/run-depclean.log 2>&1")
        elif verbose_level in [1, 2]:
            buf = buf.replace("%OUTPUT%", "2>&1 | tee /var/log/portage/run-depclean.log")
        else:
            assert False

        super().__init__(buf)

    _scriptContent = """
#!/bin/bash

export EMERGE_WARNING_DELAY=0
export CLEAN_DELAY=0
export EBEEP_IGNORE=0
export EPAUSE_IGNORE=0
export CONFIG_PROTECT="-* .x"

emerge --depclean %OUTPUT%
"""
