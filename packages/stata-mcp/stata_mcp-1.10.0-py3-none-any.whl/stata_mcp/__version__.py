#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : __version__.py

from importlib.metadata import version

__version__ = version("stata-mcp")


def main():
    print(f"Stata-MCP: v{__version__}")


if __name__ == "__main__":
    main()
