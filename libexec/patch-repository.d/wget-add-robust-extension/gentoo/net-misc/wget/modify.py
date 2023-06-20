#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import shutil
import pathlib

selfDir = os.path.dirname(os.path.realpath(__file__))
os.makedirs("files", exist_ok=True)
shutil.copyfile(os.path.join(selfDir, "files", "wget"), os.path.join("files", "wget"))

try:
    # what to insert (with blank line in the beginning and the end)
    buf2 = r"""
src_install() {
    default
    mv "${D}/usr/bin/wget" "${D}/usr/bin/wget-reference"
    dobin "${FILESDIR}/wget"
}
"""
    buf2 += "\n"

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert to the end of src_install()
        pos = buf.find("src_install() {")
        if pos >=0:
            raise ValueError()

        # do insert
        buf += buf2
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
