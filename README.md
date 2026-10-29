# UniXNU luming (f2-luming) — format-2 bring-up skeleton

Device support skeleton for the Xiaomi Civi 5 Pro (`luming`, Qualcomm SM8735 "Tuna"), built on the
official **format-2** architecture (the sheng/dada "6S Pro way"): native 4K XNU from source +
XnuPrelink, in-tree/catalog components, Mu-Silicium UEFI + DarwinBoot, the official OS profile,
SHNGROOT userdata + VerifiedRoot, and a macOS CI workflow.

**Status: skeleton only. Resolve-able as a format-2 board; not buildable end-to-end yet, never
booted from this repository, no device operations performed.** See `docs/GAP-LIST.md` for every
missing input and `docs/FIRST-BUILD-PLAN.md` for the exact build/validation gates.

Status labels used in files: `[adapted]`, `[measured]`, `[placeholder]`, `[missing]` (defined in
`board.toml` header and `docs/REFERENCE-SOURCES.md`).

## OS profile decision

`board.toml` selects the **proven official profile `ipados-17.7.11-21H461`** (Darwin 23.6.0,
xnu-10063.141.1) that sheng (full iPadOS UI) and dada (launchd/SpringBoard/backboardd) actually
boot. The project direction is "any iOS is fine, just make iOS boot", so this skeleton does **not**
target iOS16/Darwin22. Alternatives are kept only as comments/traceability:

- `proposals/profiles/os/ios-16.7.16-20H392/` — public picasso skeleton, `abi_qualified=false`,
  no official UniXNU profile; not chosen.
- The retired iOS16 20H392 SHNGROOT image is recorded in `docs/KNOWN-VALUES.md` #4 but not used.

## Layout

| Path | Contents |
| --- | --- |
| `board.toml` | schema 2: board, kernel defconfig/archives/prelink (dada no-AMFI), firmware, payload, ADT, bootimg, userdata |
| `porting.toml` | format-2 porting record, 13 structured areas (all `planned`) |
| `feeds.toml`, `unixnu.lock`, `local.toml.example` | source pins and local overrides; the SM8735 feed is a local `soc/` scaffold |
| `configs/` | `luming_defconfig` (active), reference copies for arch/soc/os fragments |
| `dts/luming.dts` + `soc/dts/sm8735.dtsi` | board hardware, measured luming facts |
| `soc/` | vendored SM8735 SoC feed scaffold (from `unixnu-format2/UniXNU-sm8735-common`) |
| `patches/xnu/` | arch/os reference series, soc series (native-smp), device series (empty) |
| `patches/unixnu/` | UniXNU-side patches (header v4, owner-cache, missing ADT pram/asmb) |
| `firmware/` | uefi-luming interface + Mu-Silicium/DarwinBoot patches (**uefi-builder owns this**) |
| `drivers/` | component wrapper notes: NativeUfs (missing), DisplayTouch (missing) |
| `package/`, `kits/` | board package/kit (format-1 stub, re-derive later) |
| `scripts/` | `check-skeleton.py` (host validation) + format-1 reference preflight (**windows-ci owns**) |
| `docs/` | A-FIX-CROSSWALK, GAP-LIST, FIRST-BUILD-PLAN, KNOWN-VALUES, UFS, REFERENCE-SOURCES, references |
| `.github/workflows/` | `porting-record.yml` (sheng caller) + adapted `macos.yml` |

## What works today

- **Offline schema/static validation** on Windows: `python scripts/check-skeleton.py` (see below).
- The board resolves with the local `unixnu-format2/UniXNU` tool snapshot through `defconfig`,
  `status --json` and `tree`, provided the base feeds are available (network) or already fetched.
- Reference diffs: `docs/reference/dada-board.toml` (target shape) and
  `soc/dts/sm8735.dtsi.scaffold` (pre-correction SoC tree).

## What does not build yet (top gaps; full table in `docs/GAP-LIST.md`)

1. **UFS component missing** — board selects `ShengUfs` as a placeholder; the luming SM8735 fork
   (`LumingUfs`) and its storage-class/kext-binding archives are not a format-2 component yet.
2. **SM8735 SoC feed unpublished/unvalidated** — the vendored `soc/` scaffold is the local
   `UniXNU-sm8735-common` (migration notes: "not build-tested, not validated by ./unixnu").
3. **Firmware integration incomplete** — `uefi-luming` does not yet embed UniXNU, UniXNUDxe,
   UniXNURamDiskDxe, DarwinBoot + DiskIo/FAT; FD base/size and `Resources/Configs/luming.toml`
   are missing (owned by uefi-builder).
4. **Payload/root inputs missing** — platform seed (`--unique-chip-id`), DBRDISK1 Data seed,
   verified root UUID, trust cache (optional on the no-AMFI route).
5. **AMFI/PMGR/owner-cache path** follows dada's proven restored-AMFI shape (27 prelink roots,
   `early_security_init`, trust-cache pin, copied `build-luming-platform-power.py`/storage builders).
   The no-AMFI entitlement-guard patches are fallback only; UI still needs display/input components.

## Build commands (from a UniXNU checkout; format-2 CLI)

```sh
./unixnu defconfig luming_defconfig -D ../../agents/f2-luming
./unixnu fetch     -D ../../agents/f2-luming
./unixnu status --json -D ../../agents/f2-luming
./unixnu tree      -D ../../agents/f2-luming
./unixnu ipsw info  -D ../../agents/f2-luming
./unixnu ipsw fetch -D ../../agents/f2-luming
./unixnu build kernel  -D ../../agents/f2-luming
./unixnu build package -D ../../agents/f2-luming
./unixnu build firmware -D ../../agents/f2-luming --uefi /path/to/uefi-luming
./unixnu build payload  -D ../../agents/f2-luming --unique-chip-id "$UNIXNU_UNIQUE_CHIP_ID"
./unixnu build userdata -D ../../agents/f2-luming
./unixnu bootimg -D ../../agents/f2-luming --uefi /path/to/uefi-luming --dtb /path/to/firmware.dtb
```

The first three commands work on the local Windows reference tool only after `unixnu fetch` has
the base feeds; the build steps need the official Linux toolchain (dada: `/opt/unixnu-linux`) or a
macOS/Xcode host. Expected output root: `out/luming/ipados-17.7.11-21H461/luming/`.

## Validation (host, no device)

```sh
python agents/f2-luming/scripts/check-skeleton.py
# optional, needs the UniXNU script + git:
python unixnu-format2/UniXNU/scripts/porting-record.py check --device agents/f2-luming
```

Results are recorded in `docs/VALIDATION-HOST.log`.

## CI

`.github/workflows/macos.yml` adapts the official macOS build workflow (checks out UniXNU + this
device repo, installs LLVM/LLD/mtools/dtc, runs defconfig/status, kernel/package/payload/userdata,
uploads redacted text logs only). `.github/workflows/porting-record.yml` runs the official
porting-record check. After publication run:

```sh
gh workflow run macos.yml -f unixnu_repository=UniXNU/UniXNU -f unixnu_ref=main \
  -f device_ref=main -f defconfig=luming_defconfig -f steps="kernel"
```

## Safety

No device operation is part of this repository. All hardware steps are approval-gated, start with
`fastboot boot` only, and follow the official S1-S7 bring-up order
(`docs/FIRST-BUILD-PLAN.md` §4). Nothing here flashes or erases partitions.
