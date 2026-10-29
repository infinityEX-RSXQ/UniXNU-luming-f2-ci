#!/usr/bin/env python3
"""Apply the ref-scout dada->luming clone recipe (REPORT-DADA-CLONE-RECIPE.md §6.3) to the skeleton.

Idempotent-ish: re-running re-copies the reference files and rewrites the generated blocks.
Sources are read-only: agents/official-crawl/recipe/cache/dada-full/.
"""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
D = Path(r'D:/civitoip20/agents/official-crawl/recipe/cache/dada-full')
U = Path(r'D:/civitoip20/unixnu-format2/UniXNU')


def copy(src, dst):
    src, dst = Path(src), ROOT / dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f'copied {src.relative_to(D) if src.is_relative_to(D) else src} -> {dst.relative_to(ROOT)}')


def retext(dst, pairs):
    path = ROOT / dst
    text = path.read_text()
    for old, new in pairs:
        text = text.replace(old, new)
    path.write_text(text)


def copy_builders():
    # kernel archive builders: storage base class, kext binding, PMGR instrument, ram block, boot log,
    # log reader. Rename the dada board names to luming while keeping the proven code/addresses.
    mapping = {
        'scripts/build-storage-classes.py': 'scripts/build-storage-classes.py',
        'scripts/build-storage-kext-bindings.py': 'scripts/build-storage-kext-bindings.py',
        'scripts/storage_abi_headers.py': 'scripts/storage_abi_headers.py',
        'scripts/build-dada-platform-power.py': 'scripts/build-luming-platform-power.py',
        'scripts/build-dada-ram-block.py': 'scripts/build-luming-ram-block.py',
        'scripts/build-dada-boot-log.py': 'scripts/build-luming-boot-log.py',
        'scripts/read-dada-log.py': 'scripts/read-luming-log.py',
    }
    for src, dst in mapping.items():
        copy(D / src, dst)
        if 'dada' in src:
            retext(dst, [('Dada', 'Luming'), ('DADA', 'LUMING'), ('dada', 'luming')])
    # drivers: copy the proven instrument and UFS transport; source identifiers stay as the ABI
    # expects (the runtime class remains NativeUfs / ApplePMGR), only the board directory is renamed.
    for src_name, dst_name in (('DadaPlatformPower', 'LumingPlatformPower'), ('DadaUfs', 'LumingUfs')):
        src_dir = D / 'drivers' / src_name
        dst_dir = ROOT / 'drivers' / dst_name
        if src_dir.is_dir():
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
            print(f'copied drivers/{src_name} -> drivers/{dst_name}')
            for path in dst_dir.rglob('*'):
                if path.is_file() and path.suffix in ('.py', '.toml', '.md', '.c', '.cpp', '.h', '.inc'):
                    text = path.read_text(errors='replace')
                    if 'Dada' in text or 'dada' in text:
                        path.write_text(text.replace('Dada', 'Luming').replace('dada', 'luming'))
    # UniXNU-side patches from the proven route
    for name in ('unixnu-payload-amfi-guard.patch', 'unixnu-ufs-archive-override.patch',
                 'unixnu-bootimg-header-v4.patch', 'unixnu-kern-exit-owner-cache.patch'):
        src = D / 'docs/patches' / name
        if src.is_file():
            copy(src, 'patches/unixnu/' + name)
        else:
            print(f'WARN missing UniXNU patch: {name}')


def copy_patches():
    device = ROOT / 'patches/xnu/device'
    active = []
    # dada's device patch series, renamed by board. Order from dada/patches/xnu/series.
    series_names = [
        'zzz-boot-progress-min.patch',
        'zzzzz-dada-entitlements-without-amfi.patch',
        'zzzzzz-dada-more-amfi-null-guards.patch',
        'zzzzzzz-dada-owner-cache-diagnostics.patch',
        'zzzzzzz-dada-cache-path.patch',
        'zzzzzzzz-dada-owner-cache-initproc-panic.patch',
        'zzzzzzzzz-dada-owner-cache-probe.patch',
        'zzzzzzzzzz-dada-owner-cache-root-list.patch',
        'zzzzzzzzzzz-dada-owner-cache-root-hex.patch',
        'zzzzzzzzzzzz-dada-owner-cache-dirent32.patch',
        'zzzzzzzzzzzzz-dada-owner-cache-lib-list.patch',
        'zzzzzzzzzzzzzz-dada-owner-cache-union-env.patch',
        'zzzzzzzzzzzzzzz-dada-no-cs-bringup.patch',
        'zzzzzzzzzzzzzzzzz-dada-sheng-pmgr-call.patch',
        'zzzzzzzzzzzzzzzzz-dada-ufs-log.patch',
        'zzzz-dada-skip-entitlement-acceleration-without-amfi.patch',
        'zzzz-dada-skip-root-auth-gate-without-owner-audit.patch',
    ]
    for name in series_names:
        src = D / 'patches/xnu' / name
        if not src.is_file():
            print(f'WARN missing dada patch: {name}')
            continue
        new = name.replace('dada', 'luming')
        copy(src, 'patches/xnu/device/' + new)
        if 'sheng-pmgr-call' in new:
            retext('patches/xnu/device/' + new, [('dada', 'luming'), ('Dada', 'Luming')])
        active.append(new)
    # fallback-only patches stay inactive; active list mirrors dada's series minus the no-AMFI fallbacks.
    fallback = {'zzzzz-luming-entitlements-without-amfi.patch',
                'zzzzzz-luming-more-amfi-null-guards.patch',
                'zzzzzzzzzzzzzzz-luming-no-cs-bringup.patch',
                'zzzz-luming-skip-entitlement-acceleration-without-amfi.patch',
                'zzzz-luming-skip-root-auth-gate-without-owner-audit.patch'}
    lines = ['# Device-owned xnu patch series (device: namespace). board.toml [kernel].patch_series',
             '# "device:patches/xnu/device/series" resolves this file.',
             '#',
             '# [adapted] from the proven dada route (agents/official-crawl/recipe/cache/dada-full/patches/xnu/,',
             '# renamed dada -> luming; patch bodies are byte-identical unless noted). These carry the',
             '# AMFI+PMGR trust path, owner-cache/SystemOS union and the sheng_pmgr_run() call from bsd_init.',
             '# Apply order matters: boot-progress-min first, then owner-cache/union, no-cs fallback,',
             '# sheng-pmgr call, then the UFS log instrument.',
             '#']
    for name in active:
        if 'no-cs-bringup' in name or 'entitlements-without' in name or 'null-guards' in name or 'skip-' in name:
            lines.append('# [fallback only, inactive] ' + name)
        else:
            lines.append(name)
    lines += ['# [fallback only] these no-AMFI patches are kept for debugging the PMGR instrument:',
              '# ' + ', '.join(sorted(fallback))]
    (device / 'series').write_text('\n'.join(lines) + '\n')
    print('wrote patches/xnu/device/series')


def copy_firmware_reference():
    src = D / 'docs/patches'
    for name in ('mu-silicium-bootshim-header-size.patch', 'mu-silicium-unixnu-components.patch',
                 'mu-silicium-unixnu-ramdisk.patch'):
        if (src / name).is_file():
            copy(src / name, 'firmware/patches/' + name)
    cfg = Path(r'D:/civitoip20/agents/official-crawl/recipe/cache/uefi-dada/Resources/Configs/dada.toml')
    if cfg.is_file():
        copy(cfg, 'firmware/reference-uefi-dada.toml')
        retext('firmware/reference-uefi-dada.toml', [('dada', 'luming'), ('Dada', 'Luming')])


def rewrite_board():
    path = ROOT / 'board.toml'
    text = path.read_text()

    # 1) header AMFI paragraph
    old = '''# OS profile decision (Lead direction, 2026-10-29): use the proven official profile that
# sheng and dada actually boot - ipados-17.7.11-21H461. Do not target iOS16/Darwin22:
# no official Darwin 22 profile exists and the only public skeleton (picasso) is
# abi_qualified=false. Alternatives are kept as comments only:'''
    new = '''# OS profile decision (Lead direction + clone recipe 2026-10-29): use the proven official
# profile that sheng and dada actually boot - ipados-17.7.11-21H461. Do not target
# iOS16/Darwin22: no official Darwin 22 profile exists and the only public skeleton
# (picasso) is abi_qualified=false. The prelink/AMFI/PMGR/owner-cache blocks below follow
# dada's current PROVEN shape (AMFI+PMGR+sandbox restored; see
# docs/reference/dada-known-values.md and agents/official-crawl/recipe/REPORT-DADA-CLONE-RECIPE.md).
# Alternatives are kept as comments only:'''
    text = text.replace(old, new)

    # 2) components comment: AMFI/PMGR are back in the prelink roots
    old = '''# Storage: ShengUfs is the catalog transport for the SHNGROOT + VerifiedRoot recipe; the luming
# SM8735 fork (NativeUfs/LumingUfs) is not a catalog component yet - dada solves this with its
# board-owned DadaUfs entry (docs/GAP-LIST.md #2, docs/UFS.md).
# Deliberately NOT prelinked for the first boot (dada no-AMFI shape): AMFI, PMGR, sandbox,
# IOHIDFamily, IOGPUFamily, IOMobileGraphicsFamily. Display/GopFramebuffer, Adreno and the
# input stack are later phases (docs/GAP-LIST.md #4/#5).'''
    new = '''# Storage: ShengUfs is the catalog transport for the SHNGROOT + VerifiedRoot recipe; the luming
# SM8735 fork (LumingUfs, cloned from dada's DadaUfs) is not a catalog component yet
# (docs/GAP-LIST.md #2, docs/UFS.md).
# The prelink roots below are dada's current proven 27-item set: AMFI, PMGR, sandbox and
# AppleImage4 are INCLUDED, while the GPU/graphics/HID families (IOGPUFamily,
# IOMobileGraphicsFamily, IOHIDFamily, IOHIDEventDriver) stay out until a display/input
# component exists (docs/GAP-LIST.md #4/#5).'''
    text = text.replace(old, new)

    # 3) archives: activate the copied board builders + storage-class pair; keep UFS component placeholder
    old_start = text.index('[kernel]')
    old_end = text.index('[kernel.prelink]')
    block = text[old_start:old_end]
    new_block = '''[kernel]
defconfig = "luming_defconfig"
# Official profile roots: arch:/soc:/os: series are owned by UniXNU profiles; device: is this repo.
# The vendored copies under configs/{arch,soc,os} and patches/xnu/{arch,os} are reference copies
# only; change the official files upstream, not these copies.
config_fragments = ["arch:configs/common.config", "soc:configs/sm8735.config", "os:configs/ipados.config"]
patch_series = ["arch:patches/xnu/series", "soc:patches/xnu/series", "os:patches/xnu/series", "device:patches/xnu/device/series"]
# Ordered archive plan, [adapted] from dada/board.toml [kernel] archives (the proven build).
# Storage needs the pinned IOBlockStorageDevice reference object (build-storage-classes.py) and the
# kext-binding pass (build-storage-kext-bindings.py) that rebinds base-class imports to the
# prelinked com.apple.iokit.IOStorageFamily addresses; compiling the base class instead registers a
# duplicate OSMetaClass. The copied builders live in scripts/ (see docs/REFERENCE-SOURCES.md).
archives = [
  "build-corecrypto-14.py",
  "build-corecrypto-14.py --namespace",
  "component:ArmDTPlatform",
  "component:ArmCpu",
  "component:SoftwareAES",
  "build-software-aes-bindings.py",
  "build-libpthread-kernel.py",
  "build-storage-classes.py",
  # [placeholder] component:LumingUfs is the fork of dada's DadaUfs; not a catalog component yet.
  "component:ShengUfs",
  "build-luming-platform-power.py",
  "build-storage-kext-bindings.py --component ShengUfs",
  "build-luming-ram-block.py",
  "build-luming-boot-log.py",
]

'''
    text = text[:old_start] + new_block + text[old_end:]

    # 4) prelink block: dada current proven 27-root AMFI+PMGR shape
    start = text.index('[kernel.prelink]')
    end = text.index('[device_tree]')
    roots = [
        'com.apple.AppleFSCompression.AppleFSCompressionTypeZlib',
        'com.apple.driver.AppleARMPlatform',
        'com.apple.driver.AppleARMWatchdogTimer',
        'com.apple.driver.AppleAudioClockLibs',
        'com.apple.driver.AppleEffaceableStorage',
        'com.apple.driver.AppleIISController',
        'com.apple.driver.AppleM2ScalerCSCDriver',
        'com.apple.driver.AppleMobileFileIntegrity',
        'com.apple.driver.ApplePMGR',
        'com.apple.driver.IODARTFamily',
        'com.apple.filesystems.apfs',
        'com.apple.iokit.CoreAnalyticsFamily',
        'com.apple.iokit.IOAVFamily',
        'com.apple.iokit.IOAudio2Family',
        'com.apple.iokit.IOCECFamily',
        'com.apple.iokit.IOCryptoAcceleratorFamily',
        'com.apple.iokit.IOHDCPFamily',
        'com.apple.iokit.IOReportFamily',
        'com.apple.iokit.IOSlowAdaptiveClockingFamily',
        'com.apple.iokit.IOStorageFamily',
        'com.apple.iokit.IOSurface',
        'com.apple.kec.Libm',
        'com.apple.kec.corecrypto',
        'com.apple.kext.AppleMatch',
        'com.apple.kext.CoreTrust',
        'com.apple.security.AppleImage4',
        'com.apple.security.sandbox',
    ]
    roots_text = '\n'.join(f'  "{root}",' for root in roots)
    prelink = f'''[kernel.prelink]
# [adapted] dada's current PROVEN prelink shape (agents/official-crawl/recipe/REPORT-DADA-CLONE-RECIPE.md
# §2, docs/reference/dada-known-values.md "Trust cache lock"/"Why AMFI is not prelinked" history).
# tool, kernel and kernelcache_sha256 stay inherited from the official OS profile; slide is
# dada's proven -0x1000000 (also the format-1 luming candidate).
slide = "-0x1000000"
# The AMFI early-security initializer is restored to the profile value so the kernel calls
# AppleMobileFileIntegrity's initializer before trust_cache_runtime_init(); dropping it (the
# intermediate no-AMFI variant) dead-ends in AMFI NULL walls after launchd.
early_security_init = "com.apple.driver.AppleMobileFileIntegrity=0xfffffff005ab4ae0"
# 27 roots: the profile's 31 minus the GPU/graphics/HID families that need components this board
# does not have yet (IOGPUFamily, IOMobileGraphicsFamily, IOHIDFamily, IOHIDEventDriver).
# AMFI, PMGR, sandbox and AppleImage4 are included on purpose.
roots = [
{roots_text}
]

'''
    text = text[:start] + prelink + text[end:]

    # 5) payload trust-cache pin (same 21H461 IPSW bundle as the profile)
    old = '''dram_size = "0x23ffff000"
panic_screen = false
'''
    new = '''dram_size = "0x23ffff000"
panic_screen = false
# [adapted] The profile pins two 21H461 trust-cache modules; the first hash is the bundle dada and
# sheng ship (`docs/reference/dada-known-values.md` "Trust cache"). The bundle itself is an input
# (--trust-cache) and is never stored in the repository.
trust_cache_sha256 = ["7416ca4f8377146626bb284e2133c76bee6cb4e3ee0af5d648b186235a7323a7"]
'''
    text = text.replace(old, new)

    # 6) kernel args: keep sheng-pmgr=2 (the PMGR instrument consumes it)
    old = '''  # [placeholder] driver args inherited from dada/format-1 luming; no luming driver publishes
  # these yet. Given to components we deliberately do not prelink or have not ported.
  "sheng-pmgr=2",
  "sheng-data-persist=2",'''
    new = '''  # PMGR instrument (copied from dada, same kernelcache/slide addresses) publishes the
  # ApplePMGRNub AMFI asks for; sheng-pmgr=2 selects it in bsd_init.
  "sheng-pmgr=2",
  "sheng-data-persist=2",'''
    text = text.replace(old, new)

    # 7) ADT: drop the stale no-AMFI amfi-only-platform-code override (profile value 1 applies now)
    old = '''[adt.chosen.u32]
# dada no-AMFI first boot: nothing reads the platform-code policy when AMFI is not prelinked.
# The profile's identity/security tuple (0,0,1,1) is inherited from ipados-17.7.11-21H461.
amfi-only-platform-code = 0
# [adapted] A-line panic-log finding: the size property lands here; the /pram node itself has no
# generic format-2 binding yet (docs/A-FIX-CROSSWALK.md (b) and docs/GAP-LIST.md #6).
embedded-panic-log-size = 1048576'''
    new = '''[adt.chosen.u32]
# The profile's identity/security tuple (0,0,1,1) and amfi-only-platform-code=1 are inherited from
# ipados-17.7.11-21H461. dada's stale no-AMFI override (0) and its comments are intentionally NOT
# copied: the proven HEAD restores AMFI/PMGR (recipe §2.2 "clone rule").
# [adapted] A-line panic-log finding: the size property lands here; the /pram node itself has no
# generic format-2 binding yet (docs/A-FIX-CROSSWALK.md (b) and docs/GAP-LIST.md #6).
embedded-panic-log-size = 1048576'''
    text = text.replace(old, new)

    # 8) firmware: FD base/size marker + reference config
    old = '''config = "luming"                              # Resources/Configs/luming.toml in the Mu-Silicium checkout'''
    new = '''# [unverified] candidate FD base/size from the SM8750-class Mu-Silicium boards and the local
# uefi-luming baseline: FD_BASE 0xA7100000, FD_SIZE 0x300000. Measure the luming reserved region
# or trial-boot before trusting it (recipe §4 "UEFI firmware" row).
config = "luming"                              # Resources/Configs/luming.toml (shape: firmware/reference-uefi-dada.toml)'''
    text = text.replace(old, new)
    path.write_text(text)
    print('rewrote board.toml prelink/archives/adt/payload/firmware blocks')


def rewrite_defconfig():
    text = '''# Kernel configuration of the f2-luming image. CONFIG_XNU_<NAME> becomes XNU_<NAME>.
#
# [adapted] from dada/configs/dada_defconfig (the PROVEN format-2 shape: AMFI+PMGR restored,
# owner-cache/SystemOS union on) with luming names. Every switch below mirrors dada's current
# defconfig unless a comment says otherwise; the copy source is
# agents/official-crawl/recipe/cache/dada-full/configs/dada_defconfig (see the clone recipe §2.1).

[archives]
CONFIG_XNU_BUILD_ARCHIVES=y
CONFIG_XNU_SOURCE_CORECRYPTO14=y
CONFIG_XNU_SOURCE_PTHREAD=y
CONFIG_XNU_ARM_DT_PLATFORM=y
CONFIG_XNU_ARMCPU=y

# [adapted] Storage: transport archive override for the luming fork of dada's DadaUfs.
# [placeholder] component:LumingUfs is not a catalog component yet; the boards selects ShengUfs as a
# placeholder and this path does not exist until the fork is wired (docs/UFS.md).
CONFIG_XNU_NATIVE_UFS=y
CONFIG_XNU_NATIVE_UFS_ARCHIVE="{tree}/build/luming-ufs/libLumingUfs.a"   # [placeholder]
CONFIG_XNU_NATIVE_AES=y

# AMFI is restored in the prelink roots; the trust-cache runtime must therefore be ON (dada's
# restored state, docs/reference/dada-known-values.md "Trust cache lock"). Turning it off is the
# intermediate no-AMFI variant, kept only as a fallback.
CONFIG_XNU_TRUST_CACHE_RUNTIME=y
CONFIG_XNU_NATIVE_CS_HASH_CACHE=y
CONFIG_XNU_NATIVE_ARCH_TIMER=y
CONFIG_XNU_NATIVE_PAN=y
CONFIG_XNU_BOOT_PROGRESS=n
CONFIG_XNU_DT_PANIC_REGION=y

# Data seed carrier and the owner/SHNGROOT chain (dada current proven switches).
CONFIG_XNU_NATIVE_RAM_BLOCK=y
CONFIG_XNU_LUMING_BOOT_LOG=y
CONFIG_XNU_OWNER_DATA_MOUNT=y
CONFIG_XNU_OWNER_BOOT_MANIFEST=y
CONFIG_XNU_OWNER_DATA_VOLUME_UUID="BA3B9FFA-0E35-4DE1-B942-E291D7BD5B52"
CONFIG_XNU_OWNER_CACHE_MOUNT=y
CONFIG_XNU_OWNER_CACHE_VOLUME_UUID="8846FE78-2910-4297-AF97-D59BB6F8FC16"
CONFIG_XNU_OWNER_CACHE_STARTUP=y
CONFIG_XNU_OWNER_UNION_SYSTEMOS=y

CONFIG_XNU_CRYPTO_BOOTSTRAP="prelinked"

# Explicitly off for the first milestone (dada keeps them off; the text console comes from
# DarwinBoot boot_args.Video and pexpert, not from a display component):
#   ADRENO/MOBILE_DISPLAY/LEGACY_DISPLAY - no gen8-6-0 GPU component
#   ARMVIRT_PLATFORM - not QEMU
#   SOURCE_MOCKFS - test fixture
CONFIG_XNU_NATIVE_ADRENO=n
CONFIG_XNU_SHENG_PMGR=y          # sheng/ApplePMGR instrument publishes ApplePMGRNub (sheng-pmgr=2)
CONFIG_XNU_NATIVE_MOBILE_DISPLAY=n
CONFIG_XNU_ARMVIRT_PLATFORM=n
CONFIG_XNU_SOURCE_MOCKFS=n
CONFIG_XNU_NATIVE_LEGACY_DISPLAY=n
CONFIG_XNU_VERIFIED_ROOT_PROBE=n
'''
    (ROOT / 'configs/luming_defconfig').write_text(text)
    print('rewrote configs/luming_defconfig')


def rewrite_docs():
    r = ROOT
    # README: replace the "does not build" AMFI bullet and add trust cache/PMGR facts
    p = r / 'README.md'
    t = p.read_text()
    t = t.replace(
        '''5. **AMFI-less entitlement guards** (dada patches) and luming display/input components are needed
   before userland exec and GUI.''',
        '''5. **AMFI/PMGR/owner-cache path**: the prelink roots, `early_security_init`, defconfig switches,
   trust-cache pin and the copied `build-luming-platform-power.py`/storage builders now follow dada's
   proven AMFI+PMGR shape (`docs/reference/dada-known-values.md`, clone recipe §2). The
   no-AMFI entitlement-guard patches are kept as fallback only; UI needs display/input components.''')
    t = t.replace(
        '`board.toml` selects the **proven official profile `ipados-17.7.11-21H461`**',
        '`board.toml` selects the **proven official profile `ipados-17.7.11-21H461`**')
    p.write_text(t)

    # KNOW-VALUES: replace section 7 AMFI row
    p = r / 'docs/KNOWN-VALUES.md'
    t = p.read_text()
    t = t.replace(
        '''| AMFI | intentionally NOT prelinked (dada no-AMFI configuration); trust-cache runtime off; AMFI-less entitlement guards required before userland exec | DADA; GAP-LIST #9 |''',
        '''| AMFI/PMGR | **restored to the proven dada shape**: 27 prelink roots include AppleMobileFileIntegrity + ApplePMGR + sandbox + AppleImage4; `early_security_init` = profile value; trust-cache runtime on; `build-luming-platform-power.py` (copied DadaPlatformPower) publishes the ApplePMGRNub | DADA `docs/known-values.md` "Trust cache lock"/"PMGR instrument"; `agents/official-crawl/recipe/REPORT-DADA-CLONE-RECIPE.md` §2 |
| Trust cache pin | `7416ca4f8377146626bb284e2133c76bee6cb4e3ee0af5d648b186235a7323a7` (21H461 bundle of two v2 modules) | profile `[payload] trust_cache_sha256`; recipe §2.2 |''')
    p.write_text(t)

    # GAP-LIST #9 rewrite
    p = r / 'docs/GAP-LIST.md'
    t = p.read_text()
    t = t.replace(
        '''| 9 | P1 | **AMFI/PMGR absent by design.** First boot is dada's no-AMFI route; userland `exec` will hit the NULL-AMFI entitlement path (`IOTaskHasEntitlement`, `IOUserClient::copyClientEntitlement`) without dada's AMFI-less guard patches. | userland exec (launchd) in the S6/S7 phase | dada's `patches/xnu/zzzzz-dada-entitlements-without-amfi.patch` + `zzzzzz-dada-more-amfi-null-guards.patch` (not cached) or the sheng AMFI+PMGR instrument (`build-sheng-platform-power.py` analogue) | dada repo `patches/xnu/`; sheng `scripts/build-sheng-platform-power.py` |''',
        '''| 9 | P1 | **AMFI/PMGR/owner-cache path must be validated on SM8735.** The skeleton now copies dada's proven shape (27 roots incl AMFI+PMGR, `early_security_init`, trust-cache runtime on, owner-cache/union switches, `build-luming-platform-power.py` with the same kernelcache/slide addresses, trust-cache pin). It has never run on luming. | userland exec/root chain | run the copied builders and patches; verify PMGR bindings on the luming prelink; fallback: no-AMFI entitlement-guard patches (copied, inactive in the device series) | `patches/xnu/device/series`, `scripts/build-luming-platform-power.py`, `firmware/patches/`; recipe §2.2 |''')
    t = t.replace(
        '''| 15 | P2 | **Trailing `[kernel.prelink] early_security_init = ""` semantics unverified.** Clearing an inherited profile scalar in format 2 has not been tested against the resolver. | prelink may still carry the AMFI initializer (or reject an empty value) | the dada→luming clone recipe's exact key/clearing idiom, then validate with `unixnu status --json` | `agents/official-crawl/recipe/REPORT-DADA-CLONE-RECIPE.md` (pending); dada `docs/known-values.md` "Why AMFI is not prelinked" |''',
        '''| 15 | P2 | **Prelink values are copied, not re-measured.** `[kernel.prelink]` now copies dada's current 27-root AMFI+PMGR shape and `early_security_init` value (same 21H461 kernelcache/slide), but the resolver has not been run against this board yet. | G2 prelink gate | `unixnu status --json` + prelink report must show 27 roots incl AMFI+PMGR and the early-security initializer; compare with `docs/evidence/kernel-build.json` in the dada reference | `agents/official-crawl/recipe/cache/dada-full/docs/evidence/kernel-build.json`; recipe §2.1 |''')
    p.write_text(t)

    # A-FIX-CROSSWALK a12 rewrite
    p = r / 'docs/A-FIX-CROSSWALK.md'
    t = p.read_text()
    t = t.replace(
        '''| a12 | **`com.apple.driver.AppleMobileFileIntegrity`/`ApplePMGR` removal from prelink roots** | dada reference (`docs/reference/dada-known-values.md`); no AMFI panic `AMFI: No PMGR?y` | This one **is** carried forward: board.toml `[kernel.prelink] roots` is dada's 24-root no-AMFI set; `early_security_init` is cleared. |''',
        '''| a12 | **`com.apple.driver.AppleMobileFileIntegrity`/`ApplePMGR` restore in the prelink roots** | dada current HEAD / clone recipe §2.1: 27 roots incl AMFI+PMGR+sandbox+AppleImage4, `early_security_init` restored, trust-cache runtime on. The earlier 24-root no-AMFI variant is documented history (`known-values.md` "Why AMFI is not prelinked") and dead-ends after launchd. | Carried forward as the proven shape: board.toml `[kernel.prelink]` 27 roots + early init; defconfig trust-cache/owner switches; copied `build-luming-platform-power.py`; trust-cache pin. |''')
    t = t.replace(
        '''| b11 | **iOS16 20H392 SHNGROOT userdata image** (`build/ios16-root/luming/userdata/userdata-root.img`) | `agents/roots-userspace/route-b/verified-inventory.json` | Not used on the chosen route (Lead decision: official iOS17-era profile, sheng SHNGROOT recipe); recorded in `docs/KNOWN-VALUES.md` #4 as retired alternative | Reusable only if the project ever returns to an iOS16/Darwin22 profile. |''',
        '''| b11 | **iOS16 20H392 SHNGROOT userdata image** (`build/ios16-root/luming/userdata/userdata-root.img`) | `agents/roots-userspace/route-b/verified-inventory.json` | Not used on the chosen route (official iPadOS 17.7.11 profile; sheng SHNGROOT recipe); recorded in `docs/KNOWN-VALUES.md` #4 as retired alternative | Reusable only if the project ever returns to an iOS16/Darwin22 profile. |''')
    p.write_text(t)

    # UFS doc: dada-fork + SM8735 offsets
    p = r / 'docs/UFS.md'
    t = p.read_text()
    t = t.replace('## Component shape (from dada\'s proven DadaUfs)', '## Component shape (from dada\'s proven DadaUfs, copied into drivers/LumingUfs)')
    p.write_text(t)

    # porting.toml: configuration/storage/power findings mention no-AMFI -> corrected
    p = r / 'porting.toml'
    t = p.read_text()
    t = t.replace('dada-shaped no-AMFI kernel configuration', 'dada-shaped AMFI+PMGR kernel configuration')
    t = t.replace('the closest no-AMFI source-XNU format-2 device', 'the closest proven source-XNU format-2 device (AMFI+PMGR restored)')
    t = t.replace('the no-AMFI first boot may need dada\'s AMFI-less entitlement guards before userland exec', 'the owner-cache/union and trust-cache path must be validated on SM8735; the copied AMFI-less guard patches are fallback only')
    p.write_text(t)


def main():
    copy_builders()
    copy_patches()
    copy_firmware_reference()
    rewrite_board()
    rewrite_defconfig()
    rewrite_docs()
    print('recipe applied')


if __name__ == '__main__':
    main()
