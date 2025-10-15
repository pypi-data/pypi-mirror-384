from __future__ import annotations

import os
import winreg
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional


@dataclass(frozen=True)
class RegistryLocation:
    """Where to read a registry value (and which registry view)."""

    hive: int  # e.g. winreg.HKEY_CURRENT_USER
    subkey: str  # e.g. r"Software\Zemax"
    value_name: str  # e.g. "ZemaxRoot"
    view_flag: int  # winreg.KEY_WOW64_64KEY or _32KEY

    def _pretty(self) -> str:  # internal helper
        hive_name = {
            winreg.HKEY_CURRENT_USER: "HKCU",
            winreg.HKEY_LOCAL_MACHINE: "HKLM",
        }.get(self.hive, str(self.hive))
        view = "64-bit" if self.view_flag == winreg.KEY_WOW64_64KEY else "32-bit"
        return f"{hive_name}\\{self.subkey}\\{self.value_name} [{view}]"

    def __str__(self) -> str:
        return self._pretty()

    def __repr__(self) -> str:
        return f"<RegistryLocation {self._pretty()}>"


def read_reg(loc: RegistryLocation) -> Optional[str]:
    """
    Read a string/expandable string value from the registry.
    Returns expanded path string or None if missing / wrong type.
    """
    try:
        with winreg.OpenKeyEx(loc.hive, loc.subkey, 0, winreg.KEY_READ | loc.view_flag) as k:
            val, typ = winreg.QueryValueEx(k, loc.value_name)
    except (FileNotFoundError, PermissionError):
        return None

    if typ not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
        return None

    s = str(val).strip().strip('"')
    if typ == winreg.REG_EXPAND_SZ:
        s = os.path.expandvars(os.path.expanduser(s))
    return s or None


@dataclass
class DetectOut:
    path: Optional[Path] = None
    location: Optional[RegistryLocation] = None


def detect_into(candidates: Iterable[RegistryLocation], out: DetectOut) -> bool:
    """
    Iterate candidates; if a readable, existing directory path is found,
    write it into `out.path` and the matching `out.location`, then return True.
    Otherwise clear `out` and return False.
    """
    for loc in candidates:
        s = read_reg(loc)
        if not s:
            continue
        p = Path(s)
        if p.is_dir():  # directory expected
            out.path = p
            out.location = loc
            return True
    out.path = None
    out.location = None
    return False
