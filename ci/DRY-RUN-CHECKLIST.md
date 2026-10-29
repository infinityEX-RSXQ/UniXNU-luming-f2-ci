# f2-luming format-2 macOS CI — dry-run checklist

Status: **prepared, host-validated, not yet published/run** (route ①: sheng/dada format-2).
A-line prelinked-kernel work is cancelled; this checklist is the entry point for the format-2 CI.

Files:

| File | Purpose |
| --- | --- |
| `.github/workflows/macos.yml` | primary adapted device-repo CI workflow (~24 KiB); dispatchable from the device repository |
| `scripts/ci/f2-luming-ci.sh` | device-side helper: `dry-run`, `preflight`, `pre_build`, `collect` |
| `ci/ci-wiring.ps1` | Windows-side publish/dispatch/wait/download helper (GitHub API; DPAPI token) |
| `ci/f2-luming-macos.yml` | optional core-fork variant (official shape: workflow in a UniXNU core fork); not required |
| `ci/unixnu-macos-reference.yml` | unmodified reference copy of the official format-2 workflow |
| `ci/DRY-RUN-CHECKLIST.md` | this file |

## 0. What the workflow will do (once the repository is published and inputs exist)

```sh
# inside the UniXNU format-2 core checkout
./unixnu defconfig luming_defconfig -D ../device
./unixnu fetch -D ../device
./unixnu status --json -D ../device
./unixnu build kernel -D ../device -j 3 [--kernelcache <file>] [--ipsw <url>]
./unixnu build package -D ../device
./unixnu build firmware -D ../device --uefi ../uefi
./unixnu build payload -D ../device --unique-chip-id $UNIXNU_UNIQUE_CHIP_ID \
  [--trust-cache <file>|--owner-trust-cache <file>] [--data-ramdisk <data.dbr>] [--skip-setup]
./unixnu bootimg -D ../device --uefi ../uefi --fd <SILICIUM_UEFI.fd> --dtb <luming.dtb> \
  -o out/f2-luming/boot/boot.img
```

`build kernel` is where the format-2 pipeline runs the board’s `config_fragments`, `patch_series`,
`archives` (including `build-corecrypto-14.py` / `SoftwareAES`) and `[kernel.prelink]`
(`roots` / `slide` / `early_security_init`); `bootimg` emits Android header v4.

## 1. Current dry-run result (host, 2026-10-29)

`bash scripts/ci/f2-luming-ci.sh dry-run` passes (exit 0) and reports:

**Input blockers (workflow dispatch must supply):**
- firmware step needs a `uefi_repository` checkout (or a prebuilt FD/DTB pair);
- payload step needs `UNIXNU_UNIQUE_CHIP_ID`;
- firmware preflight `scripts/check-luming.py` is missing (gap-list #14).

**Skeleton gaps from `scripts/check-skeleton.py` (248 pass / 7 missing / 2 warn):**
- `scripts/check-luming.py` (format-2 firmware preflight; only the format-1 script in `scripts/reference/` exists);
- external `uefi-luming` checkout / FD base-size verification (owned by uefi-builder; gap-list #7);
- `drivers/LumingUfs` and `drivers/LumingDisplayTouch` are not format-2 components yet (gap-list #2/#4/#5);
- `data.dbr` and `trustcache.bundle` are build-time inputs (never committed; gap-list #8).

**Warnings only (not build-stoppers):**
- FD base/size `0xA7100000/0x300000` unverified for the format-2 path;
- component-series entries are resolver-owned (`component:XnuPrelink/patches/…`).

A **strict preflight** (`bash scripts/ci/f2-luming-ci.sh preflight`) fails with the same blockers by
design. The workflow’s `dry_run=true` / `steps=preflight` dispatch deliberately succeeds and uploads the
checklist so the blocker list is usable immediately.

## 2. Host-side trigger (nothing happens unless you ask)

```powershell
# offline plan only (no GitHub calls that modify anything):
pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -DryRun

# publish the device repo (private by default) and dispatch a dry run:
pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -Prepare -Dispatch -Wait -DryRunWorkflow

# publish + real build once the blockers in §1 are resolved:
pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -Prepare -Dispatch -Wait `
  -Steps "kernel package firmware payload bootimg" `
  -KernelcacheUrl "<masked URL>" -KernelcacheSha256 "<sha256>"
```

GitHub UI equivalent: **Actions → “macOS build (format-2 luming)” → Run workflow**
(`steps=preflight`, `dry_run=true` for the checklist; `dry_run=false` for a build once ready).

## 3. Repository wiring / credentials

- Default device repository: `infinityEX-RSXQ/UniXNU-luming-f2` (private; branch `f2-luming-ci`).
  `ci-wiring.ps1` creates it and uploads the whole `agents/f2-luming` tree, including this workflow,
  to both `main` (required for `workflow_dispatch` to appear) and `f2-luming-ci`.
- The workflow checks out **UniXNU/UniXNU** at the pinned format-2 snapshot
  `33da81310819b86d3ea62cb704f156c56407764a` (override with `unixnu_repository`/`unixnu_ref`), so no
  UniXNU-core fork is required.
- Token: the same DPAPI-protected GitHub token used by the previous kernel-CI runs
  (`agents/ufs-ci/ci_run.ps1`): `%LOCALAPPDATA%\unixnu-luming\github-token.xml` (or `$env:GITHUB_TOKEN`).
  Scopes: `repo` + `workflow`. **The token is never printed.**
- Repository secrets on the device repo:
  - `UNIXNU_UNIQUE_CHIP_ID` — payload platform seed (required for a payload build).
    **Fixed documented value: `addf4030`** = first 8 hex of
    `sha256("f576d0f5")` (full digest `addf4030ba71b85592719d64c2efe6df0026bf67653ce66708eab90b8d875754`). This is a platform seed, not a
    user secret; it is recorded here so runs are reproducible. The workflow only consumes it
    through the repository secret and never prints it.
  - `UNIXNU_IPSW` — optional pinned IPSW URL (alternative to kernelcache inputs);
  - `UNIXNU_DEVICE_TOKEN` — only if the UEFI/device checkouts are private.
- Kernelcache for `ipados-17.7.11-21H461` is delivered as a private-repo release asset:
  tag `kernelcache-ipados-17.7.11-21H461`, asset `kernelcache.macho` (46,415,872 B,
  sha256 `f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7`). The workflow
  downloads it with `${{ github.token }}` when `kernelcache_release_tag` is set (authenticated
  release-asset API; verifies sha256); `kernelcache_url`+sha256 remains the public-URL path.
- Proprietary inputs are dispatch inputs/masked: `kernelcache_url`+sha256, `ipsw_url`, `fd_url`,
  `dtb_url`, `trust_cache_url`, `data_seed_url`; they are downloaded into `$RUNNER_TEMP` and deleted at
  the end. Do not commit Apple-derived files.

## 4. Blockers before a real build can succeed (from docs/GAP-LIST.md)

P0: LumingUfs component (#2), published SM8735 SoC feed (#3), firmware integration in uefi-luming
(#7), payload Data seed / platform seed / root UUID verification (#8), repository published + secrets
(#13), format-2 `scripts/check-luming.py` (#14). The kernel/prelink gate itself is already resolvable
from source for the copied dada shape (27 roots incl AMFI/PMGR, `early_security_init`), but the
resolver has not run against luming yet (gap #15).

## 5. Expected artifacts

Per successful build, `ci-artifacts/` (uploaded as `f2-luming-<board>-<run>-<attempt>`):
- `kernel/kernel.macho` and prelink manifest/log;
- `payload/**` (FAT payload volume, `kernel.macho.adt`, `unixnu.toml`);
- `firmware/SILICIUM_UEFI.fd`, `firmware/luming.dtb`;
- `boot/boot.img` (Android v4);
- `SHA256SUMS` + `build-manifest.json` (run id/attempt/ref/sha, file sizes/sha256);
- build logs. Dry runs instead upload `f2-luming-preflight-<board>-<run>` with `DRY-RUN.md` and
  `preflight.json`.

## 6. Known risks / notes

- Artifacts contain device firmware/kernel images: keep the device repository private (default in
  `ci-wiring.ps1`) or restrict artifact access; the official public repos upload only logs.
- Apple CDN DNS quirks on runners (seen by picasso-yincql): the workflow prefers explicit
  `kernelcache_url`/`ipsw_url` inputs; a curl + DNS-over-HTTPS fallback can be added inside `pre_build`
  if the runner cannot resolve `updates.cdn-apple.com`.
- `unixnu fetch` needs a GitHub token for public sources; the workflow passes `${{ github.token }}`
  (read-only).
- `macos-26`/Xcode 26.6 and Homebrew packages (`llvm lld mtools dtc unifdef`) must be available; the
  workflow records the toolchain and fails early if a tool is missing.
- Format-2 output images are large (kernel+payload+FD+bootimg ≈ 250 MiB); Actions artifact limits apply.
- No device operations: the workflow never flashes or boots a phone.

## 7. Executed result (2026-10-29)

The private repo and CI are live: `infinityEX-RSXQ/UniXNU-luming-f2` (private), workflow
`.github/workflows/macos.yml`. **Run #22 is green** (kernel + prelink):
https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40764094912
artifact `f2-luming-luming-22-1` (id 12850326740), kernel.macho 54,169,600 B sha256
`9958a2550323a6695630d586831818b4359112ac5a7e5d05a94b49e27ae0c8d1`.
`kernelcache_release_tag=kernelcache-ipados-17.7.11-21H461` and
`kernelcache_sha256=f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7` were supplied.
This checklist is satisfied for the kernel gate; firmware/payload/bootimg remain on the Lead's direction.

## 8. Boot image (run #47, 2026-10-29)

**boot.img is green and device-testable.**
- run: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40780288876
- artifact `f2-luming-luming-47-1`, id 12857760540, zip sha256
  `892294f91a2bdd12a362b0e93c327adf2206c5d7c71a227bb95d48b84e3a65dd`
- **boot.img 85,925,888 B (81.95 MiB), sha256
  `7559218f9ea2ac783fae73a5c18fa3a7a5eb591ac0a52f8666e520f73f20ab77`**
- payload.img 80 MiB sha256 `10c46a77…`; prebuilt FD sha256 `a16e12fe…`; DTB sha256 `1c943608…`.
- RAM-only `fastboot boot`; never flash.

## 9. Video-console boot image (run #48, 2026-10-29)

Video-console fix patch applied. **boot.img 85,925,888 B, sha256
`fa94c2764a00b8fb159da72d24a477086b8f324926c4ea66b4f20955fe3e3acd`**, artifact
`f2-luming-luming-48-1` (id 12858664116, zip sha `a331d2c0…`).
Run: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40785641147
RAM-only `fastboot boot`; never flash.

## 10. Diagnostic boot-marks + early-console boot image (run #50, 2026-10-29)

Five colour bands + early vcattach() flush. **boot.img 85,925,888 B, sha256
`3337b65e3daba52398a9bdd603608a69399f1b43910788bffa5957ee88bad49e`**, artifact
`f2-luming-luming-50-1` (id 12860362260, zip sha `b654e380…`).
Run: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40787880736
Previous images preserved: `runs/bootimg-evidence/` (#47 `7559218f…`, #48 `fa94c276…`).

## 11. Start-signals A/B/C boot image (run #51, 2026-10-29)

A red block / B green at FB+2MiB / C PSCI reset after MMU enable. **boot.img 85,925,888 B, sha256
`263e2073955c1698264c9e543c367d5a52ff049ae89a723ee50d53dccd5a75d2`**, artifact
`f2-luming-luming-51-1` (id 12861081811, zip sha `15575428…`).
Run: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40789525996
RAM-only `fastboot boot`; never flash.

## 12. Diagnostic firmware bundle uploaded; Actions billing blocker (run #52)

Diag bundle `uefi-luming-ci-diag.tar.gz` (385,426,068 B, sha
`109777c2e2f20693a06b7e274cde6147eb38113af1f90b3ec3cd39017fa2ebd4`) uploaded as private release
tag `uefi-luming-ci-diag`, asset id 686763008, digest verified.
Run #52 failed before any step: GitHub annotation "The job was not started because recent account
payments have failed or your spending limit needs to be increased." No diag boot.img yet.

## 13. Local diag boot.img (firmware BASE/ADDR/ARGS/ENTRY/SIZE)

CI blocked by GitHub Actions billing (run #52, 0 steps). Locally rebuilt from #51 with diag FD,
verified by exact #51 reproduction: **boot.img 85,925,888 B, sha256
`a2eef01486cdecf4de9885601d8503231dba17b9b40729a9118fa891c8dfc693`**; path
`runs/diag-fw-local/boot-diag.img`; embedded FD `1612900e…` (3,145,728 B). RAM-only `fastboot boot`.

## 14. Root cause: super J2 blob overrides ramdisk payload

Diag firmware big-text on device reported the A-line donor kernel geometry
(`BASE 0xFFFFFFF003DC8000`, `Entry-Base 0x3601488`, `End-Base ≈0x4797000`), not the format-2 kernel
(`BASE 0xFFFFFFF00427C000`, `End-Base 0x4417000`). `super` still holds the A-line J2 payload;
`J2HandoffDxe` publishes it as SFS and DarwinBoot ignores the boot.img ramdisk. All format-2 kernel
patches therefore never ran. Fix: `J2HandoffDxe.c` no-op (return EFI_SUCCESS) forces
`UniXNURamDiskDxe → FAT → ramdisk payload`; new FD rebuilt locally. Format-2 CI images are invalid on
a device with an A-line J2 super unless super is restored/pristine or J2 is disabled.

## 15. Device bring-up status / preconditions (2026-10-29 round 2)

- Format-2 kernel confirmed on device only after flashing a format-2 J2 `super`; DarwinBoot big-text
  must show `BASE 0xFFFFFFF00427C000`. A stale A-line J2 super makes the device boot the old kernel
  and ignore the boot.img ramdisk.
- Kernel reaches `PE_init_iokit`; current blocker is an exception inside it with no video-console
  output. FB `0xFC800000..0xFF300000` is outside the 256 MiB physmap window
  (`0xE387C000..0xF387C000`), and a forced 1 GiB window is above 4 GiB. Proposed DarwinBoot fix:
  diagnostic 512 MiB preferred window at `0xDFE7C000` (end `0xFFE7C000`, below 4 GiB, covers FB);
  see `docs/ALLOCATEWINDOW-PROPOSAL.md`.
- CI GitHub Actions is blocked by account billing/spending limit (run #52, 0 steps). Diagnostic
  firmware bundle is uploaded as private release `uefi-luming-ci-diag` (asset 686763008, sha
  `109777c2…`); after billing is fixed run `steps="kernel payload bootimg"` with that tag/sha,
  kernelcache `f18b4df8…`, reduced payload, CI panic_screen=false.

## 16. Ready-to-run diagnostic-firmware CI command (after billing fix)

`ci/ci-wiring.ps1` now accepts `-UefiArchiveReleaseTag` / `-UefiArchiveSha256`. When GitHub Actions
can start jobs again, the diag-bundle kernel iteration run is:

```powershell
pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -Dispatch -NoWait `
  -Steps 'kernel payload bootimg' `
  -KernelcacheReleaseTag 'kernelcache-ipados-17.7.11-21H461' `
  -KernelcacheSha256 'f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7' `
  -UefiArchiveReleaseTag 'uefi-luming-ci-diag' `
  -UefiArchiveSha256 '109777c2e2f20693a06b7e274cde6147eb38113af1f90b3ec3cd39017fa2ebd4'
```

The workflow still applies the CI-only `[payload].panic_screen=false` override; reduced payload with
no trust cache/Data seed. Latest known blocker: GitHub account billing/spending limit (run #52
annotation); no job starts until it is resolved.

## 17. Window experiment in progress (2026-10-29)

Lead forced DarwinBoot `WindowSize=0x20000000` locally; FD sha `9c351396…`, boot.img sha
`7b5998d2…`, J2 super with `phystokv` boot marks flashed. Awaiting device photo of `ADDR`/`SIZE` +
bands; if >4 GiB run, add the `0xDFE7C000..0xFFE7C000` preferred probe from
`docs/ALLOCATEWINDOW-PROPOSAL.md`. **CI held**; no dispatch until Lead confirms.

## 18. MEMDUMP diagnostic boot.img (2026-10-29)

FD `94499e29…` (3,145,728 B) + `payload-t51.img` → **boot-msgdump.img 85,925,888 B, sha256
`72cc8a2369deedabb35cb1495d9e1aba5da1f9c0e65c67e20dcd514948088c3d`**.
Local: `D:\civitoip20\build\fw-msgdump\boot-msgdump.img`; copy
`runs/msgdump-local/boot-msgdump.img` + `boot.json`. Adds row-8 WIN COVER/NOCOVER and 64 KiB
MEMDUMP at `0xE4000000` (LUMDBG1). RAM-only `fastboot boot`; never flash.
