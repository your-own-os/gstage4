#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import shutil
import pathlib

# don't allow USE flag gtk3, only allow USE flag gtk4
# don't allow USE flag pdfimport (it depends on xpdf so that depends on x11)

selfDir = os.path.dirname(os.path.realpath(__file__))
os.makedirs("files", exist_ok=True)
shutil.copyfile(os.path.join(selfDir, "files", "no-x11.patch"), os.path.join("files", "no-x11.patch"))

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # remove X use flag dependency
        buf = buf.replace("x11-libs/cairo[X]", "x11-libs/cairo")
        buf = buf.replace("[wayland,X]", "[wayland]")

        # disable skia since it doesn't have wayland backend, only have x11 backend
        buf = buf.replace("--with-x", "--with-x --disable-skia")

        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
