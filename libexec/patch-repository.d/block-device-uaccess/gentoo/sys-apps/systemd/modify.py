#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    # what to insert (with blank line in the beginning and the end)
    buf2 = r"""
# we don't add uaccess tag onto block devices, so that we can eliminate udisks
sed -i -E ':x; /\\$/ { N; s/\\\n +//; tx }'   ${D}/usr/lib/udev/rules.d/70-uaccess.rules                                          # combind lines ends with \ to one line

sed -i '/# optical drives/i \
# all kinds of disks\
SUBSYSTEM=="block", TAG+="uaccess"\
' ${D}/usr/lib/udev/rules.d/70-uaccess.rules

sed -i -E 's/TAG=="uaccess", SUBSYSTEM!="sound"/TAG=="uaccess", SUBSYSTEM!="block|sound"/g' ${D}/usr/lib/udev/rules.d/71-seat.rules
## end ####"""
    buf2 = buf2.replace("\n", "\n\t")
    buf2 += "\n"

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert to the end of src_install()
        pos = buf.find("multilib_src_install_all() {")
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
