#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        if "x11-libs/cairo[X,glib]" not in buf:
            raise ValueError()
        buf = buf.replace("x11-libs/cairo[X,glib]", "x11-libs/cairo[glib]")

        # do insert
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
