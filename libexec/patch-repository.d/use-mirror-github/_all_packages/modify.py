#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib
import subprocess

try:
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()

        if 'SRC_URI="https://github.com/' not in buf:
            continue

        # check all ebuild files in this package, don't do modification if check failed
        try:
            out = subprocess.check_output(["ebuild", fn, "manifest"], stderr=subprocess.STDOUT)
            if len(out) > 0:
                break
        except subprocess.CalledProcessError:
            break

        buf = buf.replace('SRC_URI="https://github.com/', 'SRC_URI="mirror://github/')
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
