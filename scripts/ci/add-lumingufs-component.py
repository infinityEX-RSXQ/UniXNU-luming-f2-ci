#!/usr/bin/env python3
"""Add the LumingUfs entry to the UniXNU component catalog in a CI checkout.

The upstream catalog at the pinned format-2 commit does not carry LumingUfs yet, and the
hand-maintained patch context drifts when the catalog gains entries. This appends the exact
component block instead, so the step is deterministic and context-free.

Usage: python3 add-lumingufs-component.py path/to/components.toml
"""
from __future__ import annotations

import sys
from pathlib import Path

COMPONENT = """
[[component]]
id = "LumingUfs"
repository_id = 0   # [placeholder] assign when the source repository is published
kind = "driver"
function = "SM8735 UFS transport and luming SHNGROOT storage"
scope = "board"
repository = "https://github.com/REQUIRED_OWNER/UniXNU-luming-ufs.git"   # [placeholder]
revision = "local"   # device module; published revision TBD
path = "drivers/LumingUfs"
hardware = ["SM8735 UFS controller", "apps_smmu stream 0x60"]
os_abi = ["ipados-17.7.11-21H461"]
board_dependencies = ["luming userdata SHNGROOT layout", "SM8735 GCC offsets and qmp-v4-niobe PHY hand-off"]
verified_devices = []
dependencies = ["VirtioMmioBlock", "VerifiedRoot"]
source_files = ["LumingUfs.cpp"]
runtime_identifiers = ["NativeUfs", "NativeUfs.cpp", "LumingUfs.cpp", "org.blu-sharky.NativeUfs"]
build_stage = "kernel"
build = ["build-arm-driver.py", "LumingUfs"]
outputs = ["build/luming-ufs/libLumingUfs.a"]
"""


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file():
        print(f"error: {path} does not exist", file=sys.stderr)
        return 1
    text = path.read_text(encoding="utf-8")
    if 'id = "LumingUfs"' in text:
        print(f"{path}: LumingUfs already present")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text + COMPONENT, encoding="utf-8")
    print(f"{path}: appended LumingUfs component")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
