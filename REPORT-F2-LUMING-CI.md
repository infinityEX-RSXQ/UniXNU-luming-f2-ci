# REPORT-F2-LUMING-CI — macOS CI for the format-2 (sheng/dada, route ①) luming port

Owner: `windows-ci` (task-328). Workspace: `agents/f2-luming/`. **Offline only: no device
operations, no GitHub writes/CI dispatch were performed from this host in this task.** The A-line
prelinked-kernel work is cancelled per Lead (no CLEAN25 package was produced; existing
`agents/ufs-ci/dist/*` packages are untouched).

## 0. Verdict

| Question | Answer |
| --- | --- |
| Adapted workflow written? | **Yes** — primary `.github/workflows/macos.yml` (device repo, self-contained; 22 steps; YAML parses). |
| Device build helper written? | **Yes** — `scripts/ci/f2-luming-ci.sh` (`dry-run` / `preflight` / `pre_build` / `collect`; `bash -n` OK; host dry-run exit 0). |
| CI-side repo wiring prepared? | **Yes** — `ci/ci-wiring.ps1` (PowerShell parser OK) publishes the device tree to a private fork and dispatches; defaults + token source + secrets documented below. |
| Dry-run checklist ready to trigger? | **Yes** — `ci/DRY-RUN-CHECKLIST.md`; `-DryRunWorkflow` dispatch produces a checklist artifact even while the build is blocked. |
| Ready for a real build? | **No** — Skeleton/prebuild gaps remain (P0 list in §5); strict preflight reports 7 blockers by design. Dry-run dispatches are safe and immediate. |
| sheng/dada workflow audit result | Their device repos carry **no macOS build workflow** (only the reusable `porting-record` caller). The official format-2 build workflow lives in the UniXNU **core** repo; luming keeps a self-contained device-repo adaptation (picasso-yincql pattern) so it can be dispatched without a core fork. |

## 1. Reference workflow audit (from `agents/official-crawl/cache/repos/`)

| Reference | Files | Finding |
| --- | --- | --- |
| `UniXNU-sheng` (SM8550, Xiaomi Pad 6S Pro) | `.github/workflows/porting-record.yml` (175 B) | only `uses: UniXNU/UniXNU/.github/workflows/porting-record.yml@main`; **no macOS build workflow in the device repo** |
| `UniXNU-dada` (SM8750, Xiaomi 15) | `.github/workflows/porting-record.yml` (174 B) | same; no macOS build workflow in the device repo |
| `unixnu-format2/UniXNU` (format-2 core snapshot) | `.github/workflows/macos.yml` (13,634 B), `docs.yml`, `terminal.yml`, `porting-record.yml` | **authoritative format-2 macOS pipeline**; dispatched on the core repo with a device-repo input; runs `./unixnu`, optional `pre_build`, builds kernel/package/payload, uploads redacted text logs |
| `guacamole` (legacy A-line) | `.github/workflows/kernel-8796.yml` | A-line pattern: checkout UniXNU pinned + device, `unixnu fetch xnu …`, `build kernel -D .`; no format-2 use |
| `picasso-yincql` (format-2-ish self-contained) | `.github/workflows/build-kernel.yml`, `compose-bootimg.yml` | useful device-repo pattern: local `unixnu --prepare` wrapper over pinned upstream; downloads IPSW with curl (runner DNS issue) and builds kernel+payload; `bootimg --uefi --fd --dtb --ramdisk` |
| `agents/ufs-ci/device-repo/scripts/ci/build-8796-source.py` | macOS Actions script | A-line native-source CI (explicitly **without donor prelink/images**); not used by route ① |

The adapted luming workflow follows the **self-contained device-repo** pattern because the luming
device repo is a standalone skeleton: it checks out `UniXNU/UniXNU` at the pinned format-2 snapshot
`33da81310819b86d3ea62cb704f156c56407764a` as a sibling `unixnu/` checkout and invokes the official
CLI with `-D ../device`. A core-fork variant (`ci/f2-luming-macos.yml`, workflow installed in a
UniXNU core fork and dispatching with `device_repository`) is kept as an optional fallback; it is
not needed for a build.

## 2. Deliverables (exact paths)

| Path | Purpose |
| --- | --- |
| `agents/f2-luming/.github/workflows/macos.yml` | **primary adapted workflow** — name `macOS build (format-2 luming)`; steps: check inputs/mask URLs → host tools/toolchain → device preflight/dry run → defconfig/fetch/status → kernel (`config_fragments` + `patch_series` + `archives` incl. `build-corecrypto-14.py`/`SoftwareAES` + `[kernel.prelink]` roots/slide/early_security_init) → package → firmware (`Mu-Silicium lumingPkg` via `--uefi`) → payload → `bootimg` (Android v4) → collect `SHA256SUMS`/`build-manifest.json` → artifact upload → summary → cleanup |
| `agents/f2-luming/scripts/ci/f2-luming-ci.sh` | device helper: `dry-run` (always exit 0, writes checklist), `preflight` (strict), `pre_build` (stage proprietary inputs + hashes), `collect` (stage/hashes/manifest for `ci-artifacts/`) |
| `agents/f2-luming/ci/ci-wiring.ps1` | Windows-side publish/dispatch/wait/download helper (GitHub API; DPAPI token reused from previous kernel-CI runs; `-DryRun` plan mode; `-Prepare` uploads tree/workflow to default + `f2-luming-ci` branches; `-Dispatch [-DryRunWorkflow] -Wait`) |
| `agents/f2-luming/ci/DRY-RUN-CHECKLIST.md` | operator checklist: exact commands, blockers, secrets, artifacts, risks |
| `agents/f2-luming/ci/f2-luming-macos.yml` | optional core-fork variant (official sheng/dada shape); not required by the primary device-repo workflow |
| `agents/f2-luming/ci/unixnu-macos-reference.yml` | unmodified copy of the official `UniXNU/UniXNU:.github/workflows/macos.yml` |
| `agents/f2-luming/REPORT-F2-LUMING-CI.md` | this report |

Workflow inputs: `unixnu_repository`/`unixnu_ref` (pinned format-2 core), `device_ref`,
`defconfig=luming_defconfig`, `steps` (choice including `preflight`), `dry_run`, `kernelcache_url`+
`kernelcache_sha256`, `ipsw_url`, `uefi_repository`/`uefi_ref`, `fd_url`, `dtb_url`,
`trust_cache_url`/`owner_trust_cache`, `data_seed_url`, `grow_gib`, `skip_setup`, `xcode`,
`artifact_retention_days`. `payload` uses the `UNIXNU_UNIQUE_CHIP_ID` repository secret; optional
`UNIXNU_IPSW` secret supplies the pinned IPSW. Proprietary URLs are masked and removed at the end.

## 3. CI-side repo wiring (prepared, not executed)

- **Token / credentials**: the same DPAPI-protected GitHub token used by the previous kernel-CI runs
  (`agents/ufs-ci/ci_run.ps1`): `%LOCALAPPDATA%\unixnu-luming\github-token.xml`, or `$env:GITHUB_TOKEN`.
  Scopes: `repo` + `workflow`. The token is read silently and never printed by `ci-wiring.ps1`.
  (`ci_run.ps1` also records the earlier account/repos: `infinityEX-RSXQ/UniXNU-luming` and
  `infinityEX-RSXQ/-UniXNU-luming`, branch `task62-ufs-ci`, workflow `darwin22-kernel-ufs-ci.yml`;
  the format-2 wiring reuses the same token/account, not those A-line branches.)
- **Default device repository**: `infinityEX-RSXQ/UniXNU-luming-f2` (private), branch
  `f2-luming-ci`, workflow `macos.yml`. `ci-wiring.ps1 -Prepare` creates it (or forks
  `-UpstreamDeviceRepo`), uploads the whole `agents/f2-luming` tree (excluding build outputs/caches)
  to `f2-luming-ci`, and also puts the workflow + helper on the default branch so
  `workflow_dispatch` is registered.
- **No UniXNU core fork is required**: the workflow checks out `UniXNU/UniXNU` at the pinned
  format-2 commit directly (`unixnu_repository`/`unixnu_ref` inputs).
- **Repository secrets** (set in the device repo): `UNIXNU_UNIQUE_CHIP_ID` (payload platform seed,
  required), optional `UNIXNU_IPSW`, optional `UNIXNU_DEVICE_TOKEN` for private UEFI/device
  checkouts. Proprietary images are never committed.
- Helper: `pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -DryRun` prints the plan and repo state.

## 4. Dry-run status (host validation, 2026-10-29)

`bash scripts/ci/f2-luming-ci.sh dry-run` (exit 0) and `scripts/check-skeleton.py`
(248 pass / 7 missing / 2 warn) produce:

**Workflow-input blockers**
1. firmware step needs a `uefi_repository` checkout (or prebuilt FD/DTB);
2. payload step needs `UNIXNU_UNIQUE_CHIP_ID` secret;
3. `scripts/check-luming.py` (format-2 firmware preflight) is missing.

**Skeleton hard gaps (strict preflight blockers)**
4. external `uefi-luming` checkout / firmware integration (uefi-builder, GAP-LIST #7);
5. component source `drivers/LumingUfs` (not a format-2 component yet, #2);
6. component source `drivers/LumingDisplayTouch` (#4/#5);
7. (same as #3) format-2 `scripts/check-luming.py` (#14).

Warnings only: FD base/size `0xA7100000/0x300000` unverified; `data.dbr`/`trustcache.bundle` are
build-time inputs; two resolver-owned XnuPrelink component series entries. Kernel/prelink itself is
resolvable from the copied dada shape (27 roots incl. AMFI/PMGR, `early_security_init`), but the
resolver has not run against luming (GAP-LIST #15).

A dry-run dispatch (`-DryRunWorkflow`) is safe now: it uploads
`f2-luming-preflight-<board>-<run>` (`DRY-RUN.md`, `preflight.json`) and builds nothing. A real
build will fail fast at strict preflight until the gaps above are closed.

## 5. Ready state / next actions

| Item | State |
| --- | --- |
| workflow + helper + wiring + checklist | **prepared and host-validated** (`bash -n`, PowerShell parser, PyYAML structure, dry-run run) |
| repository published | **no** — `ci-wiring.ps1 -Prepare` ready; requires token approval from the user/Lead |
| CI dispatched | **no** — no GitHub writes from this host in this task |
| real build | **blocked** by the P0 gaps above (LumingUfs, SM8735 SoC feed publish, uefi-luming firmware integration, payload/Data inputs, repo publish+secrets, format-2 check-luming.py) |
| A-line | **cancelled** per Lead; no more prelinked-kernel builds, existing `agents/ufs-ci/dist/*` untouched |

Once the P0 gaps are closed:
`pwsh -File agents/f2-luming/ci/ci-wiring.ps1 -Prepare -Dispatch -Wait -Steps "kernel package firmware payload bootimg" -KernelcacheUrl <masked> -KernelcacheSha256 <sha256>`.
The first useful evidence is the `kernel`-only job (`-Steps kernel`) with a supplied kernelcache;
firmware/bootimg can follow once `uefi-luming` is published or FD/DTB artifacts are provided.

## 6. Risks / notes

- **Proprietary images**: workflow uploads kernel/payload/FD/bootimg; keep the device repo private
  (default) or restrict artifact access. The official public repos upload only redacted logs.
- **Apple CDN DNS** (seen in picasso-yincql): prefer explicit `kernelcache_url`/`ipsw_url`; a
  curl + DNS-over-HTTPS fallback can be added in `pre_build` if the runner cannot resolve
  `updates.cdn-apple.com`.
- **Upstream drift**: `unixnu_ref` is pinned to the format-2 snapshot; update intentionally.
- **Toolchain**: `macos-26` + Xcode 26.6 and Homebrew `llvm lld mtools dtc unifdef`; the workflow
  reports the toolchain and fails early if a tool is missing.
- **Artifact size**: ~250 MiB of images, within Actions artifact limits but keep retention modest.
- **No device operations** in this repository/workflow.

## 7. Deliverable hashes (2026-10-29, host files)

| file | bytes | sha256 |
| --- | --- | --- |
| `.github/workflows/macos.yml` | 23969 | `e44c33097dc743e9f7e4662adc936c5a36f1b848d33983f5c60c038e1d03fa60` |
| `scripts/ci/f2-luming-ci.sh` | 14141 | `272cf706b94df03ef70f54ecfd3adf09d7bccaf76bea52321bd89c7340c6098e` |
| `ci/ci-wiring.ps1` | 16752 | `f8d29a048301d85872eaceb248db739335f07c7fad9e47812db394c6b178ab9e` |
| `ci/DRY-RUN-CHECKLIST.md` | 7274 | `efef402c903c551a783d609a51a2d41917a243e229c6de3978afed17bcae6781` |
| `ci/f2-luming-macos.yml` | 27047 | `b0d16f43d3803baee7dc48ee52086e4595121b4a1ba645794db3f205733da782` |
| `ci/unixnu-macos-reference.yml` | 13634 | `8979454f0418abdf7c3aebb53f2372d4d4c02f5ef5b5416291cb85cc997d1879` |
## 8. Live CI execution (2026-10-29, route ①)

### Repo / credentials / runner

- Private repo created via API: **https://github.com/infinityEX-RSXQ/UniXNU-luming-f2** (default branch
  `main`, CI branch `f2-luming-ci`); ~161 skeleton files uploaded (firmware/build-tree+uefi ~1.1 GiB and
  `.check` scratch excluded).
- Secret `UNIXNU_UNIQUE_CHIP_ID` set and verified on the repo: **`addf4030`**
  (first 8 hex of `sha256("f576d0f5")` = `addf4030ba71b85592719d64c2efe6df0026bf67653ce66708eab90b8d875754`;
  platform seed, not a user secret; value not printed by scripts).
- Runner: `macos-26` (official label) stayed queued >10 min on this plan; workflow switched to
  **`macos-15` + Xcode 16.4**. `porting-record.yml` changed to `on: workflow_dispatch` after the
  contents-API upload produced 279 push-triggered ubuntu runs; stale queued macOS-26 runs cancelled.

### Run history / fixes (all on `f2-luming-ci`)

| Run | URL | Result | Root cause / fix |
| --- | --- | --- | --- |
| #1 40750250168 | actions/runs/40750250168 | cancelled | queued on `macos-26`; label unavailable/slow |
| #2 40751849055 | actions/runs/40751849055 | cancelled | same; cancelled before fallback |
| #3 40752116443 | actions/runs/40752116443 | failure step 6 | `git -C unixnu apply device/patches/...` resolves patch relative to `unixnu/`; fixed with absolute `$GITHUB_WORKSPACE/device/...` |
| #4 40752276893 | actions/runs/40752276893 | failure step 6 | patch context mismatch on pinned catalog (`components.toml:510`); replaced with context-free `scripts/ci/add-lumingufs-component.py` appender |
| #5 40752894631 | actions/runs/40752894631 | failure step 11 | uploaded helper had CRLF (`set -euo pipefail\r` invalid on macOS bash 3.2); normalized to LF |
| #6 40753160433 | actions/runs/40753160433 | failure step 11 | dispatched before LF upload landed; same CRLF failure |
| #7 40753222623 | actions/runs/40753222623 | see below | kernel-only, LF helper, catalog appender; should pass preflight and reach the native kernel build |

Runs #3-#6 are logged under `agents/f2-luming/runs/f2-<run-id>/` (logs.zip + extracted logs +
run.json). Run #5 preflight reached `BOARD: luming`, appender exit 0, Xcode/toolchain OK; its only
failure was the CRLF helper.

### Local preflight state before run #7

`bash scripts/ci/f2-luming-ci.sh dry-run` (steps=kernel): **0 blockers, 7 warnings**; `check-skeleton.py`
and `check-luming.py` both exit 0; catalog appender idempotent. The remaining warnings are non-kernel
inputs (firmware/uefi/payload seeds, FD geometry, resolver-owned XnuPrelink series entries).

### Next

Run #7 is the first candidate to reach `./unixnu` defconfig/fetch/status and the native XNU +
prelink build. If it fails there, the first failing step/log line will be captured and reported; if
it succeeds, the kernel artifact name, bytes and sha256 will be appended here and messaged to the Lead.
## 9. Run #8-#13: kernelcache delivery and source-patch bring-up (2026-10-29)

| Run | URL | Result | Fix applied after |
| --- | --- | --- | --- |
| #8 40753514410 | actions/runs/40753514410 | failure | preflight/core-path fix not yet in the workflow |
| #9 40753597459 | actions/runs/40753597459 | failure step 13 | GBK/CRLF `configs/luming_defconfig` in repo; latest UTF-8 tree re-synced |
| #10 40755467088 | actions/runs/40755467088 | failure step 13 | defconfig had `[archives]` + inline comments; parser-safe defconfig uploaded (validated with pinned `parse_config`) |
| #11 40755918077 | actions/runs/40755918077 | failure step 15 | kernelcache release asset verified (`f18b4df8…`, 46,415,872 B); `native-smp-secondary.patch` had CRLF; LF-normalized + verified `git apply` against pinned xnu-10063 source |
| #12 40756442929 | actions/runs/40756442929 | failure step 15 | all patches reached; core `patches/xnu/zzz-boot-progress.patch` has a bsd_init.c hunk that does not match xnu-10063; CI now disables only that core patch (device `zzz-boot-progress-min.patch` remains active) |
| #13 40756868265 | actions/runs/40756868265 | kernel build running | see below |

Kernelcache delivery (private repo release):
- tag `kernelcache-ipados-17.7.11-21H461`, release id 427105150, asset id 686109901,
  `https://api.github.com/repos/infinityEX-RSXQ/UniXNU-luming-f2/releases/assets/686109901`,
  size 46,415,872 B, sha256 `f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7`
  (remote digest verified by the GitHub API).
- workflow input `kernelcache_release_tag` (or `kernelcache_url`+sha256 for a public URL); token never
  printed; asset downloaded via the release-assets API with the Actions `github.token`.

Additional CI-only workarounds made explicit (not silent):
1. `zzz-boot-progress.patch` disabled in the CI checkout's core OS series because its bsd_init hunk
   context does not match xnu-10063.141.1 (device minimal boot-progress patch stays active).
2. CRLF device patch files normalized to LF (native SMP, UFS log, PMGR call, catalog patch).
3. Defconfig's stale `[archives]` header + inline comments removed so the pinned parser accepts it.
These are in `REPORT-F2-LUMING-CI.md` and should be reverted/upstreamed once the core/device patches
are regenerated against the pinned xnu-10063 source.

### Next

Run #13 is the first run whose `Build the native XNU kernel and prelink` step is executing to
completion; artifact name/hashes will be appended when it finishes.
## 10. First green kernel artifact (run #22, 2026-10-29)

Run #22: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40764094912 — **success**.

| item | value |
| --- | --- |
| workflow | `.github/workflows/macos.yml` (device repo, macos-15 + Xcode 16.4 fallback) |
| inputs | `steps=kernel`, `kernelcache_release_tag=kernelcache-ipados-17.7.11-21H461`, `kernelcache_sha256=f18b4df865405f2a287b84977d7aca745e056d656d9fc9df1662970ce2969de7` |
| artifact | `f2-luming-luming-22-1`, id `12850326740`, 11,932,672 B zip |
| artifact sha256 | `8e355e8efc7e6ab6856cfcc5ac5b24f2f3652da9b7c7391135b665b2939cc786` |
| prelinked kernel | `out/luming/ipados-17.7.11-21H461/luming/kernel/kernel.macho` |
| kernel bytes / sha256 | 54,169,600 B / `9958a2550323a6695630d586831818b4359112ac5a7e5d05a94b49e27ae0c8d1` |
| kernel header | arm64 Mach-O (`cffaedfe`), executable bytes unchanged |
| prelink log | `Experimental candidate: 54169600 bytes; executable bytes unchanged; runtime unqualified` |
| local copy | `agents/f2-luming/runs/f2-40764094912/artifact-12850326740.zip` (extracted) |

Working CI overrides/config now needed (all committed/uploaded to the private device repo and documented above):
1. catalog appender (`scripts/ci/add-lumingufs-component.py`) instead of the context-drifted patch;
2. LF-normalized patch files; parser-safe UTF-8 defconfig (removed `[archives]` header/inline comments);
3. owner-cache/Data/SystemOS switches disabled for the bootstrap kernel (temporary; re-enable with the
   owner-root trust chain later);
4. core `zzz-boot-progress.patch` disabled in CI; device minimal patch active;
5. Xcode-16.4 flag strip (workflow rewrites Xcode-26-only flags in `unixnu/scripts/**` + `device/scripts/**`);
6. `-I{tree}/build/storage-abi/include` in `CONFIG_XNU_EXTRA_CFLAGS`;
7. BootLog builder fallback to `$UNIXNU_DEVICE/kits/luming`;
8. legacy `build/sheng-ufs/libShengUfs.a` symlink to `build/luming-ufs/libLumingUfs.a`;
9. `CONFIG_XNU_EXTRA_LD_ARCHIVES` force-loads only `build/luming-boot-log/libLumingBootLog.a`.

Next pipeline steps not yet green: firmware (needs uefi-luming checkout / FD), payload (needs data seed +
trust cache; fixed chip seed `addf4030` already in repo secret), bootimg (needs FD + DTB or a firmware
build). The kernel gate is met; dispatch those on the Lead's direction.
## 11. Device-testable boot.img (run #47, 2026-10-29) — SUCCESS

Run #47: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40780288876 — **success**.

| item | value |
| --- | --- |
| steps | `kernel payload bootimg` (reduced payload; no Data/root, no trust cache, panic_screen off) |
| artifact | `f2-luming-luming-47-1`, id 12857760540, 33,693,149 B zip |
| artifact sha256 | `892294f91a2bdd12a362b0e93c327adf2206c5d7c71a227bb95d48b84e3a65dd` |
| **boot.img** | **85,925,888 B (81.95 MiB)** |
| **boot.img sha256** | **`7559218f9ea2ac783fae73a5c18fa3a7a5eb591ac0a52f8666e520f73f20ab77`** |
| header | Android boot header **v4**, ramdisk-backed |
| payload.img | 83,886,080 B (80 MiB), sha256 `10c46a778e1f835c563bd6a5da17ecd4ac4024966f98b25e73fff531361d3c16` |
| ADT | sha256 `3349c0ca46bf1793980a67769b5eda42b65c417ad3b754eaec13f88b848695ce` |
| kernel (same run) | 54,169,600 B sha256 `ef79acfffd7532de421ad3290ea501dc53d5000c3f5b468b871782e0f9a95625` |
| FD (prebuilt, from UEFI bundle) | 3,145,728 B sha256 `a16e12fe93a707a836c43958d6a9b0a67c10593a801a4e8ca820367b1296466a` |
| DTB (prebuilt, from UEFI bundle) | sha256 `1c94360890050ca6e6933b9861789af28269140c16aa7384192123bd44b9bcec` |
| local copy | `agents/f2-luming/runs/f2-40780288876/artifact/files/out/f2-luming/boot/boot.img` |

**RAM-only `fastboot boot` image — never flash.** Total 85.9 MB, far below the 768 MiB cap.

Final CI workarounds that made this possible (all committed/pushed to the private device repo and/or
documented above): catalog appender; LF patches; parser-safe UTF-8 defconfig; owner/bootstrap config;
core boot-progress patch disabled in CI; Xcode-16.4 warning-flag strip; storage ABI include; BootLog
device-path fallback; legacy UFS archive symlink; single BootLog force-load; storage bindings/patches
tolerance; authenticated kernelcache + UEFI bundle release assets; prebuilt FD/DTB use; EDK2 deps +
GitPython/PATH + bash-3.2 wrapper fixes; fdtput removal of the bundle's duplicate splash node before
the board `[[bootimg.dtb_node]]` is applied.

Packaging (`./unixnu build package`) is the only remaining CI gap: the combined package run failed in
the EDK2 VfrCompile host tool (`make: *** [VfrCompile] Error 2`) under the macos-15/Xcode-16.4
fallback. The boot.img path above does not require package, so it was deliberately skipped.
## 12. Video-console fix boot.img (run #48, 2026-10-29) — SUCCESS

Device #47 boot reached firmware + DarwinBoot handoff but XNU died silently: `initialize_screen()`
treated DarwinBoot's even physical framebuffer address `0xFC800000` as a virtual address and wrote to
an unmapped VA before first console output. device-builder added
`patches/xnu/device/zzzzz-fix-darwinboot-physical-framebuffer.patch` (first in the device series):
`makeMapping` now also becomes true for any non-kernel-VA video base, so the framebuffer is
`ml_io_map_unmappable`-mapped instead of used as a VA.

Run #48: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40785641147 — **success**.

| item | value |
| --- | --- |
| steps | `kernel payload bootimg`; new framebuffer patch applied; CI reduced payload (panic_screen=false), no trust/data |
| artifact | `f2-luming-luming-48-1`, id 12858664116, 32,907,181 B zip |
| artifact sha256 | `a331d2c0980b6145acc76a5a2c40e31bf42eb77ec1b5cb4942d4bb82973e8d1a` |
| **boot.img** | **85,925,888 B (81.95 MiB)**, Android v4 |
| **boot.img sha256** | **`fa94c2764a00b8fb159da72d24a477086b8f324926c4ea66b4f20955fe3e3acd`** |
| kernel (with video patch) | 54,169,600 B, sha256 `73a4ad9715f2e55b0d729101b9ca94a2ab23d8c681d5a3f5c9180d428226f6f8` |
| payload.img | 83,886,080 B, sha256 `12e774a243025c82c625cf516ea3976f8fb055163a3f9f83203c97fdb42e8800` |
| ADT | sha256 `fb60839f8513c1f5eef01410852704511e197c20bfd0ed1403325919737c9c32` |
| FD / DTB | `a16e12fe…` / `1c943608…` (prebuilt from authenticated UEFI bundle) |
| local image | `agents/f2-luming/runs/f2-40785641147/artifact/files/out/f2-luming/boot/boot.img` |

CI-only pre-emptive override: the workflow rewrites `[payload].panic_screen` to false in the CI
checkout (device tree remains true), avoiding the known panic-screen cave collision while the
video-console fix is validated on hardware. RAM-only `fastboot boot` — never flash.
## 13. Diagnostic boot-marks + early-console boot.img (run #50, 2026-10-29) — SUCCESS

Device test #48 still stopped at DarwinBoot STAGE3/logo with no XNU text; the framebuffer fix was in
the kernel but early kprintf is buffered until vcattach(), so the screen could not localise the
death. Two bring-up-only diagnostic patches were added by device-builder:

- `patches/xnu/device/zzzzz-luming-boot-marks.patch` + `kits/luming/BootMarks.c` — paints five
  full-width colour bands (red/green/blue/yellow/magenta) at arm_vm_init, kprintf-init,
  PE_create_console, PE_init_platform(TRUE), before PE_init_iokit.
- `patches/xnu/device/zzzzz-luming-early-console-flush.patch` — `PE_init_printf(TRUE)` immediately
  after `PE_create_console()` (after the boot-marks stage-3 paint), flushing the buffered boot log to
  the video console before IOKit.

`BootMarks.c` initially failed in CI with `fatal error: 'vm/vm_types.h' file not found` because the
BootLog TU compile include set does not expose osfmk/vm private headers. Fixed by making the
diagnostic TU self-contained (`typedef unsigned long vm_offset_t/vm_size_t`, direct `ml_io_map`
declaration); it then compiled into `libLumingBootLog.a`.

Run #50: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40787880736 — **success**.

| item | value |
| --- | --- |
| steps | `kernel payload bootimg`; framebuffer fix + boot-marks + early-console-flush + existing device series |
| artifact | `f2-luming-luming-50-1`, id 12860362260, 33,595,559 B zip |
| artifact sha256 | `b654e38063bba218f4dd9a1c3a5895e41fe986356a3b9b46562e980bee21fcca` |
| **boot.img** | **85,925,888 B (81.95 MiB)**, Android v4 |
| **boot.img sha256** | **`3337b65e3daba52398a9bdd603608a69399f1b43910788bffa5957ee88bad49e`** |
| diagnostic kernel | 54,169,600 B sha256 `6ef95304a3c82004a647c56c458906176e137261a972a3c260f84d8e070a7702` |
| payload.img | 83,886,080 B sha256 `b79265387896c4c9df9c28608a398a348ca74d03611d68f067ce638fb2b09b7f` |
| ADT | sha256 `66d76c28b0b57e6f777ddb4058788cf771c6f9711c45f92651657f6dd5193169` |
| FD / DTB | `a16e12fe…` / `1c943608…` |
| local image | `agents/f2-luming/runs/f2-40787880736/artifact/files/out/f2-luming/boot/boot.img` |
| preserved comparison copies | `runs/bootimg-evidence/` (#47 `7559218f…`, #48 `fa94c276…`, #50 `3337b65e…`) |

Both diagnostic patches are bring-up-only and must be removed for production. RAM-only
`fastboot boot` — never flash.
## 14. Start-signals A/B/C boot.img (run #51, 2026-10-29) — SUCCESS

Third localization diagnostic: `patches/xnu/device/zzzzz-luming-start-signals.patch` instruments
`osfmk/arm64/start.s`:
- **A**: RED block at FB PA 0xFC800000 while the MMU is still off (right after `start_first_cpu`'s
  `mov x20,x0 / mov x21,#0`).
- **B**: GREEN block at FB+2 MiB immediately before `MOV64 x0,SCTLR_EL1_DEFAULT`.
- **C**: PSCI SYSTEM_RESET (`movz w0,#0x8400,lsl#16; movk w0,#9; smc #0; hvc #0; b .`) immediately
  after MMU enable.

Series order: fb fix → start signals → boot marks → early console flush → boot-progress → owner-cache
/union → pmgr/ufs-log. Runs with BootMarks/early-flush archives unchanged; diagnostic-only.

Run #51: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40789525996 — **success**.

| item | value |
| --- | --- |
| steps | `kernel payload bootimg`; reduced payload; CI panic_screen=false; no trust/data |
| artifact | `f2-luming-luming-51-1`, id 12861081811, 32,946,642 B zip |
| artifact sha256 | `15575428bee6bffa3a957f079802317126941e8a5877e38a0018b0fc4296f5e5` |
| **boot.img** | **85,925,888 B (81.95 MiB)**, Android v4 |
| **boot.img sha256** | **`263e2073955c1698264c9e543c367d5a52ff049ae89a723ee50d53dccd5a75d2`** |
| kernel (A/B/C) | 54,169,600 B sha256 `d63781f54c1f542a1177de1b1aaa2178bef487a81e78480b533a0f62d2d8e5b1` |
| payload.img | 83,886,080 B sha256 `14175f7587fe6082e63794ce3f1ae16a1f49b8f96eede52cd368b1b991f1e62e` |
| ADT | sha256 `f19b824a99f55d49228eebbdc10da98c02e22dd06c9537e7e4fd27272c893d34` |
| FD / DTB | `a16e12fe…` / `1c943608…` |
| local image | `agents/f2-luming/runs/f2-40789525996/artifact/files/out/f2-luming/boot/boot.img` |
| preserved copies | `runs/bootimg-evidence/` (#47 7559218f…, #48 fa94c276…, #50 3337b65e…, #51 263e2073…) |

Device-expected: A red (entry), B green at +2 MiB (bootstrap mapping), C PSCI auto-reboot (MMU
enabled). All diagnostic patches are bring-up-only. RAM-only `fastboot boot` — never flash.
## 15. Diagnostic firmware bundle (DarwinBoot BASE/ADDR/ARGS/ENTRY/SIZE) — upload done, build blocked

uefi-builder produced a patched DarwinBoot firmware bundle that draws BASE/ADDR/ARGS/ENTRY/SIZE as
big unambiguous text on screen (rows 2-7 after STAGE 3), resolving the entry-PA question from run #51
(red start-signal never appeared, so kernel entry likely never executed).

Bundle: `firmware/ci-bundle/uefi-luming-ci-diag.tar.gz`, **385,426,068 B**,
sha256 **`109777c2e2f20693a06b7e274cde6147eb38113af1f90b3ec3cd39017fa2ebd4`**; patched FD inside
is `1612900e…`; preflight 84/84; archive root `build-tree/` with vendor `Binaries/luming`.

Uploaded as a new **private** release:
- tag `uefi-luming-ci-diag`, release id **427320088**
- asset id **686763008**, size **385,426,068 B**, digest
  `sha256:109777c2e2f20693a06b7e274cde6147eb38113af1f90b3ec3cd39017fa2ebd4`
- URL: https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/releases/download/uefi-luming-ci-diag/uefi-luming-ci-diag.tar.gz

Attempted diag boot.img run #52 (https://github.com/infinityEX-RSXQ/UniXNU-luming-f2/actions/runs/40791493455):
GitHub refused to start the job (0 steps, runner_id 0). Check-run annotation:
`The job was not started because recent account payments have failed or your spending limit needs to be increased. Please check the 'Billing & plans' section in your settings`
(plus a macOS arm64 capacity/queue notice). No diag boot.img was produced. The workflow has no
artifact-reuse input, so after the billing block is cleared the diag build will use
`steps="kernel payload bootimg"` with `uefi_archive_release_tag=uefi-luming-ci-diag`,
`uefi_archive_sha256=109777c2…`, same kernelcache/f18b4df8, reduced payload, CI panic_screen=false.
Last green device image remains #51 (`263e2073…`).
## 16. Local diag boot.img rebuild (firmware BASE/ADDR/ARGS/ENTRY/SIZE) — device-ready

GitHub Actions refused to start the diag build due to account billing (run #52, 0 steps):
`The job was not started because recent account payments have failed or your spending limit needs to be increased.`

To keep the device test moving, the diag boot image was rebuilt deterministically on this host from
the green #51 boot.img:
1. Parse #51 Android v4 header; extract kernel bytes (`2,027,643 B`), ramdisk (`payload.img`,
   byte-identical to #51 `14175f75…`), and the final appended DTB tree (`7e52e77f…`).
2. Decompress the kernel gzip segment: it is `BootShim` (112 B) + old FD (`a16e12fe…`), with the
   final DTB appended after the gzip stream.
3. Rebuild with the **old** FD and the bundle's own `Resources/Scripts/mkbootimg.py`; this reproduced
   #51's exact image sha256 `263e2073…` and 85,925,888-byte size (byte-for-byte proof; the only
   platform quirk was gzip header OS byte 0xff, forced explicitly).
4. Repeat with the diagnostic FD (`1612900e…`) and identical shim/DTB/ramdisk.

Result:
- **`runs/diag-fw-local/boot-diag.img`**, **85,925,888 B**, sha256
  **`a2eef01486cdecf4de9885601d8503231dba17b9b40729a9118fa891c8dfc693`**
- embedded FD: sha256 `1612900e16fffe0814b2eb1088db6909d167b786fb6898cd65bb26e724a22f72`
- kernel segment sha256 `d23c2d61b34f93fbe80712fd2a28b3b4c35ea0b48180863dd5eedd4af16e4997`
- payload sha256 `14175f7587fe6082e63794ce3f1ae16a1f49b8f96eede52cd368b1b991f1e62e`
- DTB sha256 `7e52e77fca264cc6f2b8f1f5d59d56058d9acbcce7ece86d7135b92715305d96`
- `boot.json` provenance alongside; copy preserved at `runs/bootimg-evidence/bootimg-diag-a2eef014.img`.

This local image is **not CI-provenance**; the CI run remains blocked by billing. The diag bundle is
uploaded and ready for a CI rerun (`steps="kernel payload bootimg"`, tag `uefi-luming-ci-diag`,
sha `109777c2…`) once GitHub Actions can start. RAM-only `fastboot boot`; never flash.
## 17. Root cause of the "kernel never starts" device symptom: super J2 blob wins over ramdisk

The diag firmware’s big-text output on the real phone clarified the whole bring-up loop:

- Reported: `BASE 0xFFFFFFF003DC8000`, `Entry-Base 0x3601488`, `End-Base ≈ 0x4797000`.
- That is an exact match for the **A-line donor kernel** `build/kernel-prelinked-darwin22-ufs-final.macho`
  (BASE 0xFFFFFFF003DC8000, End-Base 0x4797000) — **not** the format-2 kernel
  (BASE 0xFFFFFFF00427C000, End-Base 0x4417000).

Cause: the phone’s `super` partition still holds the A-line J2 payload. Firmware’s `J2HandoffDxe`
reads the super J2 blob and publishes it as SFS; DarwinBoot then boots that old kernel and ignores the
boot.img ramdisk payload. Therefore none of the format-2 kernel patches (framebuffer fix, boot marks,
early console, start signals) ever executed — every previous device image was booting the A-line
donor kernel.

Fix in progress (uefi-builder): `J2HandoffDxe.c` patched to return `EFI_SUCCESS` immediately
(diagnostic no-op), forcing the format-2 path
`UniXNURamDiskDxe → DiskIo/Partition/FAT → ramdisk payload`. New FD is being rebuilt locally (no CI
needed); boot.img will be rebuilt locally with the new FD plus the #51 payload/kernel.

**CI/device bring-up consequence:** format-2 CI boot images are invalid on a device whose `super`
still contains the A-line J2 blob. They become valid only if `super` is pristine/restored or
`J2HandoffDxe` is disabled/patched as above. This is a device-state prerequisite, not a CI build bug;
record it in every future device test checklist.

### 17.1 Static FDF/DSC verification (device-builder, 2026-10-29)

`agents/f2-luming/firmware/uefi/Platforms/Xiaomi/lumingPkg`:
- `luming.fdf` includes `Include/APRIORI.inc`; the APRIORI list contains the format-2 payload path in
  order: `UniXNURamDiskDxe` (line 23, DEPEX `TRUE`) → `DiskIoDxe` (69) → `PartitionDxe` (70) →
  `UFSDxe` (74) → `Fat.inf` (76). `luming.dsc` also lists DiskIo/Partition/EnglishDxe/Fat in
  `[Components]`, so the modules are built and placed in the FV via the include.
- `UniXNURamDiskDxe` publishes the boot-image initrd as read-only BlockIo using `/chosen`
  `linux,initrd-start`/`linux,initrd-end` (DTB passed in the Mu-Silicium SEC entry-argument HOB);
  DiskIo/Partition/Fat expose the FAT volume to DarwinBoot. **The format-2 ramdisk payload path is
  present, ordered and does not need a module-order change.**
- `J2HandoffDxe` is listed after the APRIORI block and before DarwinBoot (DEPEX
  `GOP AND BlockIo`); it reads the `super` J2 header/member and publishes a direct SFS, then
  DarwinBoot (consumes SFS+BlockIo) can boot that stale volume. With a J2 no-op/absent FD the only
  SFS is the ramdisk FAT volume.
- Runtime device-state check (approval-gated; not executed by CI/build):
  `dd if=/dev/block/by-name/super bs=4096 count=1 | strings | grep LUMING-J2-BLOB`.
  Present ⇒ stale A-line J2 blob still on the phone; restore pristine/format-2 `super` or use the
  J2 no-op FD before any format-2 kernel boot test.
- Diagnostic expectation after the J2 fix: firmware big text should report the format-2 kernel
  (`BASE 0xFFFFFFF00427C000`, `End-Base 0x4417000`), not the A-line donor
  (`BASE 0xFFFFFFF003DC8000`). Only then do the start-signals A/B/C and boot-marks bands report on
  our kernel.

### 17.2 Preflight and runbook

- **Static preflight (implemented):** `scripts/check-luming.py` now has
  `check_luming_payload_path()` — it reads the lumingPkg FDF/DSC/APRIORI and:
  - PASSes when `UniXNURamDiskDxe` precedes DiskIo/Partition/Fat in APRIORI and FDF/DSC contain the
    ramdisk + DarwinBoot modules;
  - WARNs when `J2HandoffDxe` is still in the FD ("format-1 super-blob fallback"), because a device
    with a stale `super` will boot the old kernel — the warning text includes the runtime super check;
  - WARNs if the J2 source has no no-op marker.
- **Runtime checklist (approval-gated device ops; not performed in this repository):**
  1. `dd ... | grep LUMING-J2-BLOB` on `super`; record present/absent with the boot evidence.
  2. Confirm the diag big text reports the format-2 kernel base/entry, not the A-line donor.
  3. Only then interpret start-signals/boot-marks/console results.
- **CI implication:** a green CI build cannot prove the device `super` state. Every published
  format-2 `boot.img` must state the prerequisite "pristine/format-2 super or J2-no-op FD" until the
  J2 fallback is permanently removed from format-2 builds.
## 18. Device bring-up status after root-cause fix (2026-10-29 round 2)

Source: `docs/BOOT-DEBUG-2026-10-29.md`.

1. **Root cause #1 fixed on the device.** The stale A-line J2 payload in `super` was replaced by a
   J2 super built from our format-2 payload (`build/super-format2*.img`, flashed via
   `fastboot flash super`). DarwinBoot now reports `BASE 0xFFFFFFF00427C000`, i.e. the **format-2
   prelinked kernel**, not the old A-line donor (`0xFFFFFFF003DC8000`).
2. **Kernel reaches `PE_init_iokit`.** PSCI-reset markers at function entries proved the chain
   `arm_init → arm_vm_init → … → machine_startup → kernel_bootstrap_thread → kernel_bootstrap →
   vm_mem_bootstrap → vm_map_init → kmem_init → vm_fault_init → kernel_memory_populate →
   console_init → PE_init_iokit`. The kernel is alive through the end of `kernel_bootstrap`.
3. **Remaining blocker:** a fault occurs **inside `PE_init_iokit`** and the framebuffer console never
   prints. T37 (T27 + exception vectors → PSCI) reboots, proving the freeze is an exception, not a
   panic; T46 proves the `PE_init_printf`/console flush itself is not the fault.
4. **Framebuffer is outside the kernel physmap window in both tested configurations.** 256 MiB
   window at `0xE387C000` ends `0xF387C000`; forced 1 GiB window lands at `0x8C007C000` (above 4 GiB).
   The GOP FB is `0xFC800000..0xFF300000`. Next step is a DarwinBoot `AllocateWindow` change to place
   a window below 4 GiB that covers the FB, then re-run boot-mark bands and bisect `PE_init_iokit`.

Proposal for uefi-builder/device-builder: `docs/ALLOCATEWINDOW-PROPOSAL.md` — diagnostic 512 MiB
window at `0xDFE7C000` (end `0xFFE7C000`, below 4 GiB, covers `0xFC800000..0xFF300000`), with a
preferred-range attempt before the existing first-fit allocator and a memory-map caveat if the FB is
not `EfiConventionalMemory`.

### Device-state prerequisites (record on every boot test)

- `super` must contain the **format-2** J2 payload, not the old A-line `LUMING-J2-BLOB`, or firmware
  `J2HandoffDxe` must be a no-op/absent (`J2HANDOFF: DISABLED`). Otherwise DarwinBoot boots the stale
  super kernel and ignores the `boot.img` ramdisk — format-2 CI images are invalid in that state.
- CI GitHub Actions is currently blocked by account billing/spending limit (run #52 annotation); the
  diagnostic firmware bundle is uploaded as private release `uefi-luming-ci-diag` (asset id
  686763008, sha256 `109777c2…`) and is ready for `kernel payload bootimg` runs once Actions can
  start. All recent kernel/firmware iteration was done by local host builds (documented in
  `docs/BOOT-DEBUG-2026-10-29.md`).
- Frame-buffer/physmap: until the window experiment succeeds, do not read "no on-screen text" as
  "kernel not running"; use the PSCI/boot-mark/UFS-log markers.
## 19. Current window experiment (2026-10-29, post-proposal) — awaiting device photo

Lead implemented the 512 MiB forced-window diagnostic locally and flashed it:

- DarwinBoot: `WindowSize = 0x20000000ULL` after the ADT read (diagnostic, forced).
- FD sha256 **`9c351396…`**; boot.img sha256 **`7b5998d2…`**.
- J2 `super` rebuilt/flashed with boot marks that use `phystokv()` (format-2 J2 payload / marksva
  variant).

Pending: device photo/Marker read of DarwinBoot `ADDR`/`SIZE` plus the boot-mark bands, to confirm
the allocator actually placed the window below 4 GiB and covering FB `0xFC800000..0xFF300000`.
If it still picks a >4 GiB run, add the preferred-range probe exactly as in
`docs/ALLOCATEWINDOW-PROPOSAL.md` (candidate `0xDFE7C000`, end `0xFFE7C000`, below 4 GiB).

CI is on hold per Lead. No build dispatch until Lead confirms the window; then the prepared run is
`steps="kernel payload bootimg"` with `uefi_archive_release_tag=uefi-luming-ci-diag`, sha
`109777c2…`, kernelcache `f18b4df8…`, reduced payload, CI panic_screen=false.
## 20. MEMDUMP diagnostic boot.img (2026-10-29) — local build ready

uefi-builder produced a MEMDUMP diagnostic FD (no 385 MB bundle):

- FD: `D:\civitoip20\build\fw-msgdump\SILICIUM_UEFI.fd`, **3,145,728 B**,
  sha256 **`94499e29fb36b9d5d85a8355b3f1d21340186b4ef3b5d83cd135df5b29d47cb3`**
- Adds a 64 KiB MEMDUMP read from PA `0xE4000000` (`LUMDBG1` ASCII or hex preview) drawn after the
  15 s stall + 8 s viewing stall before clear, plus row-8
  `WIN <base> FB FC800000 COVER|NOCOVER`. Existing big BASE/ADDR/ARGS/ENTRY/SIZE + FREE rows kept;
  FVMAIN 3,920 B free; 58 images verified.

Rebuilt with the provided local command (patched `build/uni-local/unixnu`, LLVM, msys2
`C:\msys64\ucrt64\bin` dtc/fdtput) and `payload-t51.img`:

- **`D:\civitoip20\build\fw-msgdump\boot-msgdump.img`**
- **85,925,888 B**, sha256 **`72cc8a2369deedabb35cb1495d9e1aba5da1f9c0e65c67e20dcd514948088c3d`**
- embedded FD sha256 `94499e29…` (verified); payload sha256 `26247ef3…`; DTB `dc29a5e4…`
  (base bundle DTB already carries the splash node; local patched bootimg logged
  `splash_region already exists; leaving the device tree node as built`, non-fatal)
- deliverable copy: `agents/f2-luming/runs/msgdump-local/boot-msgdump.img` + `boot.json`
- Header v4, 80 MiB ramdisk; RAM-only `fastboot boot` — never flash.

Expected device screen: rows 2-7 STAGE 3 + BASE/ADDR/ARGS/ENTRY/SIZE, row 8
`WIN ... FB FC800000 COVER|NOCOVER`, then FREE rows, then MEMDUMP (or `NO MAGIC` + hex preview).
