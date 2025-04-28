#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()
        if "dev-libs/libappindicator:2" not in buf:
            raise ValueError()
        buf = buf.replace("dev-libs/libappindicator:2", "dev-libs/libappindicator")
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
