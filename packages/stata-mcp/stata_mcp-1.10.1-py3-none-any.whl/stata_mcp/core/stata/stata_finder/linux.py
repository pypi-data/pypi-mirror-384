#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : linux.py

from typing import Dict, List

from .base import FinderBase


class FinderLinux(FinderBase):
    def finder(self) -> str:
        pass

    def find_path_base(self) -> Dict[str, List[str]]:
        return {
            "bin": ["/usr/local/bin"],
        }


if __name__ == "__main__":
    finder = FinderLinux()
