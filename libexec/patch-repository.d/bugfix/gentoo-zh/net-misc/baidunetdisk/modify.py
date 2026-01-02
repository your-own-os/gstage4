#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        buf2 = buf.replace("x11-libs/gtk+:3[cups]", "x11-libs/gtk+:3[X,cups]")
        if buf2 == buf:
            raise ValueError()
        buf = buf2

        # do insert
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
