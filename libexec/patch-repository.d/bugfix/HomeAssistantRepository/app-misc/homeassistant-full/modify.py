#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import glob
import pathlib

try:
    for fn in glob.glob("*.ebuild"):
        buf = pathlib.Path(fn).read_text()

        buf = buf.replace("~dev-python/attrs", ">=dev-python/attrs")
        buf = buf.replace("~dev-python/bcrypt", ">=dev-python/bcrypt")
        buf = buf.replace("~dev-python/cryptography", ">=dev-python/cryptography")
        buf = buf.replace("~dev-python/h11", ">=dev-python/h11")
        buf = buf.replace("~dev-python/python-slugify", ">=dev-python/python-slugify")
        buf = buf.replace("~dev-python/pyudev", ">=dev-python/pyudev")
        buf = buf.replace("~dev-python/regex", ">=dev-python/regex")
        buf = re.sub(r"~dev-python/grpcio-[0-9\.]+", "dev-python/grpcio", buf)
        buf = re.sub(r"<dev-python/python-engineio-.*", "", buf, flags=re.M)

        # save and generate manifest
        with open(fn, "w") as f:
            f.write(buf)
except ValueError:
    print("outdated")
