# Agent instructions — f2-luming

This repository owns the luming board configuration, hardware description, component selection,
firmware/payload policy, partition geometry and build glue for the format-2 route. Shared SM8735
resources belong in the (not yet published) `UniXNU-sm8735-common`; shared tools, profiles and the
component catalog belong to `UniXNU`.

Read before editing:

| Task | Required reading |
| --- | --- |
| Every change | `docs/GAP-LIST.md`, `docs/FIRST-BUILD-PLAN.md`, `docs/KNOWN-VALUES.md`, `docs/A-FIX-CROSSWALK.md` |
| Board/profile | `board.toml` header, `docs/reference/dada-board.toml`, `docs/reference/dada-known-values.md`, `unixnu-format2/UniXNU-sheng/board.toml` |
| Hardware | `dts/luming.dts`, `soc/dts/sm8735.dtsi`, `backup/analysis/device-live/luming-live/*`; the UniXNU device-tree and device-repository docs |
| Storage | `docs/UFS.md`, `docs/reference/dada-ufs.md`, `agents/nativeufs-plan/REPORT-UFS-PLAN.md`, `agents/ufs-ci/REPORT-UFS-CI.md` |
| Firmware | `firmware/README.md` (uefi-builder owns `firmware/`) |
| CI | `.github/workflows/*` (windows-ci owns `.github/` + `scripts/`) |

Rules:

1. **No invented values.** Mark every value `[adapted]`, `[measured]`, `[placeholder]` or
   `[missing]` with a source path; unresolved values stay placeholders and go to `docs/GAP-LIST.md`.
2. **No binary patching.** The format-2 route builds from source; A-line/prelinked binary
   workarounds are documented in `docs/A-FIX-CROSSWALK.md` and must not be reintroduced.
3. **No device operations.** No adb/fastboot/flash/boot in this repository. Hardware steps are
   approval-gated and documented in `docs/FIRST-BUILD-PLAN.md` §4.
4. **No copying from non-format-2 routes.** Route 2 (ios-sweet shim / hackios resident loader) is
   out of scope; see `agents/c-ios16-star/REPORT-C-IOS16-STAR.md` for the record.
5. Keep the official format-2 field shapes (`schema_version = 2`, typed `[adt]` tables, arch:/soc:/
   os:/device: prefixes). Reference copies under `configs/{arch,soc,os}` and `patches/xnu/{arch,os}`
   are not the owners of those files.
6. Run `python scripts/check-skeleton.py` before claiming a change works, and record results in
   `docs/VALIDATION-HOST.log`.
7. Coordination: **uefi-builder** owns `firmware/` and the `uefi-luming` tree; **windows-ci** owns
   `.github/` and `scripts/`; do not overwrite their files without asking the Lead. This workspace
   is written only under `agents/f2-luming/`.
