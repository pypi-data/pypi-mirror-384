#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam
# @Email  : sepinetam@gmail.com
# @File   : windows.py

import os
import re
import string


def get_available_drives():
    drives = []
    for letter in string.ascii_uppercase:
        if os.path.exists(f"{letter}:\\"):
            drives.append(f"{letter}:\\")
    return drives


def windows_stata_match(path: str) -> bool:
    """
    Check whether the given path matches the pattern of a Windows
    Stata executable.

    Args:
        path: Path string to be checked.

    Returns:
        bool: ``True`` if the path matches a Stata executable pattern,
        otherwise ``False``.
    """
    # Regular expression matching ``Stata\d+\Stata(MP|SE|BE|IC)?.exe``
    # ``\d+`` matches one or more digits (the version number)
    # ``(MP|SE|BE|IC)?`` matches an optional edition suffix
    pattern = r"Stata\d+\\\\Stata(MP|SE|BE|IC)?\.exe$"

    if re.search(pattern, path):
        return True
    return False
