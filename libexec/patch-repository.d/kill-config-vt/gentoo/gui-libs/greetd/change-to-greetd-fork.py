#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import os
import shutil

if not os.path.exists("greetd-9999.ebuild"):
    selfDir = os.path.dirname(os.path.realpath(__file__))
    shutil.copy(os.path.join(selfDir, "greetd-9999.ebuild"), "greetd-9999.ebuild")
else:
    print("outdated")
