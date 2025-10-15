#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : _cli.py

import argparse
import sys

from .. import stata_mcp as mcp
from ..__version__ import __version__
from ..utils.Installer import Installer
from ..utils.usable import usable


def main() -> None:
    """Entry point for the command line interface."""
    parser = argparse.ArgumentParser(
        prog="stata-mcp",
        description="Stata-MCP command line interface",
        add_help=True)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"Stata-MCP version is {__version__}",
        help="show version information",
    )
    parser.add_argument(
        "-a", "--agent",
        action="store_true",
        help="run Stata-MCP as agent mode",
    )
    parser.add_argument(
        "--usable",
        action="store_true",
        help="check whether Stata-MCP could be used on this computer",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="install Stata-MCP to Claude Desktop")

    # mcp.run
    parser.add_argument(
        "-t",
        "--transport",
        choices=["stdio", "sse", "http", "streamable-http"],
        default=None,
        help="mcp server transport method (default: stdio)",
    )
    args = parser.parse_args()

    if args.usable:
        sys.exit(usable())
    elif args.install:
        Installer(sys_os=sys.platform).install()
    elif args.agent:
        from ..mode import run_agent_mode
        run_agent_mode()
    else:
        print("Starting Stata-MCP...")

        # Use stdio if there is no transport argument
        transport = args.transport or "stdio"
        if transport == "http":
            transport = (
                "streamable-http"  # Default to streamable-http for HTTP transport
            )
        mcp.run(transport=transport)
