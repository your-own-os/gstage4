#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # add --disable-mtab
        if buf.find("--enable-extras\n") < 0:
            raise ValueError()
        buf = buf.replace("--enable-extras\n", "--enable-extras \\\n --disable-mtab\n")

        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
