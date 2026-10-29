#!/usr/bin/env python3
"""Apply the deep-graft top-3 corrections (REPORT-COMPONENT-GRAFT-MAP.md §0/§3.3)."""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
D = Path(r'D:/civitoip20/agents/official-crawl/recipe/cache/dada-full')
driver = ROOT / 'drivers' / 'LumingUfs'


def edit(path, pairs, must=True):
    path = Path(path)
    text = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if must and old not in text:
            print(f'WARN {path.name}: pattern not found: {old[:70]!r}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')
    print(f'edited {path.relative_to(ROOT)}')


def main():
    # 1) driver file rename: LumingUfs.cpp -> LumingUfs.cpp (builders resolve by filename)
    src = driver / 'LumingUfs.cpp'
    dst = driver / 'LumingUfs.cpp'
    if src.is_file():
        if dst.exists():
            dst.unlink()
        src.rename(dst)
        print('renamed drivers/LumingUfs/LumingUfs.cpp -> LumingUfs.cpp')
    # every remaining mention of the old filename in the skeleton, except the graft report/reference copies
    for path in ROOT.rglob('*'):
        if not path.is_file() or path.suffix not in ('.py', '.md', '.toml', '.h', '.cpp', '.inc', '.patch', '.sh'):
            continue
        if any(part in path.parts for part in ('docs/reference', 'deep-graft', 'firmware/build-tree')):
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        if 'LumingUfs.cpp' in text:
            path.write_text(text.replace('LumingUfs.cpp', 'LumingUfs.cpp'), encoding='utf-8')
            print(f'fixed filename reference: {path.relative_to(ROOT)}')

    # 2) GccUfs.h: AGGRE 0x770f0 -> 0x770f4; SM8735 wording
    edit(driver / 'GccUfs.h', [
        ('#ifndef NATIVE_UFS_GCC_UFS_H', '#ifndef NATIVE_UFS_GCC_UFS_H'),
        ('#define GCC_AGGRE_UFS_PHY_AXI_ENABLE  0x770f0',
         '#define GCC_AGGRE_UFS_PHY_AXI_ENABLE  0x770f4   // SM8735 "tuna": gcc-tuna.c:1459-1491 (SM8750: 0x770f0)'),
        ('SM8750', 'SM8735'),
        ('sm8750', 'sm8735'),
    ])

    # 3) LumingUfs.cpp: root partition + accepted compatibles + wording
    edit(driver / 'LumingUfs.cpp', [
        ('static const char kRootPartition[] = "linux";',
         'static const char kRootPartition[] = "userdata";   // luming GPT entry (measured 3,124,736..128,619,514)'),
        ('static const char *const accepted[] = { "qcom,ufshc", "qcom,sm8750-ufshc" };',
         'static const char *const accepted[] = { "qcom,ufshc", "qcom,sm8735-ufshc" };'),
        ('SM8750', 'SM8735'),
        ('sm8750', 'sm8735'),
    ])
    # Info.plist personality name (runtime class/bundle stay NativeUfs)
    edit(driver / 'Info.plist', [
        ('dada SM8750 UFSHCI', 'luming SM8735 UFSHCI'),
    ])

    # 4) facts test rename + SM8735 expectations
    facts = driver / 'tests' / 'check_sm8750_facts.py'
    target = driver / 'tests' / 'check_sm8735_facts.py'
    if facts.is_file():
        if target.exists():
            target.unlink()
        facts.rename(target)
        text = target.read_text(encoding='utf-8')
        text = text.replace('SM8750', 'SM8735').replace('sm8750', 'sm8735')
        text = text.replace('0x770f0', '0x770f4')
        text = text.replace('gcc-sm8735.c', 'gcc-tuna.c').replace('gcc_sm8735', 'gcc_tuna')
        text = text.replace("'qcom,sm8735-ufshc'", "'qcom,sm8735-ufshc'")
        text = text.replace('linux', 'userdata')
        target.write_text(text, encoding='utf-8')
        print('renamed tests/check_sm8750_facts.py -> check_sm8735_facts.py and updated expectations')

    # 5) driver README for the SM8735 fork
    (driver / 'README.md').write_text('''# LumingUfs

luming's UFS storage driver. Owns the SM8735 host-controller bring-up, the SMMU takeover, the
request queue, GPT/window parsing and the read-only root publication.

This is the board's own driver, derived from dada's SM8750 `DadaUfs` (which in turn forks the
`ShengUfs`/`NativeUfs` component). The fork changes only the board parameters:

- accepted controller names: `qcom,ufshc` and `qcom,sm8735-ufshc` (luming's stock DT uses the bare
  name; the SM8750 name and the SM8550 name are gone).
- GCC clock offsets: SM8735 "tuna" values in `GccUfs.h` (AXI 0x77018, AHB 0x77028, TX0 0x7702c,
  RX0 0x77030, UNIPRO 0x7706c, ICE 0x7707c, AUX 0x770bc, RX1 0x770d8, **AGGRE 0x770f4**; GDSC
  0x77004/0x9e000; sources: stock `gcc-tuna.c`, live DT).
- root partition: GPT entry **`userdata`** (`kRootPartition`), where the SHNGROOT manifest and the
  OS/SystemOS windows live (measured LBAs 3,124,736..128,619,514 at 4096 B).
- SMMU stream `0x60`, apps_smmu `0x15000000`; the driver adopts the firmware-left SMMU mapping
  (see `SmmuTakeover.h`, `docs/UFS.md`).
- PHY `qcom,ufs-phy-qmp-v4-niobe` `0x1d80000/0x2000`: the driver does not program the PHY; it relies
  on the firmware hand-off exactly like dada/sheng.
- optional policy arguments use the `luming-` prefix (`luming-log`, `luming-data-persist`,
  `luming-log-reserve`).
- `NativeUfs`/`NativeUfsBlock` runtime classes and the `Info.plist` bundle ID stay as the upstream
  ABI expects (`org.blu-sharky.NativeUfs`); the source file is `LumingUfs.cpp` because the board
  builders resolve it by name.

Linked into XNU by `unixnu build kernel` through `component:LumingUfs`. See
`docs/UFS.md`, `docs/reference/dada-ufs.md` and
`agents/f2-luming/deep-graft/REPORT-COMPONENT-GRAFT-MAP.md` for the value-by-value graft map.
''', encoding='utf-8')
    print('rewrote drivers/LumingUfs/README.md')

    # 6) board.toml: LumingUfs component + archive pair/order
    edit(ROOT / 'board.toml', [
        ('include = ["ArmDTPlatform", "ArmCpu", "SoftwareAES", "ShengUfs", "RamBlock",\n           "VerifiedRoot", "XnuPrelink", "DarwinBoot"]',
         'include = ["ArmDTPlatform", "ArmCpu", "SoftwareAES", "LumingUfs", "RamBlock",\n           "VerifiedRoot", "XnuPrelink", "DarwinBoot"]'),
        ('  # [placeholder] component:LumingUfs is the fork of dada\'s DadaUfs; not a catalog component yet.\n  "component:ShengUfs",',
         '  "component:LumingUfs",'),
        ('  "build-storage-kext-bindings.py --component ShengUfs",',
         '  "build-storage-kext-bindings.py --component LumingUfs",'),
        ('# Storage: ShengUfs is the catalog transport for the SHNGROOT + VerifiedRoot recipe; the luming\n# SM8735 fork (LumingUfs, cloned from dada\'s DadaUfs) is not a catalog component yet\n# (docs/GAP-LIST.md #2, docs/UFS.md).',
         '# Storage: LumingUfs is the board module (SM8735 fork of dada\'s DadaUfs) selected by the\n# board/device module; the catalog lineage is ShengUfs/NativeUfs. It is not a published catalog\n# component yet, so the resolver needs the local drivers/LumingUfs module (docs/UFS.md).'),
    ])

    # 7) kits/luming BootLog + BootProcessProbe (build-luming-boot-log.py sources)
    kit = ROOT / 'kits' / 'luming'
    kit.mkdir(parents=True, exist_ok=True)
    for name in ('BootLog.c', 'BootProcessProbe.c'):
        srcp = D / 'package' / name
        if srcp.is_file():
            shutil.copyfile(srcp, kit / name)
            print(f'copied package/{name} -> kits/luming/{name}')
        else:
            print(f'WARN missing dada package/{name}')
    # optional: the log writer prints a board tag; keep the upstream symbol names but label luming.
    blog = kit / 'BootLog.c'
    if blog.is_file():
        text = blog.read_text(encoding='utf-8')
        text = text.replace('return "dada";', 'return "luming";')
        blog.write_text(text, encoding='utf-8')

    # 8) tests README reference
    tests_readme = driver / 'tests' / 'README.md'
    if tests_readme.is_file():
        text = tests_readme.read_text(encoding='utf-8')
        text = text.replace('check_sm8750_facts', 'check_sm8735_facts').replace('SM8750', 'SM8735')
        tests_readme.write_text(text, encoding='utf-8')
    print('deep-graft top-3 applied')


if __name__ == '__main__':
    main()
