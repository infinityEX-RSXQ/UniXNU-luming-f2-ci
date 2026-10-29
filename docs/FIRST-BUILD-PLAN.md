# FIRST-BUILD-PLAN — f2-luming format-2 skeleton

Goal: produce the first format-2 luming artifacts on a CI/host machine, with explicit validation
gates before any device interaction. **No device operations are part of this plan**; the hardware
steps at the end are approval-gated and are listed only so the build artifacts have acceptance
criteria.

Host split (same as the official path):
- **Windows (this workspace)**: TOML/schema checks, file/series checks, reference diffs; no dtc,
  Xcode, hdiutil, mtools or apfs-fuse. Run `python agents/f2-luming/scripts/check-skeleton.py`.
- **Linux (WSL2/Ubuntu) or macOS**: kernel toolchain + dtc + payload/userdata tools. The official
  UniXNU macOS workflow is `.github/workflows/macos.yml` (adapted here); dada's proven first build
  used the official Linux toolchain at `/opt/unixnu-linux` (see `docs/reference/dada-known-values.md`
  "Host build, 2026-10-26").

## 0. Resolve the device repository (first thing to run)

From the UniXNU checkout (local reference: `D:/civitoip20/unixnu-format2/UniXNU`):

```sh
cd D:/civitoip20/unixnu-format2/UniXNU
./unixnu defconfig luming_defconfig -D ../../agents/f2-luming
./unixnu fetch     -D ../../agents/f2-luming     # needs network for the base feeds
./unixnu status --json -D ../../agents/f2-luming
./unixnu tree      -D ../../agents/f2-luming
```

Expected: device `luming`, SoC `sm8735` (local feed `soc/`), profile
`ipados-17.7.11-21H461`, output root `out/luming/ipados-17.7.11-21H461/luming/`, patch order
arch → soc → os → device, components from board.toml.

**Gate G0 (Windows, no network):** `python agents/f2-luming/scripts/check-skeleton.py` →
schema/fields/files/series/DTS/ADT static checks pass (warnings for the known external gaps).

**Gate G1 (resolver):** `status --json` shows the intended profile/SoC/components/patch order and
no unresolved `device:`/`soc:` reference.

## 1. Kernel (format 2 native build + prelink)

```sh
./unixnu ipsw info  -D ../../agents/f2-luming
./unixnu ipsw fetch -D ../../agents/f2-luming   # KernelCache/DeviceTree/StaticTrustCache/...
./unixnu build kernel -D ../../agents/f2-luming
```

This applies `config_fragments` + `luming_defconfig`, runs the `archives` builders
(corecrypto/pthread/ArmDTPlatform/ArmCpu/SoftwareAES/RamBlock/ShengUfs), builds XNU for
ARM64/BCM2837/DEVELOPMENT, and prelinks with `kits/XnuPrelink` against the profile's 21H461
kernelcache using the board's 24-root no-AMFI selection and slide `-0x1000000`.

**Gate G2 (kernel artifact):**
- `out/.../kernel/kernel.macho` exists; size and sha256 recorded in the payload report.
- prelink report shows the 24 roots from `board.toml`; **no** `AppleMobileFileIntegrity`, **no**
  `ApplePMGR`, **no** early-security initializer (or one explicitly cleared per the recipe).
- no missing archive: every board.toml `[kernel].archives` entry resolved to an existing builder
  (currently `build-storage-*` and `build-luming-*` are commented placeholders → the first build
  is expected to stop or link without storage; that is gap #2/#10, not a pass).

## 2. Package + firmware

```sh
./unixnu build package -D ../../agents/f2-luming
./unixnu build firmware -D ../../agents/f2-luming --uefi <path-to-uefi-luming>
```

Firmware acceptance (owned by uefi-builder, see `firmware/README.md`): FD size matches the
Mu-Silicium `[uefi_fd]` config; FD contains UniXNU, UniXNUDxe, UniXNURamDiskDxe, DarwinBoot,
DiskIoDxe and FAT.

**Gate G3:** `SILICIUM_UEFI.fd` sha256 + module list, `fd_sha256` recorded for the boot image.

## 3. Payload / userdata / boot image

```sh
# platform seed: a local secret, never stored in the repo
export UNIXNU_UNIQUE_CHIP_ID=<placeholder, measured on the phone>

./unixnu build payload -D ../../agents/f2-luming \
  --unique-chip-id "$UNIXNU_UNIQUE_CHIP_ID"
  # optional once the SHNGROOT/Data staging exists:
  # --data-ramdisk <data.dbr>  --trust-cache <trust.bundle>
./unixnu build userdata -D ../../agents/f2-luming
./unixnu bootimg -D ../../agents/f2-luming --uefi <path-to-uefi-luming> --dtb <firmware.dtb>
```

**Gate G4 (payload/boot image):**
- `payload.img` = 192 MiB FAT label `LUMINGESP`, contains `kernel.macho`, ADT, `unixnu.toml`.
- `boot.img` = **Android header v4**, size/FD/DTB hashes in `boot.json`, `ramdisk_bytes` nonzero.
- ADT: parse the sidecar and check `/cpus` (8 CPUs, MPIDR Aff1), `/arm-io/intc` regs, `/arm-io/ufshc`
  + `/arm-io/ufsphy` windows, `/chosen` dram-base/size = `0x8c0000000/0x23ffff000`, security/
  activation properties inherited from the profile, `amfi-only-platform-code=0`.
- boot image FDT contains the `splash_region` node (`0xfc800000/0x2b00000`).

**Gate G5 (host image validation, no device):** unpack the v4 header, verify kernel/ramdisk/dtb
offsets and hashes, mount/inspect the FAT payload, check `unixnu.toml` timeout/default, and record
`sha256` of every artifact in `docs/evidence/` (create when CI runs).

## 4. Device gates (approval required; not part of this plan's execution)

From UniXNU docs/porting/bring-up.md (S1-S7); all `fastboot boot` only until the user explicitly
approves a userdata write, never `flash`/`erase`/GPT changes:

1. **S1 firmware**: v4 boot image starts UEFI, FD size matches, framebuffer console appears,
   payload volume is published.
2. **S2 UniXNU**: menu/config loaded; Advanced Logger QR optional (agents/uefi-log line builds it).
3. **S3 payload / XNU entry**: DarwinBoot accepts the kernel+ADT; `DARWINBOOT:` lines.
4. **S4/S5 platform expert**: `/cpus`, `/arm-io`, `/defaults`, `/options`, NVRAM proxy.
5. **S6 storage/root**: UFS component publishes the userdata windows, root UUID
   `04769D26-2CA0-4825-B443-E2E5F88300F2` matches, SHNGROOT root mounts.
6. **S7 userland**: launchd + Data mount + display/console; documented separately.

Fallback: if ABL refuses the v4 format-2 boot image, the A-line/J2 handoff (`super` J2 payload +
AI6 boot image, auto-xnu timeout-0) is documented in `agents/ufs-ci/REPORT-UFS-CI.md` §4/§7. It is
a fastboot-only fallback and does not replace the format-2 route.

## 5. CI (macOS)

After this repository is published (private is acceptable):

```sh
gh workflow run macos.yml \
  -f unixnu_repository=UniXNU/UniXNU \
  -f unixnu_ref=main \
  -f device_ref=main \
  -f defconfig=luming_defconfig \
  -f steps="kernel"
gh run list --workflow=macos.yml -L 3
gh run download <RUN_ID> -n f2-luming-logs-<attempt> -D agents/f2-luming/docs/evidence/ci-<run>
```

The workflow checks out UniXNU + this device repo on `macos-26`, installs LLVM/LLD/mtools/dtc,
runs `defconfig`/`status`, builds kernel → package → (payload/userdata when selected) and uploads
redacted text logs only. Secrets used when present: `UNIXNU_IPSW`, `UNIXNU_UNIQUE_CHIP_ID`
(never printed; the payload step only).

**Gate G-CI:** workflow green for `steps="kernel"`; logs show the same G1/G2 evidence. Payload
steps are expected to fail until the platform seed / Data seed / firmware inputs exist (gaps #7/#8).

## 6. What can be validated on Windows offline today

- `scripts/check-skeleton.py`: TOML schema + required fields, component IDs against the local
  `UniXNU/components.toml`, config fragment and patch-series resolution (arch/os from the local
  UniXNU profiles, soc from the vendored `soc/` feed, device from this repo), DTS include and
  memory-size/payload cross-check, `[payload]`/`[payload.adt]`/`[adt]` sanity, boot-image v4 keys,
  missing external inputs report.
- Reference diffs: `docs/reference/dada-board.toml` vs `board.toml`; the vendored scaffold
  `soc/dts/sm8735.dtsi.scaffold` vs the corrected `soc/dts/sm8735.dtsi`.
- Porting-record structure check (if Python + the local UniXNU scripts are available):
  `python unixnu-format2/UniXNU/scripts/porting-record.py check --device agents/f2-luming`
  (may need git history; report actual output).
- Not possible on Windows: `dtc` compile, XNU build, prelink, payload/userdata/bootimg tools,
  image signing, hardware boot.
