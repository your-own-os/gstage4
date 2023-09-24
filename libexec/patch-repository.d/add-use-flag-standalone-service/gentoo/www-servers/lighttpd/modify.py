#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    # what to insert (with blank line in the beginning and the end)
    buf2 = r"""
if ! use standalone-service ; then
    rm -rf ${D}/etc/lighttpd
    rm -rf ${D}/usr/lib/systemd
fi
"""
    buf2 = buf2.replace("\n", "\n\t")
    buf2 += "\n"

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert buf2 to the end of src_install()
        pos = buf.find("src_install() {")
        if pos == -1:
            raise ValueError()
        pos = buf.find("\n}\n", pos)
        if pos == -1:
            raise ValueError()
        pos += 1
        buf = buf[:pos] + buf2 + buf[pos:]

        # insert new use flag
        buf += '\nIUSE="${IUSE} standalone-service"\n'

        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
