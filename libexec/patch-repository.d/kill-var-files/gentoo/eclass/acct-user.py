#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import re
import pathlib

fn = "./acct-user.eclass"
try:
    buf = pathlib.Path(fn).read_text()

    # remove keepdir
    buf2 = re.sub('keepdir .*', 'true', buf, flags=re.M)
    if buf2 == buf:
        raise ValueError()
    buf = buf2

    # record and delete change owner and perm from preinst
    lines = buf.split("\n")
    recorded = None
    if True:
        start = -1
        end = -1
        start2 = -1
        end2 = -1
        for i in range(0, len(lines) - 1):
            if "acct-user_pkg_preinst" in lines[i]:
                start = i
                break
        if start == -1:
            raise ValueError()
        for i in range(start, len(lines) - 1):
            if lines[i] == "}":
                end = i
                break
        if end == -1:
            raise ValueError()
        for i in range(start, end):
            if "if [[ ${_ACCT_USER_HOME} != /dev/null ]]; then" in lines[i]:
                start2 = i
                break
        if start2 == -1:
            raise ValueError()
        for i in range(start2, end):
            if lines[i] == re.sub("if .*", "fi", lines[start2]):
                end2 = i
                break
        if end2 == -1:
            raise ValueError()
        recorded = lines[start2:end2+1]
        lines = lines[:start2] + lines[end2+1:]

    # modify recorded
    recorded = [x.replace('"${ED}/${_ACCT_USER_HOME#/}"', "${_ACCT_USER_HOME}") for x in recorded]
    recorded = [x.replace('fowners', "chown") for x in recorded]
    recorded = [x.replace('fperms', "chmod") for x in recorded]
    recorded = [
        "        if [[ ${_ACCT_USER_HOME} != /dev/null ]]; then",
        "                [[ -e ${_ACCT_USER_HOME} ]] || mkdir ${_ACCT_USER_HOME}",
        "        fi",
    ] + recorded

    # add to postinst
    start = -1
    start2 = -1
    for i in range(0, len(lines) - 1):
        if "acct-user_pkg_postinst" in lines[i]:
            start = i
            break
    if start == -1:
        raise ValueError()
    for i in range(start, len(lines) - 1):
        if "if [[ -n ${_ACCT_USER_ADDED} ]]; then" in lines[i]:
            start2 = i
            break
    if start2 == -1:
        raise ValueError()
    lines = lines[:start2] + recorded + lines[start2:]

    # save
    with open(fn, "w") as f:
        f.write("\n".join(lines) + "\n")
except Exception:
    print("outdated")
