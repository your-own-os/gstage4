#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import sys
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
        while not bChecked:
            bChecked = True

            if not os.path.exists("Manifest"):
                # no manifest file means no need to run ebuild after modification
                break

            if pathlib.Path("../../profiles/repo_name").read_text().rstrip("\n") == "gentoo":
                # we have confidence that manifest generation in gentoo repository can succeed
                break

            try:
                print("s ", os.path.abspath(fn))
                out = subprocess.check_output(["ebuild", fn, "manifest"], stderr=subprocess.STDOUT)
                if len(out) == 0:
                    # manifest generation succeed, we can modify ebuild files
                    print("e ", os.path.abspath(fn))
                    break
            except subprocess.CalledProcessError:
                pass

            sys.exit(0)

        buf = buf.replace('SRC_URI="https://github.com/', 'SRC_URI="mirror://github/')
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
