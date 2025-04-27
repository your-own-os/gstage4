#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()
        buf2 = buf.replace("local mycmakeargs=(\n", "local mycmakeargs=(\n-DCMAKE_HIP_COMPILER_ROCM_ROOT=/usr\n")   # or else cmake will find HIP in /usr/local and fail
        if buf == buf2:
            raise ValueError()
        pathlib.Path(fn).write_text(buf2)
except ValueError:
    print("outdated")
