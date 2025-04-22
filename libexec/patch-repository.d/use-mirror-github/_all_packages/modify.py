#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import glob
import pathlib

try:
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()
        buf2 = buf.replace(r'SRC_URI="https://github.com/', r'SRC_URI="mirror://github/')
        if buf2 != buf:
            pathlib.Path(fn).write_text(buf2)
except ValueError:
    print("outdated")
