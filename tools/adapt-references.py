#!/usr/bin/env python3
"""Materialise the f2-luming skeleton's [adapted] files from the read-only references.

Run from anywhere:  python agents/f2-luming/tools/adapt-references.py
No network, no device access. Every copy is recorded in docs/REFERENCE-SOURCES.md by the
maintainer; this script only performs the deterministic file copies/edits.

Reference roots (read-only):
  S = D:/civitoip20/unixnu-format2/UniXNU-sheng
  U = D:/civitoip20/unixnu-format2/UniXNU                 (base tool + profiles)
  C = D:/civitoip20/unixnu-format2/UniXNU-sm8735-common  (SM8735 scaffold)
  L = D:/civitoip20/UniXNU-luming                        (format-1 luming device repo)
  D = D:/civitoip20/agents/official-crawl/recipe/cache/dada-full (dada reference, cached)
  P = D:/civitoip20/agents/official-crawl/cache/repos/picasso-suzukir1n (iOS16 profile skeleton)
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
S = Path(r'D:/civitoip20/unixnu-format2/UniXNU-sheng')
U = Path(r'D:/civitoip20/unixnu-format2/UniXNU')
C = Path(r'D:/civitoip20/unixnu-format2/UniXNU-sm8735-common')
L = Path(r'D:/civitoip20/UniXNU-luming')
D = Path(r'D:/civitoip20/agents/official-crawl/recipe/cache/dada-full')
P = Path(r'D:/civitoip20/agents/official-crawl/cache/repos/picasso-suzukir1n')


def copy(src, dst, must=True):
    src, dst = Path(src), ROOT / dst
    if not src.exists():
        if must:
            raise SystemExit(f'missing reference: {src}')
        print(f'WARN missing reference: {src}')
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f'adapted {src} -> {dst.relative_to(ROOT)}')


def mkdirs():
    for rel in ('configs/arch', 'configs/soc', 'configs/os', 'patches/xnu/arch',
                'patches/xnu/soc', 'patches/xnu/os', 'patches/xnu/device', 'patches/unixnu',
                'firmware/patches', 'drivers/NativeUfs', 'drivers/LumingDisplayTouch',
                'package', 'kits', 'scripts/reference', 'soc', 'ci', 'docs/reference',
                'proposals/profiles/os/ios-16.7.16-20H392',
                '.github/workflows', 'tools'):
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def main():
    mkdirs()

    # --- repository hygiene / licence (copied verbatim from the sheng format-2 repo) ---
    copy(S / '.gitignore', '.gitignore')
    copy(S / '.gitattributes', '.gitattributes')
    copy(S / 'LICENSE', 'LICENSE')

    # --- arch and OS profile fragments: reference copies (official owners: UniXNU) ---
    copy(U / 'profiles/arch/arm64/configs/common.config', 'configs/arch/common.config')
    copy(U / 'profiles/arch/arm64/patches/xnu/series', 'patches/xnu/arch/series')
    copy(U / 'profiles/os/ipados-17.7.11-21H461/configs/ipados.config',
         'configs/os/ipados-17.7.11-21H461.config')
    copy(U / 'profiles/os/ipados-17.7.11-21H461/patches/xnu/series',
         'patches/xnu/os/series')

    # --- SM8735 SoC scaffold: vendored as a local `kind = "soc"` feed until published ---
    for rel in ('soc.toml', 'README.md', 'AGENTS.md', 'LICENSE', '.gitignore',
                'configs/sm8735.config', 'patches/xnu/series',
                'patches/xnu/native-smp-secondary.patch',
                'patches/xnu/sheng-platform-power.patch'):
        copy(C / rel, 'soc/' + rel)
    # The scaffold's dtsi is replaced by dts/sm8735.dtsi in this skeleton (measured facts added);
    # keep the original for diffing.
    copy(C / 'dts/sm8735.dtsi', 'soc/dts/sm8735.dtsi.scaffold')

    # --- format-1 luming package/scripts that carry real measured rules (reference copies) ---
    copy(L / 'package/unixnu.toml', 'package/unixnu.toml')
    copy(L / 'package/LumingKit/Kit.toml', 'package/LumingKit/Kit.toml')
    copy(L / 'package/README.md', 'package/README.md')
    copy(L / 'scripts/check-luming.py', 'scripts/reference/check-luming-format1.py')
    copy(L / 'patches/README.md', 'patches/xnu/device/reference-format1-patches.md')
    copy(L / 'configs/luming_defconfig', 'docs/reference/luming-format1_defconfig')

    # --- dada (Xiaomi 15, SM8750) format-2 reference: board shape, known values, patches ---
    copy(D / 'board.toml', 'docs/reference/dada-board.toml')
    copy(D / 'docs/known-values.md', 'docs/reference/dada-known-values.md')
    copy(D / 'docs/ufs-dada.md', 'docs/reference/dada-ufs.md')
    for name in ('mu-silicium-bootshim-header-size.patch', 'mu-silicium-unixnu-components.patch',
                 'mu-silicium-unixnu-ramdisk.patch', 'unixnu-bootimg-header-v4.patch',
                 'unixnu-kern-exit-owner-cache.patch'):
        copy(D / 'docs/patches' / name, 'firmware/patches/' + name)
    # UniXNU-side patches are not firmware patches; keep them visible under patches/unixnu.
    copy(D / 'docs/patches/unixnu-bootimg-header-v4.patch',
         'patches/unixnu/unixnu-bootimg-header-v4.patch')
    copy(D / 'docs/patches/unixnu-kern-exit-owner-cache.patch',
         'patches/unixnu/unixnu-kern-exit-owner-cache.patch')

    # --- picasso (SuzukiR1n/UniXNU-Picasso) iOS 16 / Darwin 22 profile skeleton (public) ---
    for rel in ('profiles/os/ios-16.7.16-20H392/profile.toml',
                'profiles/os/ios-16.7.16-20H392/patches/xnu/series',
                'docs/ios16.md'):
        src = P / rel
        dst = 'proposals/profiles/os/ios-16.7.16-20H392/' + Path(rel).name
        if Path(rel).name == 'series':
            dst = 'proposals/profiles/os/ios-16.7.16-20H392/patches-xnu-series'
        copy(src, dst, must=False)

    # --- upstream macOS CI workflow, kept as the unmodified reference ---
    copy(U / '.github/workflows/macos.yml', 'ci/unixnu-macos-reference.yml')
    copy(U / 'unixnu.example.toml', 'docs/reference/unixnu-example.toml')

    print('done: adapted references materialised')


if __name__ == '__main__':
    main()
