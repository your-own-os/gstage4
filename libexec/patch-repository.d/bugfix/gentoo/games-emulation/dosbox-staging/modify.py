#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        if "media-libs/libsdl2[joystick,opengl?,video,X]" not in buf:
            raise ValueError()
        buf = buf.replace("media-libs/libsdl2[joystick,opengl?,video,X]", "media-libs/libsdl2[joystick,opengl?,video]")

        # do insert
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
