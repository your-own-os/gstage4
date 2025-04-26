#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import pathlib
import subprocess

bChecked = None
try:
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()

        if 'SRC_URI="https://github.com/' not in buf:
            continue

        # do manifest file generation test, don't modify if test failed
        while bChecked is None:
            if not os.path.exists("Manifest"):
                # no manifest file means no need to generate manifest file after modification, test is not needed
                bChecked = True
                break
            if pathlib.Path("../../profiles/repo_name").read_text().rstrip("\n") == "gentoo":
                # we have confidence that manifest file generation in gentoo repository can succeed, test is not needed
                bChecked = True
                break
            try:
                out = subprocess.check_output(["ebuild", fn, "manifest"], stderr=subprocess.STDOUT)
                if len(out) == 0:
                    # test succeeds, we can modify ebuild files
                    bChecked = True
                    break
            except subprocess.CalledProcessError:
                pass
            bChecked = False
            break
        if not bChecked:
            # test failed, skip modification
            break

        buf = buf.replace('SRC_URI="https://github.com/', 'SRC_URI="mirror://github/')
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
