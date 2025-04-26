#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()

        if 'SRC_URI="https://github.com/' not in buf:
            continue

        # we don't want to see the warning when generating manifest file if EAPI is too old
        bFound = False
        for eapi in ["8", "7", "6"]:
            if f'\nEAPI={eapi}' in buf or f'\nEAPI="{eapi}"' in buf or f"\nEAPI='{eapi}'" in buf:
                bFound = True
        if not bFound:
            continue

        buf = buf.replace('SRC_URI="https://github.com/', 'SRC_URI="mirror://github/')
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
