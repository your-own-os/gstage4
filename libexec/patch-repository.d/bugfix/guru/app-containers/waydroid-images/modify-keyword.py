#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

# sucks that -9999 has no keywords
try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()
        buf2 = buf.replace('S="${WORKDIR}"', 'KEYWORDS="~amd64 ~arm ~arm64 ~x86"\nS="${WORKDIR}"')
        if buf2 == buf:
            raise ValueError()
        pathlib.Path(fn).write_text(buf2)
except ValueError:
    print("outdated")
