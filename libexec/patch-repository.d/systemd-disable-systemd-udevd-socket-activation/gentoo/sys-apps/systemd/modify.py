#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    # what to insert (with blank line in the beginning and the end)
    buf2 = r"""
# don't use socket activation for systemd-udevd
find "${D}" -name "*udev*socket*" | xargs rm -rf
sed -i '/Sockets=/d'                              ${D}/usr/lib/systemd/system/systemd-udevd.service
sed -i 's/After=.*/After=systemd-udevd.service/g' ${D}/usr/lib/systemd/system/systemd-udev-trigger.service
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
