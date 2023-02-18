#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import re
import glob
import pathlib

try:
    newFn = "train-valley-1.2.2.37064.ebuild"
    refBuf = None
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()

        buf = buf.replace(r'SRC_URI="', r'SRC_URI="mirror://gog/')
        buf = re.sub(r'RESTRICT="(.*)fetch(.*)"', r'RESTRICT="\1\2"', buf, re.M)

        if refBuf is None:
            refBuf = buf

        if newFn <= fn:
            os.unlink(fn)
        else:
            with open(fn, "w") as f:
                f.write(buf)

    with open(newFn, "w") as f:
        f.write(refBuf)

except ValueError:
    print("outdated")
