#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import glob
import pathlib

try:
    buf2 = """
## patch ####
find "${D}" -name "*chage*" | xargs rm -rf                  # for root to change a user's password expiration
find "${D}" -name "*chpasswd*" | xargs rm -rf               # change passwords in batch mode, obviously it's for root although it has a PAM config
find "${D}" -name "*pwck*" | xargs rm -rf
find "${D}" -name "*grpck*" | xargs rm -rf
find "${D}" -name "*pwconv*" | xargs rm -rf
find "${D}" -name "*pwunconv*" | xargs rm -rf
find "${D}" -name "*grpconv*" | xargs rm -rf
find "${D}" -name "*useradd*" | xargs rm -rf
find "${D}" -name "*usermod*" | xargs rm -rf
find "${D}" -name "*userdel*" | xargs rm -rf
find "${D}" -name "*newusers*" | xargs rm -rf               # create users in batch mode, obviously it's for root although it has a PAM config
find "${D}" -name "*groupadd*" | xargs rm -rf
find "${D}" -name "*groupmod*" | xargs rm -rf
find "${D}" -name "*groupdel*" | xargs rm -rf
rm -rf ${D}/etc/pam.d/shadow                                # this is the PAM config for user{add,del,mod} and group{add,del,mod}

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
