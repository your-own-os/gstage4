#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        if "-DXRT_BUILD_DRIVER_HANDTRACKING=ON" not in buf:
            raise ValueError()
        buf = buf.replace("-DXRT_BUILD_DRIVER_HANDTRACKING=ON", "-DXRT_BUILD_DRIVER_HANDTRACKING=OFF")

        if "media-libs/opencv:= " not in buf:
            raise ValueError()
        buf = buf.replace("media-libs/opencv:= ", "media-libs/opencv:=[features2d] ")

        # do insert
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
