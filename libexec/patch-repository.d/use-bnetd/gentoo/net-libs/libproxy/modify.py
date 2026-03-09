#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import glob
import pathlib

try:
    # what to insert (with blank line in the beginning and the end)
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        if re.search(r'\bnet-wireless/wireless-regdb\b', buf) is None:
            raise ValueError()
        buf = re.sub(r'\bnet-wireless/wireless-regdb\b', "", buf)

        # do write
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
