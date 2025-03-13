#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()
        buf = buf.replace(r'MY_PV_GOG="2.0.0.9"', r'MY_PV_GOG="2.0.0.85"')
        buf = buf.replace(r'gog? ( ${MY_P_GOG}.sh )', r'gog? ( mirror://gog/${MY_P_GOG}.sh )')
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
