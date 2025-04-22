#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import glob
import pathlib

try:
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()
        buf = buf.replace(r'SRC_URI="https://github.com/', r'SRC_URI="mirror://github/')
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
