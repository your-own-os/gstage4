#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

srcStr = r'rm -r "${ED}"/var'
dstStr = r'rm -rf "${ED}"/var'
try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()
        if srcStr not in buf:
            raise ValueError()
        buf = buf.replace(srcStr, dstStr)
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
