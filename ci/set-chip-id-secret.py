#!/usr/bin/env python3
"""Set the fixed documented platform seed as a GitHub Actions repository secret.

Encrypts the value with libsodium sealed-box (PyNaCl from D:\\civitoip20\\tmp\\pynacl-lib)
and PUTs it to /repos/<repo>/actions/secrets/UNIXNU_UNIQUE_CHIP_ID.

The GitHub token is read from the GH_TOKEN environment variable supplied by the caller and
is never printed. Only the secret name and HTTP status are printed.
"""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, r"D:\civitoip20\tmp\pynacl-lib")
from nacl.public import PublicKey, SealedBox  # noqa: E402

REPO = "infinityEX-RSXQ/UniXNU-luming-f2"
SECRET_NAME = "UNIXNU_UNIQUE_CHIP_ID"
SECRET_VALUE = "addf4030"
API = "https://api.github.com"


def request(method, path, body=None, token=None):
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "luming-f2-ci-task328",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.status, json.loads(response.read() or b"{}")


def main():
    token = os.environ.get("GH_TOKEN", "")
    if not token:
        print("error: GH_TOKEN is not set", file=sys.stderr)
        return 2
    status, key = request("GET", f"/repos/{REPO}/actions/secrets/public-key", token=token)
    if status != 200 or "key" not in key or "key_id" not in key:
        print(f"error: public-key response status {status}", file=sys.stderr)
        return 1
    sealed = SealedBox(PublicKey(base64.b64decode(key["key"]))).encrypt(SECRET_VALUE.encode())
    body = {"encrypted_value": base64.b64encode(sealed).decode(), "key_id": key["key_id"]}
    status, _ = request("PUT", f"/repos/{REPO}/actions/secrets/{SECRET_NAME}", body=body, token=token)
    print(f"secret {SECRET_NAME} for {REPO}: HTTP {status}")
    # Verify the secret exists, without printing its value.
    status, listing = request("GET", f"/repos/{REPO}/actions/secrets", token=token)
    names = [item["name"] for item in listing.get("secrets", [])]
    if SECRET_NAME in names:
        print(f"verified: {SECRET_NAME} is present (value not printed)")
        return 0
    print(f"error: {SECRET_NAME} not listed after update", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
