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
import shutil
import subprocess
import PySquashfsImage


class Util:

    @staticmethod
    def listStartswith(theList, subList):
        return len(theList) >= len(subList) and theList[:len(subList)] == subList

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
                             universal_newlines=True)
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
                             shell=True, universal_newlines=True)
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
                             universal_newlines=True)
        if ret.returncode > 128:
            time.sleep(1.0)

    @staticmethod
    def portageIsPkgInstalled(rootDir, pkg):
        dir = os.path.join(rootDir, "var", "db", "pkg", os.path.dirname(pkg))
        if os.path.exists(dir):
            for fn in os.listdir(dir):
                if fn.startswith(os.path.basename(pkg)):
                    return True
        return False


class TempChdir:

    def __init__(self, dirname):
        self.olddir = os.getcwd()
        os.chdir(dirname)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self.olddir)


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

    def __exit__(self, type, value, traceback):
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

        # check history actions
        historyActionFuncNameList = ["action_" + x for x in self._persistStorage.getHistoryActionNames()]
        actionFuncNameList = [x._action_func_name for x in self._actionList]
        if not Util.listStartswith(actionFuncNameList, historyActionFuncNameList):
            raise self._errClass("invalid history actions")

        # self._lastActionIndex == -1 if no action has been executed
        self._lastActionIndex = len(historyActionFuncNameList) - 1

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

    def remove_action(self, action_name):
        idx = self._getActionIndex("action_" + action_name)
        assert self._lastActionIndex < idx

        # removes action from self._actionList
        # FIXME: no way to remove action method
        self._actionList.pop(idx)

        # do check
        self._assertActions()

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
