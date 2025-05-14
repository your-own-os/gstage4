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
import time
import http.client
import shutil
import urllib.request
import urllib.error
import asyncio
import platform
import traceback
import subprocess
import PySquashfsImage


class Util:

    @staticmethod
    def robustUrlOpen(*kargs, **kwargs):
        assert "timeout" not in kwargs
        while True:
            try:
                return urllib.request.urlopen(*kargs, **kwargs, timeout=60)
            except http.client.RemoteDisconnected:
                time.sleep(1)
            except urllib.error.URLError as e:
                if isinstance(e.reason, TimeoutError):
                    time.sleep(1)
                else:
                    raise

    @staticmethod
    def getLangEncoding():
        ret = None

        # extract encoding part from LANG、LC_* environment variables
        # 1. ensures that encoding part exists
        # 2. ensures that encoding parts are same
        for k, v in os.environ.items():
            if k != "LANG" and not k.startswith("LC_"):
                continue

            # en_US.UTF-8 -> UTF-8
            m = re.fullmatch(r'.*\.(.*)', v)
            if m is None:
                return None

            if ret is None:
                ret = m.group(1)
                continue

            if m.group(1) != ret:
                return None

        return ret

    @staticmethod
    def getTermType():
        return os.environ.get("TERM", None)

    @staticmethod
    def hasTermInfoFile(termType, targetRootDir):
        fullfn = os.path.join(targetRootDir, "usr", "share", "terminfo", termType[0], termType)
        return os.path.exists(fullfn)

    @staticmethod
    def copyTermInfoFile(termType, sourceRootDir, targetRootDir):
        srcFullfn = os.path.join(sourceRootDir, "usr", "share", "terminfo", termType[0], termType)
        dstFullfn = os.path.join(targetRootDir, "usr", "share", "terminfo", termType[0], termType)
        os.makedirs(os.path.dirname(dstFullfn), exist_ok=True)
        shutil.copy(srcFullfn, dstFullfn)

    @staticmethod
    def getCpuArch():
        ret = platform.machine()
        if ret == "x86_64":
            return "amd64"
        else:
            return ret

    @staticmethod
    def isArchCompatible(targetArch, curArch):
        if targetArch == curArch:
            return True
        if targetArch == "i386" and curArch == "amd64":
            return True
        return False

    @staticmethod
    def listStartswith(theList, subList):
        return len(theList) >= len(subList) and theList[:len(subList)] == subList

    @staticmethod
    def listSparseContain(theList, subList):
        # example: theList [1, 2, 3, 4] subList [1, 3] returns True
        idx = -1
        for x in subList:
            idx2 = theList.index(x)
            if idx2 <= idx:
                return False
            idx = idx2
        return True

    @staticmethod
    def forceDelete(path):
        if os.path.islink(path):
            os.remove(path)
        elif os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.lexists(path):
            os.remove(path)             # other type of file, such as device node
        else:
            pass                        # path does not exist, do nothing

    @staticmethod
    def removeDirContentExclude(dirPath, excludeList):
        for fn in os.listdir(dirPath):
            if fn not in excludeList:
                Util.forceDelete(os.path.join(dirPath, fn))

    @staticmethod
    def pathCompare(path1, path2):
        # Change double slashes to slash
        path1 = re.sub(r"//", r"/", path1)
        path2 = re.sub(r"//", r"/", path2)
        # Removing ending slash
        path1 = re.sub("/$", "", path1)
        path2 = re.sub("/$", "", path2)

        if path1 == path2:
            return 1
        return 0

    @staticmethod
    def isMount(path):
        """Like os.path.ismount, but also support bind mounts"""
        if os.path.ismount(path):
            return 1
        a = os.popen("mount")
        mylines = a.readlines()
        a.close()
        for line in mylines:
            mysplit = line.split()
            if Util.pathCompare(path, mysplit[2]):
                return 1
        return 0

    @staticmethod
    def isInstanceList(obj, *instances):
        for inst in instances:
            if isinstance(obj, inst):
                return True
        return False

    @staticmethod
    def cmdCall(cmd, *kargs):
        # call command to execute backstage job
        #
        # scenario 1, process group receives SIGTERM, SIGINT and SIGHUP:
        #   * callee must auto-terminate, and cause no side-effect
        #   * caller must be terminated by signal, not by detecting child-process failure
        # scenario 2, caller receives SIGTERM, SIGINT, SIGHUP:
        #   * caller is terminated by signal, and NOT notify callee
        #   * callee must auto-terminate, and cause no side-effect, after caller is terminated
        # scenario 3, callee receives SIGTERM, SIGINT, SIGHUP:
        #   * caller detects child-process failure and do appopriate treatment

        ret = subprocess.run([cmd] + list(kargs),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
        if ret.returncode > 128:
            # for scenario 1, caller's signal handler has the oppotunity to get executed during sleep
            time.sleep(1.0)
        if ret.returncode != 0:
            print(ret.stdout)
            ret.check_returncode()
        return ret.stdout.rstrip()

    @staticmethod
    def shellCall(cmd):
        # call command with shell to execute backstage job
        # scenarios are the same as FmUtil.cmdCall

        ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             shell=True, text=True)
        if ret.returncode > 128:
            # for scenario 1, caller's signal handler has the oppotunity to get executed during sleep
            time.sleep(1.0)
        if ret.returncode != 0:
            print(ret.stdout)
            ret.check_returncode()
        return ret.stdout.rstrip()

    @staticmethod
    def cmdCallIgnoreResult(cmd, *kargs):
        ret = subprocess.run([cmd] + list(kargs),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True)
        if ret.returncode > 128:
            time.sleep(1.0)

    @staticmethod
    def repoListCategoryDir(repoDir):
        ret = []
        for categoryDir in os.listdir(repoDir):
            fullCategoryDir = os.path.join(repoDir, categoryDir)
            if os.path.isdir(fullCategoryDir) and (categoryDir == "virtual" or "-" in categoryDir):
                ret.append((categoryDir, fullCategoryDir))
        return ret

    @staticmethod
    def repoListEbuildDir(repoCategoryDir):
        ret = []
        for dstEbuildDir in os.listdir(repoCategoryDir):
            fullDstEbuildDir = os.path.join(repoCategoryDir, dstEbuildDir)
            if os.path.isdir(fullDstEbuildDir):
                ret.append((dstEbuildDir, fullDstEbuildDir))
        return ret

    @staticmethod
    def portageIsPkgInstalled(rootDir, pkg):
        dir = os.path.join(rootDir, "var", "db", "pkg", os.path.dirname(pkg))
        if os.path.exists(dir):
            for fn in os.listdir(dir):
                if fn.startswith(os.path.basename(pkg)):
                    return True
        return False


class DirListMount:

    def __init__(self, mountList):
        self.okList = []
        for item in mountList:      # mountList = [(directory, mount-commad-1, mount-command-2, ...)]
            dir = item[0]
            if not os.path.exists(dir):
                os.makedirs(dir)
            for i in range(1, len(item)):
                try:
                    Util.shellCall("%s %s" % ("/bin/mount", item[i]))
                    self.okList.insert(0, dir)
                except subprocess.CalledProcessError:
                    self.dispose()
                    raise

    def dispose(self):
        for d in self.okList:
            Util.cmdCallIgnoreResult("/bin/umount", "-l", d)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.dispose()


class ActionRunner:

    class PersistStorage(abc.ABC):

        @abc.abstractmethod
        def initGetCurrentActionInfo(self):
            pass

        @abc.abstractmethod
        def getHistoryActionNames(self):
            pass

        @abc.abstractmethod
        def isFinished(self):
            pass

        @abc.abstractmethod
        def isInUse(self):
            pass

        @abc.abstractmethod
        def use(self):
            pass

        @abc.abstractmethod
        def saveActionStart(self, actionName):
            pass

        @abc.abstractmethod
        def saveActionEnd(self, error=None):
            pass

        @abc.abstractmethod
        def saveFinished(self):
            pass

        @abc.abstractmethod
        def unUse(self):
            pass

    class CustomAction(abc.ABC):

        @abc.abstractmethod
        def get_after(self):
            pass

        @abc.abstractmethod
        def get_before(self):
            pass

    def Action(after=[], before=[], _custom_action_name=None, _custom_action=None):
        def decorator(func):
            def wrapper(self, *kargs, **kwargs):
                curActionIndex = self._getActionIndex(wrapper._action_func_name)
                if self._finished is not None:
                    if self._finished == "":
                        raise self._errClass("build already finished")
                    else:
                        raise self._errClass("build already failed, %s" % (self._finished))
                if curActionIndex != self._lastActionIndex + 1:
                    lastActionName = self._actionList[self._lastActionIndex]._action_func_name[len("action_"):] if self._lastActionIndex >= 0 else "None"
                    raise self._errClass("action must be executed in order (last: %s, current: %s)" % (lastActionName, wrapper._action_func_name[len("action_"):]))
                self._persistStorage.saveActionStart(wrapper._action_func_name[len("action_"):])
                try:
                    if wrapper._action is None:
                        func(self, *kargs, **kwargs)
                    else:
                        func(self, wrapper._action_func_name[len("action_"):], wrapper._action, *kargs, **kwargs)
                except BaseException as e:
                    self._finished = str(e)
                    self._persistStorage.saveActionEnd(self._finished)
                    raise
                else:
                    self._lastActionIndex = curActionIndex
                    self._persistStorage.saveActionEnd()
            wrapper._action_func_name = (func.__name__ if _custom_action_name is None else "action_" + _custom_action_name)
            wrapper._action = _custom_action
            wrapper._after = (after if _custom_action is None else _custom_action.get_after())
            wrapper._before = (before if _custom_action is None else _custom_action.get_before())
            return wrapper
        return decorator

    def __init__(self, persistStorage, actionList, customActionFunc, errClass):
        self._persistStorage = persistStorage
        self._actionList = actionList
        self._endAction = actionList[-1]
        self._customActionFunc = customActionFunc
        self._errClass = errClass

        # check self._actionList
        self._assertActions()

        # self._lastActionIndex == -1 if no action has been executed
        self._lastActionIndex = -1
        if len(self._persistStorage.getHistoryActionNames()) > 0:
            actionFuncNameList = [x._action_func_name for x in self._actionList]
            historyActionFuncNameList = ["action_" + x for x in self._persistStorage.getHistoryActionNames()]
            self._lastActionIndex = actionFuncNameList.index(historyActionFuncNameList[-1])
            if self._lastActionIndex == -1:
                raise self._errClass("invalid history actions")
            if not Util.listSparseContain(historyActionFuncNameList[:-1], actionFuncNameList[:self._lastActionIndex]):
                raise self._errClass("invalid history actions")

        # not finished:          self._finished is None
        # successfully finished: self._finished == ""
        # abnormally finished:   self._finished == error-message
        _, err = self._persistStorage.initGetCurrentActionInfo()
        if err is not None:
            self._finished = err
        else:
            self._finished = "" if self._persistStorage.isFinished() else None

        self._persistStorage.use()

    def dispose(self):
        self._persistStorage.unUse()

    def finish(self):
        assert self._finished is None
        assert self._lastActionIndex >= self._actionList.index(self._endAction)
        self._finished = ""
        self._persistStorage.saveFinished()

    def add_custom_action(self, action_name, action, insert_after=None, insert_before=None):
        self.add_custom_actions({action_name: action}, insert_after, insert_before)

    def add_custom_actions(self, action_dict, insert_after=None, insert_before=None):
        for action_name, action in action_dict.items():
            assert re.fullmatch("[0-9a-z_]+", action_name) and "action_" + action_name not in dir(self)
            assert isinstance(action, self.CustomAction)
            assert all([re.fullmatch("[0-9a-z_]+", x) for x in action.get_after()])
            assert all([re.fullmatch("[0-9a-z_]+", x) for x in action.get_before()])

        # convert action object or action name to action index
        if insert_before is not None:
            if insert_before.__class__.__name__ == "method":                        # FIXME
                insert_before = self._actionList.index(insert_before)
            else:
                insert_before = self._getActionIndex("action_" + insert_before)
        if insert_after is not None:
            if insert_after.__class__.__name__ == "method":                         # FIXME
                insert_after = self._actionList.index(insert_after)
            else:
                insert_after = self._getActionIndex("action_" + insert_after)

        # convert to use insert_before only
        if insert_before is not None and insert_after is None:
            pass
        elif insert_before is None and insert_after is not None:
            insert_before = insert_after + 1
        elif insert_before is None and insert_after is None:
            insert_before = len(self._actionList)
        else:
            assert False

        assert self._lastActionIndex < insert_before

        # create new actions and add them to self._actionList
        for action_name, action in action_dict.items():
            func = self.Action(_custom_action_name=action_name, _custom_action=action)(self._customActionFunc)
            func = func.__get__(self)
            exec("self.action_%s = func" % (action_name))
            self._actionList.insert(insert_before, eval("self.action_%s" % (action_name)))
            insert_before += 1

        # do check
        self._assertActions()

    def has_action(self, action_name):
        for action in self._actionList:
            if action._action_func_name == "action_" + action_name:
                return True
        return False

    def add_and_run_custom_action(self, action_name, action):
        self.add_and_run_custom_actions({action_name: action})

    def add_and_run_custom_actions(self, action_dict):
        i = self._lastActionIndex
        for action_name, action in action_dict.items():
            if i == -1:
                self.add_custom_action(action_name, action, insert_before=self._actionList[0])
            else:
                self.add_custom_action(action_name, action, insert_after=self._actionList[i])
            i += 1

        exec("self.action_%s()" % (list(action_dict.keys())[0]))

    def get_progress(self):
        if self._finished is None:
            ret = (self._lastActionIndex + 1) * 100 // len(self._actionList)
            return min(ret, 99)
        else:
            return 100

    def _getActionIndex(self, action_func_name):
        for i, action in enumerate(self._actionList):
            if action._action_func_name == action_func_name:
                return i
        assert False

    def _assertActions(self):
        actionFuncNameList = [x._action_func_name for x in self._actionList]
        for i, action in enumerate(self._actionList):
            assert all(["action_" + x not in actionFuncNameList[:i] for x in action._before])
            assert all(["action_" + x not in actionFuncNameList[i+1:] for x in action._after])


class SqfsExtractor:

    """
    The following code is copy and modified from PySquashfsImage.extract
    hardlink, device file, special file, user/group/mode, xattr are not supported
    """

    @classmethod
    def extract(cls, filepath, dest):
        with PySquashfsImage.SquashFsImage.from_file(filepath) as image:
            cls._sqfsExtractDir(image.select("/"), dest, {})

    @classmethod
    def _sqfsExtractDir(cls, directory, dest, lookup_table):
        for file in directory:
            path = os.path.join(dest, os.path.relpath(file.path, directory.path))
            if file.is_dir:
                os.mkdir(path)
                cls._sqfsExtractDir(file, path, lookup_table)
            else:
                cls._sqfsExtractFile(file, path, lookup_table)

    @classmethod
    def _sqfsExtractFile(cls, file, dest, lookup_table):
        if cls._lookup(lookup_table, file.inode.inode_number) is not None:
            assert False                                                            # no hardlink is allowed
        elif isinstance(file, PySquashfsImage.file.RegularFile):
            with open(dest, "wb") as f:
                for block in file.iter_bytes():
                    f.write(block)
        elif isinstance(file, PySquashfsImage.file.Symlink):
            os.symlink(file.readlink(), dest)
        elif isinstance(file, (PySquashfsImage.file.BlockDevice, PySquashfsImage.file.CharacterDevice)):
            assert False
        elif isinstance(file, PySquashfsImage.file.FIFO):
            assert False
        elif isinstance(file, PySquashfsImage.file.Socket):
            assert False
        else:
            assert False
        cls._insert_lookup(lookup_table, file.inode.inode_number, dest)

    @staticmethod
    def _lookup(lookup_table, number):
        index = PySquashfsImage.macro.LOOKUP_INDEX(number - 1)
        offset = PySquashfsImage.macro.LOOKUP_OFFSET(number - 1)
        if lookup_table.get(index) is None:
            return None
        return lookup_table[index].get(offset)

    @staticmethod
    def _insert_lookup(lookup_table, number, pathname):
        index = PySquashfsImage.macro.LOOKUP_INDEX(number - 1)
        offset = PySquashfsImage.macro.LOOKUP_OFFSET(number - 1)
        if lookup_table.get(index) is None:
            lookup_table[index] = {}
        lookup_table[index][offset] = pathname


class AioPoolWithJobAndLoadAverage:

    # this is a modified version of https://dgithub.xyz/gistart/asyncio-pool (v0.6.0)

    def __init__(self, jobs, loadAverage, loop=None):
        self.loop = loop or self._get_loop()

        self.jobs = jobs
        self.load_average = loadAverage
        self.size = jobs

        self._executed = 0
        self._joined = set()
        self._waiting = {}  # future -> task
        self._active = {}  # future -> task
        self.semaphore = asyncio.Semaphore(value=self.size)

    async def __aenter__(self):
        return self

    async def __aexit__(self, ext_type, exc, tb):
        await self.join()

    def __len__(self):
        '''Returns count of coroutines that is active or waiting.'''
        return len(self._waiting) + self.n_active

    @property
    def n_active(self):
        '''Counts active coroutines'''
        return len(self._active)

    @property
    def is_empty(self):
        '''Returns `True` if no coroutines are active or waiting.'''
        return 0 == len(self._waiting) == self.n_active                     # equvalent to `len(self) == 0`

    @property
    def is_full(self):
        '''Returns `True` if `size` coroutines are already active.'''
        return self.size <= len(self)                                      # in fact using `len(self) >= self.size` would be more understandable

    async def join(self):
        '''Waits (blocks) for all spawned coroutines to finish, both active and
        waiting. *Do not `join` inside spawned coroutine*.'''

        if self.is_empty:
            return True

        fut = self.loop.create_future()
        self._joined.add(fut)
        try:
            return await fut
        finally:
            self._joined.remove(fut)

    def _release_joined(self):
        if not self.is_empty:
            raise RuntimeError()  # TODO better message

        for fut in self._joined:
            if not fut.done():
                fut.set_result(True)

    def _build_callback(self, cb, res, err=None, ctx=None):
        # not sure if this is a safe code( in case any error:
        # return cb(res, err, ctx), None

        bad_cb = RuntimeError('cb should accept at least one argument')
        to_pass = (res, err, ctx)

        nargs = cb.__code__.co_argcount
        if nargs == 0:
            return None, bad_cb

        # trusting user here, better ideas?
        if cb.__code__.co_varnames[0] in ('self', 'cls'):
            nargs -= 1  # class/instance method, skip first arg

        if nargs == 0:
            return None, bad_cb

        try:
            return cb(*to_pass[:nargs]), None
        except Exception as e:
            return None, e

    async def _wrap(self, coro, future, cb=None, ctx=None):
        res, exc, tb = None, None, None
        try:
            res = await coro
        except BaseException as _exc:
            exc = _exc
            tb = traceback.format_exc()
        finally:
            self._executed += 1

        while cb:
            err = None if exc is None else (exc, tb)

            _cb, _cb_err = self._build_callback(cb, res, err, ctx)
            if _cb_err is not None:
                exc = _cb_err  # pass to future
                break

            wrapped = self._wrap(_cb, future)
            self.loop.create_task(wrapped)
            return

        self.semaphore.release()

        if not future.done():
            if exc:
                future.set_exception(exc)
            else:
                future.set_result(res)

        del self._active[future]
        if self.is_empty:
            self._release_joined()

    async def _spawn(self, future, coro, cb=None, ctx=None):
        acq_error = False
        try:
            await self.semaphore.acquire()
        except BaseException as e:
            acq_error = True
            coro.close()
            if not future.done():
                future.set_exception(e)
        finally:
            del self._waiting[future]

        if future.done():
            if not acq_error and future.cancelled():  # outside action
                self.semaphore.release()
        else:  # all good, can spawn now
            while True:
                if self.load_average is not None:
                    break                           # skip if no load average limit is specified
                if len(self._active) == 0:
                    break                           # there should always be at least one active task no matter what the load average is
                try:
                    avg = os.getloadavg()[0]        # load average of the shortest interval
                except OSError:
                    break                           # also spawn when we can not get load average, for robustness
                if avg < self.load_average:
                    break
                await asyncio.sleep(2)              # FIXME: is waiting 2 seconds the best? should refer to the implementation of "make -j X -l Y"
            wrapped = self._wrap(coro, future, cb=cb, ctx=ctx)
            task = self.loop.create_task(wrapped)
            self._active[future] = task
        return future

    def spawn_n(self, coro, cb=None, ctx=None):
        '''Creates waiting task for given `coro` regardless of pool space. If
        pool is not full, this task will be executed very soon. Main difference
        is that `spawn_n` does not block and returns future very quickly.

        Read more about callbacks in `spawn` docstring.
        '''
        future = self.loop.create_future()
        task = self.loop.create_task(self._spawn(future, coro, cb=cb, ctx=ctx))
        self._waiting[future] = task
        return future

    @staticmethod
    def _get_loop():
        """
        Backward compatibility w/ py<3.8
        """

        if hasattr(asyncio, 'get_running_loop'):
            return asyncio.get_running_loop()
        return asyncio.get_event_loop()
