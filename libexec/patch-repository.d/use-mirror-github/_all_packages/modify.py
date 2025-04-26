#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
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

        # do manifest file generation test, skip modification if test failed
        while not bChecked:
            bChecked = True
            if re.search(r'^thin-manifests\s*=\s*true$', pathlib.Path("../../metadata/layout.conf").read_text(), re.MULTILINE):
                # "thin manifest" means ebuild file is not contained in manifest file, no need to re-generate manifest file after modification, test is not needed
                break
            if pathlib.Path("../../profiles/repo_name").read_text().rstrip("\n") == "gentoo":
                # we have confidence that manifest file generation in gentoo repository can succeed, test is not needed
                break
            try:
                subprocess.check_output(["ebuild", fn, "manifest"], stderr=subprocess.STDOUT)
                break
            except subprocess.CalledProcessError:
                # test failed, do not modify any ebuild file
                sys.exit(0)

        buf = buf.replace('SRC_URI="https://github.com/', 'SRC_URI="mirror://github/')
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
