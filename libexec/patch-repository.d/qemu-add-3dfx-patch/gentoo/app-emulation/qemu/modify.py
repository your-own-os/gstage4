#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import glob
import pathlib
import subprocess

os.makedirs("files", exist_ok=True)
subprocess.check_output(["git", "clone", "https://github.com/kjliew/qemu-3dfx", "files/qemu-3dfx"])
subprocess.check_output("rm -rf files/qemu-3dfx/.*", shell=True)

try:
    # what to insert (with blank line in the beginning and the end)
    buf2 = r"""
# apply 3dfx patch
cp -r ${FILESDIR}/qemu-3dfx/qemu-0/hw/3dfx hw
cp -r ${FILESDIR}/qemu-3dfx/qemu-1/hw/mesa hw
patch -p0 -i ${FILESDIR}/qemu-3dfx/00-qemu82x-mesa-glide.patch
bash ${FILESDIR}/qemu-3dfx/scripts/sign_commit
"""
    buf2 = buf2.replace("\n", "\n\t")
    buf2 += "\n"

    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        # insert to the end of src_install()
        pos = buf.find("src_prepare() {")
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
