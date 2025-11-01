#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import re
import glob
import shutil
import pathlib

try:
    selfDir = os.path.dirname(os.path.realpath(__file__))
    os.makedirs("files", exist_ok=True)
    shutil.copyfile(os.path.join(selfDir, "python3-config"), os.path.join("files", "python3-config"))

    buf2 = """
dobin ${FILESDIR}/python3-config
dosym python3-config /usr/bin/python-config
"""

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # remove script operation for python-config and python3-config
        m = re.search(r"local scripts=\((.+)\)", buf)
        if m is not None:
            s2 = m.group(0)
            s2 = s2.replace("python-config", "")
            s2 = s2.replace("python3-config", "")
            buf = buf.replace(m.group(0), s2)
        else:
            raise ValueError()

        # insert to the end of src_install()
        pos = buf.find("src_install() {")
        if pos == -1:
            raise ValueError()
        pos = buf.find("\n}\n", pos)
        if pos == -1:
            raise ValueError()
        pos += 1

        # do insert
        buf = buf[:pos] + buf2 + buf[pos:]

        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
