#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import subprocess

try:
    selfDir = os.path.dirname(os.path.realpath(__file__))
    for fullfn in glob.glob(os.path.join(selfDir, "files", "*.ebuild")):
        if os.path.exists(os.path.basename(fullfn)):
            raise ValueError()
        subprocess.check_call("cp %s ." % (fullfn), shell=True)
    subprocess.check_call("cp %s/files/files/* ./files" % (selfDir), shell=True)
except ValueError:
    print("outdated")
