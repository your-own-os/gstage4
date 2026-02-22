#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    s2 = "|| ( virtual/linux-sources virtual/dist-kernel )"
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()
        if s2 not in buf:
            raise ValueError(fn)
        buf = buf.replace(s2, "")
        pathlib.Path(fn).write_text(buf)
except ValueError as e:
    print("outdated " + str(e))
