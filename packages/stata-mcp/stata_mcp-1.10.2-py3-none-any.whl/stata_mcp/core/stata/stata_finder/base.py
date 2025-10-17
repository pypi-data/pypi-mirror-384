#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 - Present Sepine Tam, Inc. All Rights Reserved
#
# @Author : Sepine Tam (谭淞)
# @Email  : sepinetam@gmail.com
# @File   : base.py

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Iterable, List, Optional


class FinderBase(ABC):
    stata_cli: str = None

    def __init__(self, stata_cli: str = None):
        if stata_cli:
            self.stata_cli = stata_cli
        self.load_default_cli_path()

    def find_stata(self) -> str | None:
        if self.stata_cli:
            return self.stata_cli
        return self.finder()

    @abstractmethod
    def finder(self) -> str: ...

    @abstractmethod
    def find_path_base(self) -> Dict[str, List[str]]: ...

    @staticmethod
    def priority() -> Dict[str, List[str]]:
        name_priority = {
            "mp": ["stata-mp"],
            "se": ["stata-se"],
            "be": ["stata-be"],
            "default": ["stata"],
        }
        return name_priority

    @staticmethod
    def _is_executable(p: Path) -> bool:
        try:
            return p.is_file() and os.access(p, os.X_OK)
        except OSError:
            return False

    def load_cli_from_env(self) -> Optional[str]:
        self.stata_cli = os.getenv("stata_cli") or os.getenv("STATA_CLI")
        return self.stata_cli

    def load_default_cli_path(self) -> str | None:
        if self.stata_cli is not None:
            # try to load from env
            self.load_cli_from_env()
        return self.stata_cli

    def find_from_bin(self,
                      *,
                      priority: Optional[Iterable[str]] = None) -> str | None:
        pr = list(priority) if priority else ["mp", "se", "be", "default"]
        name_priority = self.priority()
        bins = self.find_path_base().get("bin")

        ordered_names: List[str] = []
        for key in pr:
            ordered_names.extend(name_priority.get(key, []))

        for b in bins:
            base = Path(b)
            for name in ordered_names:
                p = base / name
                if self._is_executable(p):
                    return str(p)
        return None
