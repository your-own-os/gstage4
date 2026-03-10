#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import shutil

selfDir = os.path.dirname(os.path.realpath(__file__))

os.makedirs("files", exist_ok=True)
shutil.copyfile(os.path.join(selfDir, "files", "bnetd-wpad.patch"), os.path.join("files", "bnetd-wpad.patch"))
for fn in glob.glob("*.ebuild"):
    with open(fn, "a") as f:
        f.write('\nPATCHES=( ${PATCHES[@]} "${FILESDIR}"/bnetd-wpad.patch )\n')
