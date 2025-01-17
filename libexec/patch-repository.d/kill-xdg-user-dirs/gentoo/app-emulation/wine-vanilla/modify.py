#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # add --disable-mtab
        if buf.find("--disable-example\n") < 0:
            raise ValueError()
        buf = buf.replace("--disable-example\n", "--disable-example \\\n --disable-mtab\n")

        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
