#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import sys
import glob
import pathlib
import subprocess

try:
    bChecked = False
    for fn in sorted(glob.glob("*.ebuild"), reverse=True):
        buf = pathlib.Path(fn).read_text()
        buf2 = buf

        for m in re.finditer(r'SRC_URI=".*?"', buf2, re.DOTALL):
            buf2 = buf2.replace(m.group(0), m.group(0).replace("https://github.com/", "mirror://github/"))

        for m in re.finditer(r'SRC_URI\+=".*?"', buf2, re.DOTALL):
            buf2 = buf2.replace(m.group(0), m.group(0).replace("https://github.com/", "mirror://github/"))

        for m in re.finditer(r'EGIT_REPO_URI=".*?"', buf2, re.DOTALL):
            buf2 = buf2.replace(m.group(0), m.group(0).replace("https://github.com/", "mirror://github/"))

        for m in re.finditer(r'EGIT_REPO_URI\+=".*?"', buf2, re.DOTALL):
            buf2 = buf2.replace(m.group(0), m.group(0).replace("https://github.com/", "mirror://github/"))

        # nothing changed
        if buf2 == buf:
            continue

        # do manifest file generation test, skip modification if test failed
        # this code only gets executed only once (by bChecked variable)
        while not bChecked:
            bChecked = True
            if re.search(r'^thin-manifests\s*=\s*true$', pathlib.Path("../../metadata/layout.conf").read_text(), re.MULTILINE):
                # "thin manifest" means ebuild file is not contained in manifest file, no need to re-generate manifest file after modification, test is not needed
                break
            if pathlib.Path("../../profiles/repo_name").read_text().rstrip("\n") == "gentoo":
                # we have confidence that manifest file generation in gentoo repository can succeed, test is not needed
                break
            if True:
                # FIXME: if this command runs forever (infinite retry download), then we would stuck here
                proc = subprocess.Popen(["ebuild", fn, "manifest"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = proc.communicate()
                if proc.returncode == 0 and len(err) == 0:
                    # we have confirmed that manifest file generation can succeed
                    break
            # test failed, do not modify any ebuild file
            sys.exit(0)

        # save to file
        pathlib.Path(fn).write_text(buf2)
except ValueError:
    print("outdated")
