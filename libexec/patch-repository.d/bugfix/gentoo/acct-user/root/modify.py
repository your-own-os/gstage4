#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        buf2 = buf.replace('/bin/bash', '/bin/sh')
        if buf == buf2:
            raise ValueError()
        buf = buf2

        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
