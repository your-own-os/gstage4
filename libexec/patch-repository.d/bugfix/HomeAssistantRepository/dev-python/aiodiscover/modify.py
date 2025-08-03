#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        buf = re.sub(r">=dev-python/pyroute2-[0-9\.]+", "dev-python/pyroute2", buf, flags=re.M)

        # save and generate manifest
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
