#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : macos.py

from typing import Dict, List

from .base import FinderBase


class FinderMacOS(FinderBase):
    def finder(self) -> str | None:
        stata_cli = self.find_from_bin()
        if stata_cli:
            return stata_cli
        return None

    def find_path_base(self) -> Dict[str, List[str]]:
        return {
            "bin": ["/usr/local/bin"],
            "application": ["/Applications"],
        }


if __name__ == "__main__":
    finder = FinderMacOS()
    print(finder.finder())
