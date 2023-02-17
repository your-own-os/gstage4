#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    buf2 = """
## patch ####
find "${D}" -name "*chsh*" | xargs rm -rf
find "${D}" -name "*shfn*" | xargs rm -rf
[ -z "$(ls -A ${D}/etc/pam.d)" ] && rmdir ${D}/etc/pam.d
## end ####"""
    buf2 = buf2.replace("\n", "\n\t")
    buf2 += "\n"

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert to the end of src_install()
        pos = buf.find("src_install() {")
        if pos == -1:
            raise ValueError()
        pos = buf.find("\n}\n", pos)
        if pos == -1:
            raise ValueError()
        pos += 1
        buf = buf[:pos] + buf2 + buf[pos:]

        # save
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
