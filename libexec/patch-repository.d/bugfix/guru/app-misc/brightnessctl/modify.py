#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

# blacklight device should be exported to /dev and has uaccess tag
# it needs work in kernel
try:
    # what to insert (with blank line in the beginning and the end)
    buf2 = r"""
sed -i 's/video/users/g' 90-brightnessctl.rules
"""
    buf2 = buf2.replace("\n", "\n\t")
    buf2 += "\n"

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert to the end of src_install()
        pos = buf.find("src_compile() {")
        if pos == -1:
            raise ValueError()
        pos = buf.find("\n}\n", pos)
        if pos == -1:
            raise ValueError()
        pos += 1

        # do insert
        buf = buf[:pos] + buf2 + buf[pos:]
        pathlib.Path(fn).write_text(buf)
except ValueError:
    print("outdated")
