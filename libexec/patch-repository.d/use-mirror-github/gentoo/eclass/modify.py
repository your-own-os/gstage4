#!/usr/bin/python3
# -*- coding: utf-8; tab-width: 4; indent-tabs-mode: t -*-

import pathlib

fn = "git-r3.eclass"
try:
    buf = pathlib.Path(fn).read_text()

    # idx
    s = '\n\tlocal r\n\tfor r in "${repos[@]}"; do\n'
    idx = buf.find(s)
    if idx < 0:
        raise ValueError()

    # idx2
    s2 = '\n\t\tfi\n'
    idx2 = buf[idx:].find(s2)
    if idx2 < 0:
        raise ValueError()
    idx2 = idx + idx2

    # first insert after idx2, then insert before idx
    # FIXME: the whole script should die when portage-mrget fails
    buf = buf[:idx2 + len(s2)] + \
        '\t\trepos[$index]=$(/usr/libexec/gstage4/portage-mrget ${r})\n' + \
        '\t\t((index++))' + \
        buf[idx2 + len(s2):]
    buf = buf[:idx] + \
        '\n\tindex=0' + \
        buf[idx:]
    pathlib.Path(fn).write_text(buf)
except (FileNotFoundError, ValueError):
    print("outdated")
