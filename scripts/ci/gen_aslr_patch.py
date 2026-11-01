"""Generate a context-correct ASLR diagnostic patch for the pinned XNU source.

Runs in CI pre_build after `unixnu fetch`:
  1. copies osfmk/kern/exception.c and bsd/vm/vm_unix.c from the fetched XNU feed
  2. applies core patch series that touch those files (same order as build)
  3. applies codex's content-anchored instrumentation
  4. writes a git-format diff and enables it in the device series
"""
import glob
import shutil
import subprocess
import sys
from pathlib import Path

GIT = shutil.which("git") or "git"
TARGETS = ("osfmk/kern/exception.c", "bsd/vm/vm_unix.c")


def git(cwd, *args, check=True):
    r = subprocess.run([GIT, *args], cwd=str(cwd), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r


def main():
    core = Path(sys.argv[1]).resolve()          # unixnu core checkout
    feed = Path(sys.argv[2]).resolve()          # out/feeds/xnu-*
    out_patch = Path(sys.argv[3]).resolve()     # device/patches/xnu/device/zzzzz-cdx-generated-aslr.patch
    series = Path(sys.argv[4]).resolve()        # device/patches/xnu/device/series

    if not (feed / "osfmk/kern/exception.c").is_file():
        raise SystemExit(f"XNU feed not found: {feed}")

    tmp = out_patch.parent.parent.parent.parent / ".cache/cdx-patchgen"
    if tmp.exists():
        shutil.rmtree(tmp)
    (tmp / "osfmk/kern").mkdir(parents=True)
    (tmp / "bsd/vm").mkdir(parents=True)
    for rel in TARGETS:
        shutil.copy2(feed / rel, tmp / rel)
    git(tmp, "init", "-q")
    git(tmp, "add", "-A")
    git(tmp, "-c", "user.email=ci@local", "-c", "user.name=ci", "commit", "-qm", "base")

    series_files = []
    for p in [core / "profiles/arch/arm64/patches/xnu/series"]:
        if p.is_file():
            series_files.append(p)
    for p in sorted(glob.glob(str(core / "profiles/soc/*/patches/xnu/series"))):
        series_files.append(Path(p))
    for p in sorted(glob.glob(str(core / "profiles/os/*/patches/xnu/series"))):
        series_files.append(Path(p))

    applied = 0
    for s in series_files:
        for line in s.read_text(encoding="utf-8").splitlines():
            entry = line.strip()
            if not entry or entry.startswith("#"):
                continue
            patch = (s.parent / entry).resolve()
            if not patch.is_file():
                continue
            text = patch.read_text(encoding="utf-8", errors="ignore")
            if not any(t in text for t in TARGETS):
                continue
            r = git(tmp, "apply", "-p1", "--unsafe-paths", "--recount", str(patch), check=False)
            if r.returncode != 0:
                raise SystemExit(f"cannot replay core patch {patch.name}: {r.stderr.strip()}")
            applied += 1
    if applied:
        git(tmp, "add", "-A")
        git(tmp, "-c", "user.email=ci@local", "-c", "user.name=ci", "commit", "-qm", "core")

    inst = Path(__file__).with_name("instrument_aslr_diagnostics.py")
    r = subprocess.run([sys.executable, str(inst), str(tmp)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"instrumentation failed: {r.stderr.strip()}")
    print(r.stdout.strip())

    diff = git(tmp, "diff", "--", *TARGETS).stdout
    if "sending exception" not in diff or "CDX_ASLR_MAP" not in diff:
        raise SystemExit("generated diff does not contain the diagnostics")
    out_patch.write_text(diff, encoding="utf-8")
    print(f"wrote {out_patch} ({len(diff)} bytes), replayed {applied} core patches")

    lines = [l for l in series.read_text(encoding="utf-8").splitlines()
             if "cdx-generated-aslr" not in l and "cdx-exception-aslr-diagnostic" not in l]
    insert_at = 0
    for i, l in enumerate(lines):
        if l.strip() and not l.lstrip().startswith("#"):
            insert_at = i
            break
    lines.insert(insert_at, "zzzzz-cdx-generated-aslr.patch")
    series.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"enabled zzzzz-cdx-generated-aslr.patch in {series}")


if __name__ == "__main__":
    main()
