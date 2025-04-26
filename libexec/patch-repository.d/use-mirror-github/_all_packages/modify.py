#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import pathlib
import subprocess

try:
    bChecked = False
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()

        if 'SRC_URI="https://github.com/' not in buf:
            continue

        # check all ebuild files in this package, don't do modification if check failed
        if not bChecked:
            if os.path.exists("Manifest"):
                try:
                    out = subprocess.check_output(["ebuild", fn, "manifest"], stderr=subprocess.STDOUT)
                    if len(out) > 0:
                        break
                except subprocess.CalledProcessError:
                    break
            else:
                # no manifest file means no need to run ebuild after modification
                pass
            bChecked = True

        buf = buf.replace('SRC_URI="https://github.com/', 'SRC_URI="mirror://github/')
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
