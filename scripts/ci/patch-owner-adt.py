#!/usr/bin/env python3
"""Owner ADT fixups for the public CI checkout.

1. XNU's IODeviceTreeSupport registers AAPL,phandle, not Linux phandle.
2. Inject the 229-byte iPadOS root-hash blob as system-volume-auth-blob on the
   ADT root and /chosen so APFS root authentication has the Apple payload.
"""
from pathlib import Path
import sys

path = Path(sys.argv[1] if len(sys.argv) > 1 else 'unixnu/scripts/unixnu/devicetree.py')
source = path.read_text(encoding='utf-8')

# 1) AAPL,phandle (idempotent)
old = "            properties.append((key, struct.pack('<I', entry.scalar(key))))\n"
new = (
    "            name = 'AAPL,phandle' if key in ('phandle', 'linux,phandle') else key\n"
    "            if not any(existing == name for existing, _ in properties):\n"
    "                properties.append((name, struct.pack('<I', entry.scalar(key))))\n"
)
if old in source:
    source = source.replace(old, new, 1)
elif "AAPL,phandle" not in source:
    raise SystemExit('devicetree.py: phandle conversion block not found')

# 2) auth blob setup in generate(), after options are resolved.
marker = "    options = payload.get('adt', {})\n"
auth_setup = (
    "    options = payload.get('adt', {})\n"
    "    auth_blob = b''\n"
    "    auth_path = os.environ.get('UNIXNU_SYSTEM_VOLUME_AUTH_BLOB')\n"
    "    if auth_path:\n"
    "        auth_blob = Path(auth_path).read_bytes()\n"
    "        if len(auth_blob) != 229:\n"
    "            raise Error('system-volume-auth-blob must be the 229-byte root hash')\n"
)
if marker in source and 'auth_blob = b\'\'' not in source:
    source = source.replace(marker, auth_setup, 1)
elif 'auth_blob = b\'\'' not in source:
    raise SystemExit('devicetree.py: generate() options marker not found')

# 3) add it to /chosen and the ADT root after the platform tables are merged.
chosen_marker = "    chosen += typed_properties(platform.get('chosen', {}))\n"
chosen_inject = (
    "    chosen += typed_properties(platform.get('chosen', {}))\n"
    "    if auth_blob:\n"
    "        chosen.append(('system-volume-auth-blob', auth_blob))\n"
)
if chosen_marker in source and "chosen.append(('system-volume-auth-blob', auth_blob))" not in source:
    source = source.replace(chosen_marker, chosen_inject, 1)

root_marker = "    if not any(key == 'model' for key, _ in root_properties):\n"
root_inject = (
    "    if auth_blob:\n"
    "        root_properties.append(('system-volume-auth-blob', auth_blob))\n"
    "    if not any(key == 'model' for key, _ in root_properties):\n"
)
if root_marker in source and "root_properties.append(('system-volume-auth-blob', auth_blob))" not in source:
    source = source.replace(root_marker, root_inject, 1)

if 'AAPL,phandle' not in source:
    raise SystemExit('AAPL,phandle fix missing after patch')
if 'system-volume-auth-blob' not in source:
    raise SystemExit('auth blob injection missing after patch')
path.write_text(source, encoding='utf-8')
print('owner ADT fixed:', path)
