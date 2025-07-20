#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()
        buf2 = buf.replace('baseuri=\"https://github.com/', 'baseuri=\"mirror://github/')
        if buf == buf2:
            raise ValueError()
        pathlib.Path(fn).write_text(buf2)
except ValueError:
    print("outdated")
