#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import shutil
import pathlib

selfDir = os.path.dirname(os.path.realpath(__file__))
os.makedirs("files", exist_ok=True)
shutil.copyfile(os.path.join(selfDir, "files", "bnetd-wpad.patch"), os.path.join("files", "bnetd-wpad.patch"))

try:
    # what to insert (with blank line in the beginning and the end)
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert to the end of src_install()
        pos = buf.find("\tdefault\n")
        if pos == -1:
            raise ValueError()
        pos += 1

        # do insert
        buf = buf[:pos] + '\tPATCHES+=( "${FILESDIR}"/bnetd-wpad.patch )\n' + buf[pos:]
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
