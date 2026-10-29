# REPORT-SM8735-KERNEL — native format-2 XNU patch / component / config plan for luming (SM8735)

Task `task-334` (Route ①: the sheng/dada format-2 "6S Pro way"; route ② is cancelled). Owner
`kernel-analyst`. Workspace: `agents/f2-luming/patches-plan/` only. **No device operations, no
flash/boot.** Sources are read-only except this report.

State snapshot: 2026-10-29, ~02:55 +08. The `agents/f2-luming/` skeleton is now READY as a
format-2 skeleton (Lead: 248 checks/7 known gaps at hand-off; current `check-skeleton.py` reports
255 pass / 7 missing / 4 warn / 0 error). This report analyses the implementation gaps that remain
for the first kernel. Status labels used throughout:

> **Post-handoff update (2026-10-29 ~03:00, supersedes the "missing" list below):** device-builder
> has now applied the host-side graft — `drivers/LumingUfs/LumingUfs.cpp` (renamed, `userdata`,
> `qcom,sm8735-ufshc`, SMMU 0x60), `GccUfs.h` AGGRE 0x770f4, `kits/luming/BootLog.c` +
> `BootProcessProbe.c`, and the binding-builder component name. `check-skeleton.py` is 261 pass /
> 7 known gaps and `check-luming.py` is **139 pass / 0 errors**. The biggest blocker moved from
> "write the UFS component" to the **firmware→XNU UFS hand-off** (AI7 platform FDT + stock
> UFSDxe/ClockDxe/RpmhDxe/VcsDxe, PHY/link state, legacy-UTR vs MCQ, CAP-bit24/DMA<4GiB vs the
> 0x8c0000000 DRAM window). Remaining host-side action: add `sheng-smp=1`, `luming-log=1`,
> `luming-data-persist=2` (replace `sheng-data-persist`) to `board.toml` kernel_args, rename the
> BootLog `dada-log`/`DADALOG2` identity, and run the AI7 firmware validation. The detailed
> current-tree analysis is `agents/f2-luming/deep/REPORT-KERNEL-COMPONENTS-FLOW.md`.
>
> The analysis below is retained as the design record; where it says "missing/stale", the
> post-handoff state above is authoritative.

Status labels used throughout:

* **[ready]** — source/config exists locally and is expected to work with only file/series
  selection.
* **[adapted]** — exists but is copied/transformed and must be changed for luming; the change is
  named.
* **[missing]** — no source/config/input exists locally or the exact file is absent.

---

## 0. Decision and single biggest blocker

### 0.1 Chosen profile / config family

**Use the official `ipados-17.7.11-21H461` OS profile and the dada-final format-2 configuration
shape**, not the iOS 16 / Darwin 22 profile and not the `.tools/xnu-8796` source tree:

* The profile is `profiles/os/ipados-17.7.11-21H461/profile.toml` — Darwin 23.6.0, XNU
  `10063.141.1`, revision `d8b80295118ef25ac3a784134bcf95cd8e88109f`, kernelcache/ADT/trust-cache
  inputs pinned by the profile `[ready]`.
* **sheng** uses the same profile with a full iPadOS UI (official device record: native XNU +
  XnuPrelink, 31-root OS profile, native `ShengUfs`, SHNGROOT root; `REPORT-OFFICIAL-PATH.md:35`).
* **dada** uses the same profile and has the closest **proven minimal** shape: final state prelinks
  27 components including AMFI/PMGR, `early_security_init` restored, owner cache/SystemOS union,
  native UFS, and the kernel log records `launchd p1`, `backboardd`, `SpringBoard`,
  `runningboardd`, `lsd`, `cfprefsd`, `containermanage` (`dada-full/README.md:47-58`;
  `dada-full/docs/known-values.md:525-542`).
* **Do not use `.tools/xnu-8796`** for this profile: it is `xnu-8796.141.3` (Darwin 22.6) from the
  iOS 16 route. The proven profile's source is `xnu-10063.141.1`; it is not present locally and must
  be fetched by `unixnu fetch` / the macOS CI (`[missing]`, standard fetch step).
* The current `agents/f2-luming/skeleton` already points at this profile
  (`board.toml:33`, `board.toml:43-47`, `board.toml:99-104`) and has copied the dada-final
  AMFI/PMGR/owner-cache shape; use it as the base, not the earlier no-AMFI staging.

### 0.2 Single biggest blocker

**SM8735 UFS storage bring-up:** there is no finished `LumingUfs` component and no SM8735 UFS
host/PHY power-up sequence.

* The current `drivers/LumingUfs/` is still a **stale DadaUfs/SM8750 copy**: README says
  SM8750/SM8750 facts (`drivers/LumingUfs/README.md:3-12`), `GccUfs.h:2-3` says SM8750, the
  compatible list is `qcom,ufshc`/`qcom,sm8750-ufshc` (`DadaUfs.cpp:150`), and the root partition is
  **`linux`**, not luming `userdata` (`DadaUfs.cpp:1169`). `check-luming.py:279-296` expects
  `LumingUfs.cpp`, `kRootPartition="userdata"` and `qcom,ufshc`+`qcom,sm8735-ufshc`.
* The skeleton's catalog/archive wiring is already present: `patches/unixnu/unixnu-components-lumingufs.patch`
  adds the `LumingUfs` catalog entry, and `board.toml` selects `component:LumingUfs` with
  `CONFIG_XNU_NATIVE_UFS_ARCHIVE="{tree}/build/luming-ufs/libLumingUfs.a"`. But the required source
  name `drivers/LumingUfs/LumingUfs.cpp` does not exist — the directory still contains the copied
  `DadaUfs.cpp`, so `build-arm-driver.py LumingUfs` cannot compile and G2 fails.
* Even with the source adapted, the driver **adopts** the controller that firmware leaves running;
  it does not program the SM8735 QMP v4 **niobe** PHY. The luming UEFI currently does not embed the
  platform FDT fragment (`/soc/ufs0`, `ufs_clk*`, `ufs_phy_cfg`, `volt_regs`) that stock `UFSDxe`
  needs, so the UFS block may be unclocked at XNU entry (`agents/nativeufs-plan/REPORT-UFS-PLAN.md`
  §4; `agents/f2-luming/docs/KNOWN-VALUES.md` UFS rows). A cold QMP-v4-niobe PHY init would be a
  separate, larger job.
* Consequence: a kernel can be compiled/prelinked with `CONFIG_XNU_NATIVE_UFS=n` (a console-only
  first build), but a kernel that can mount the root and reach userland is blocked on this
  component+PHY/firmware work. That is the one piece that dominates the schedule.

Everything else in the kernel patch/config plan is locally available or a one-line adaptation:
ArmDTPlatform/ArmCpu/SoftwareAES/RamBlock/VirtioMmioBlock/XnuPrelink/DarwinBoot sources, the
official profile, the 53-entry arch patch series, the OS series, and the Dada-copied device series.

### 0.3 First three concrete files to create

The catalog/archive entries already exist; these are the first three UFS-critical files to
create/rewrite (the rest of the plan is in §1–§7).

1. **`agents/f2-luming/drivers/LumingUfs/LumingUfs.cpp`**
   Fork the localized DadaUfs source
   (`agents/official-crawl/recipe/cache/dada-full/drivers/DadaUfs/DadaUfs.cpp`, 106,149 B) and
   adapt it for luming: accepted compatible `qcom,ufshc` + `qcom,sm8735-ufshc` (the live tree says
   `qcom,ufshc`), root partition **`userdata`**, UFS/RootLayout window handling matching luming's
   `SHNGROOT`, and the build-visible source name `LumingUfs.cpp`.
2. **`agents/f2-luming/drivers/LumingUfs/GccUfs.h`**
   Replace the current SM8750 table with the SM8735 `gcc-tuna` table already prepared at
   `agents/nativeufs-fix/driver/GccUfsSm8735.h` (eight of nine UFS branch offsets differ from
   SM8550; against SM8750 only `GCC_AGGRE_UFS_PHY_AXI_ENABLE` moves 0x770f0→0x770f4; GDSC/BCR
   facts are recorded there). `check-luming.py:303-315` asserts the SM8735 values.
3. **`agents/f2-luming/firmware/fdt/luming-ufs-platform.dtb`**
   The UEFI platform-FDT fragment for luming's stock vendor `UFSDxe`/`ClockDxe` (the
   `/soc/ufs0`, `ufs_clk0..8`, `ufs_phy_cfg`, `volt_regs`, init/perf speed and timeout nodes from
   `backup/analysis/uefiplat-fdt-dump.json` / `agents/nativeufs-plan/evidence/xbl_config-fdt1-dump.txt`).
   This must be embedded by the luming UEFI image (firmware team); without it the UFS driver sees a
   gated controller. If the firmware path is fixed differently, this file becomes the documented
   input rather than a separate firmware change.

Immediately after these: update `scripts/build-storage-kext-bindings.py` from its DadaUfs defaults
(`scripts/build-storage-kext-bindings.py:270,300`) to `LumingUfs`/`build/luming-ufs`; create
`kits/luming/BootLog.c` + `BootProcessProbe.c` required by `scripts/build-luming-boot-log.py:11,35`,
`CONFIG_XNU_LUMING_BOOT_LOG`, and `check-luming.py:316-319`; add the `check_sm8735_facts.py` test and
remove the SM8750 test (`check-luming.py:320-325`); then run the build gates in §5. The catalog and
board wiring are already present; the current 7 known gaps are listed by
`python scripts/check-skeleton.py` and `python scripts/check-luming.py`.

---

## 1. Patch-series plan by level (arch / soc / os / device)

The format-2 resolver applies four series in this order: `arch:...`, `soc:...`, `os:...`,
`device:...` (`board.toml:72`). Arrays replace inherited arrays; the board must carry the complete
list it wants (`UniXNU docs/porting/device-repository`, `sheng porting.toml:10-15`).

### 1.1 `arch` — official ARM64/Darwin-23 series: 53 entries, **[ready]**

Source: `unixnu-format2/UniXNU/profiles/arch/arm64/patches/xnu/series` (53 lines). These are
generic ARM64/4KiB/BCM2837/Darwin-23 patches, owned by UniXNU, not by luming. They are **used
unchanged**; no SM8735-specific arch patch is needed for the first kernel. Groups and target
files:

| Group (entries) | Purpose / target files | Deps / risk |
| --- | --- | --- |
| Build/toolchain: `apple-only-cpu-tunables`, `cxx-flag-dependencies`, `external-archive-dependencies`, `kernel-sdk-root`, `local-availability`, `source-machine-layer`, `source-pthread-bootstrap`, `source-corecrypto14-bootstrap` | make XNU build from Apple source with the 4K `BCM2837` machine layer; targets `makedefs/*`, `bsd/conf/Makefile.template`, `config/MASTER*`, `osfmk/prng/prng_random.c`, `bsd/kern/source_pthread_bootstrap.c` | Official CI-proven on sheng/dada; risk only if we edit the profile/defconfig incompatibly |
| 4K bootstrap/ABI: `native-4k-bootstrap-capacity`, `native-4k-signature-hash-cache`, `native-4k-user-abi`, `native-arm-pan`, `native-text-fixup`, `non-apple-pmap-field`, `non-apple-iommu-bootstrap`, `non-apple-cache-monitor`, `zzx-pmap-sync-64bit-pa` | 4 KiB pages, code-signing hash cache, pmap bootstrap, 64-bit PA sync; target `osfmk/arm/**`, `osfmk/arm64/**`, `bsd/kern/mach_loader.c` | Luming is 4K; `native-4k-user-abi` is mandatory for arm64 userland; risk = low |
| Platform expert/timer/DT: `architectural-timer-entry`, `armvirt-platform-personality`, `native-dt-panic-region`, `native-quiet-managed-page-report` | Darwin 23 timer entry; ARM virt personality for QEMU; DT panic region; memory-report noise; target `iokit/KernelConfigTables.cpp`, `pexpert/**` | `native-dt-panic-region` is mandatory (BCM2837 fallback address is a DRAM hole on luming); **no `/pram` binding exists yet** — see §1.5 |
| Security/owner/AGX: `native-trust-cache-runtime`, `public-entitlements-header`, `native-priv-work-interval`, `native-work-interval-*`, `published-freezer-condition`, `offline-owner-*` (`boot-manifest`, `cache-carrier`, `systemos-mount`, `root-binding`, `root-crypto`, `component-load-probes`), `offline-legacy-start`, `offline-*air*`, `offline-pgz-*`, `pgz-aligned-validation` | Prelinked trust cache optionality, entitlement header, owner-root/cache/SystemOS hooks; targets `bsd/kern/kern_trustcache.c`, `bsd/kern/kern_priv.c`, `bsd/vfs`, IOKit | **Dada-final relies on these**: AMFI/PMGR/trust-cache/owner-cache flow; risk = configuration coupling with dada device patches |
| Graphics/Wi-Fi sandbox/staged apps: `zzw-native-adreno-sandbox-grant`, `zzwb-native-sandbox-grant-set-properties`, `zzy-native-gpu-addon-mount`, `zzy-staged-system-apps` | Sandbox grants and staged app paths; targets `iokit/Kernel/IOUserClient.cpp`, `bsd/kern/kern_exec.c`, `bsd/miscfs/bindfs` | Not needed for first console/root; harmless inherited; risk = none for build |
| Mockfs/QEMU: `mockfs-*` (5) | QEMU root fixture; target `bsd/miscfs/mockfs/*` | `CONFIG_XNU_SOURCE_MOCKFS=n`; not selected for the device; keep for QEMU |
| Misc: `disabled-deferred-reclaim` (`vm_user.c`), `native-lookup-trace`, `native-union-*`, `*work-interval*` | debug/VM behavior | low |

**Risk overall:** low and managed by the profile; do not copy these into the device repo. The only
luming-sensitive entries are `native-4k-user-abi`, `native-dt-panic-region`,
`native-trust-cache-runtime` and the owner-cache set — their config switches must match the chosen
Dada final shape (§2).

### 1.2 `os` — official profile series: 3 entries, **[ready]**

Source: `profiles/os/ipados-17.7.11-21H461/patches/xnu/series`:

| Entry | Purpose / target | Deps / risk |
| --- | --- | --- |
| `zzz-boot-progress.patch` | boot-progress owner-root instrumentation | Config `CONFIG_XNU_BOOT_PROGRESS=n` in dada/luming; patch compiles to no-op or is gated; keep only because profile owns it |
| `component:XnuPrelink/patches/xnu-10063.141.1-security-init.patch` | prelink early-security init hook for AMFI | Required for **Dada-final AMFI** path; uses `early_security_init` address from profile |
| `component:XnuPrelink/patches/xnu-10063.141.1-sparse-index.patch` | XnuPrelink sparse-index ABI | Required by prelink tool; no board change |

No SM8735-specific OS patch is needed. The **profile itself** supplies the pinned kernelcache,
slide, roots, `early_security_init`, trust-cache pins and ADT identity
(`profile.toml:28-42`). The board overrides only where dada/luming differ.

### 1.3 `soc` — SM8550/SM8735 common series: 2 entries, one **[adapted]**, one replaced

Source: `unixnu-format2/UniXNU-sm8550-common/patches/xnu/series`; the sm8735 scaffold copies them
(`unixnu-format2/UniXNU-sm8735-common/patches/xnu/series`), and the f2 skeleton vendors them in
`soc/patches/xnu/`.

| Entry | Existing content | Luming disposition |
| --- | --- | --- |
| `native-smp-secondary.patch` | `pexpert/pexpert/arm64/board_config.h`: `MAX_CPUS 4→8`; `osfmk/arm64/start.s`: mask `MPIDR&0xFFFF` for Aff1 core numbering under `HAS_CLUSTER||BCM2837` | **[adapted]** — luming has 8 cores with MPIDR Aff1 `0x000..0x700`; the patch content is correct; must be **re-applied to xnu-10063.141.1** and build-tested. It is the only soc patch currently active in `soc/patches/xnu/series` (`agents/f2-luming/soc/patches/xnu/series:6`). |
| `sheng-platform-power.patch` | `bsd/kern/bsd_init.c` one hunk: `extern void sheng_pmgr_run(void); sheng_pmgr_run();` under `XNU_SHENG_PMGR` | **[adapted elsewhere]** — not active in `soc/` (commented at `soc/patches/xnu/series:7-10`). Dada's identical patch is copied into the **device** series as `zzzzzzzzzzzzzzzzz-luming-sheng-pmgr-call.patch` (`patches/xnu/device/series:23`). Keep it in device, not SoC; it is needed for the final AMFI+PMGR path and is inert when `CONFIG_XNU_SHENG_PMGR=n`. |

**SM8735-specific SoC patches that must be written:** none for the first kernel beyond the
`native-smp-secondary` adaptation. The UFS/GCC work is a **component**, not an XNU patch (§3).
A future `sm8735-platform-power` patch is only needed if the Dada PMGR instrument cannot be reused;
the current Dada copy (`drivers/LumingPlatformPower/ShengPlatformPower.cpp`,
`scripts/build-luming-platform-power.py`) is the preferred route.

### 1.4 `device` — luming-owned series: current Dada copies **[adapted]**; no new XNU patch required for first kernel

Current files: `agents/f2-luming/patches/xnu/device/` (copied from
`agents/official-crawl/recipe/cache/dada-full/patches/xnu/`, names `dada→luming`). Active order in
`patches/xnu/device/series:11-24`:

| Patch | Purpose / target | Status |
| --- | --- | --- |
| `zzz-boot-progress-min.patch` | minimal boot progress for the owner path | **[adapted]** copied; inert with `CONFIG_XNU_BOOT_PROGRESS=n` |
| `zzzzzzz-luming-owner-cache-diagnostics.patch`, `zzzzzzz-luming-cache-path.patch`, `zzzzzzzz-luming-owner-cache-initproc-panic.patch`, `zzzzzzzzz-luming-owner-cache-probe.patch`, `zzzzzzzzzz-luming-owner-cache-root-list.patch`, `zzzzzzzzzzz-luming-owner-cache-root-hex.patch`, `zzzzzzzzzzzz-luming-owner-cache-dirent32.patch`, `zzzzzzzzzzzzz-luming-owner-cache-lib-list.patch`, `zzzzzzzzzzzzzz-luming-owner-cache-union-env.patch` | SystemOS/owner-cache mount, dyld path, union mount, diagnostics | **[adapted]** from Dada final; needed for launchd/SystemOS; risk = they assume the same 21H461 cache layout and UFS root provider, both true for the chosen profile |
| `zzzzzzzzzzzzzzzzz-luming-sheng-pmgr-call.patch` | calls `sheng_pmgr_run()` from `bsd_init()` under `XNU_SHENG_PMGR` | **[adapted]**; depends on `drivers/LumingPlatformPower` and `CONFIG_XNU_SHENG_PMGR=y`; this is the only XNU patch on the AMFI/PMGR path |
| `zzzzzzzzzzzzzzzzz-luming-ufs-log.patch` | UFS boot-log writer instrumentation | **[adapted]** diagnostic; needed with `CONFIG_XNU_LUMING_BOOT_LOG=y` |
| Inactive fallbacks: `zzzz-luming-skip-entitlement-acceleration-without-amfi`, `zzzz-luming-skip-root-auth-gate-without-owner-audit`, `zzzzz-luming-entitlements-without-amfi`, `zzzzzz-luming-more-amfi-null-guards`, `zzzzzzzzzzzzzzz-luming-no-cs-bringup` | no-AMFI guards / no-code-signing | **[adapted] fallback only**; active only if the AMFI+PMGR path is unavailable. Dada reached first launchd exec with these, but then hit AMFI NULL walls; final Dada restores AMFI+PMGR (`dada-full/docs/known-values.md:236-298,525-542`). Do not enable them in the target build. |

**New SM8735 XNU patches:** none required if the UFS work stays in the component and the Dada
PMGR/owner-cache series is reused. The candidate “xiaomi,luming platform expert” mentioned in
Dada's open measurements (`dada-full/docs/known-values.md:536`) is **not required** for the first
boot because `ArmDTPlatform` is generic and matches the root `device-tree` name; a board-specific
expert becomes needed only if firmware/ADT identity must be changed.

### 1.5 UniXNU-side patches (not a kernel series, but required to make the kernel image usable)

| Patch | Purpose / status |
| --- | --- |
| `patches/unixnu/unixnu-bootimg-header-v4.patch` | v4 header support (present in f2 skeleton; copies dada's patch) **[adapted/ready]** |
| `patches/unixnu/unixnu-kern-exit-owner-cache.patch` | owner-cache ExitBoot path (present) **[adapted]** |
| `unixnu-ufs-archive-override.patch` (from `dada-full/docs/patches/`) | honor `CONFIG_XNU_NATIVE_UFS_ARCHIVE` for the board transport **[adapted/ready to copy/verify]** |
| `unixnu-owner-cache-bringup.patch` (Dada) | relax owner build gate for bring-up **[adapted/ready to copy/verify]** |
| `unixnu-payload-amfi-guard.patch` (Dada) | apply PMGR requirement only when AMFI is prelinked **[adapted/ready to copy/verify]** |
| **`unixnu-dt-pram-asmb.patch`** | **MISSING:** format-2 ADT converter has typed `/chosen`/`/defaults`/`/options`/`/product`/`/buttons` but **not** a `/pram` child, `/chosen/asmb` child, or `virtual-timer-intid`; target `scripts/unixnu/devicetree.py`. Needed for full A-line ADT parity (`/pram` panic log + lp-sip); not needed for `bsd_init` if the panic path is skipped (`CONFIG_XNU_DT_PANIC_REGION` falls back safely when `/pram` absent — dada behavior). **[missing]** |

### 1.6 Dada no-AMFI vs Dada-final AMFI: both config items are documented; choose final

The task asks to include the no-AMFI/`early_security_init`/pc-relative config items from dada.
Dada has **two stages**, and luming should target the second but keep the first as a diagnostic
fallback:

| Item | Dada no-AMFI first boot (24 roots) | Dada final target (27 roots) |
| --- | --- | --- |
| roots | 24; no AMFI, PMGR, sandbox, IOGPU/IOMobileGraphics, IOHID/IOHIDEventDriver | 27; AMFI, PMGR, sandbox and AppleImage4 present (`dada-full/board.toml:71-99`) |
| `early_security_init` | not set/cleared | `com.apple.driver.AppleMobileFileIntegrity=0xfffffff005ab4ae0` (`dada-full/board.toml:70`) — must match the slide/kernelcache |
| `CONFIG_XNU_TRUST_CACHE_RUNTIME` | `n` (avoids “amfi interface not available”) | `y` (AMFI path, trust-cache lock init) (`dada-full/configs/dada_defconfig:46`) |
| AMFI-less XNU guards | active (`iokit/bsddev/IOKitBSDInit.cpp`, `iokit/Kernel/IOUserClient.cpp`, `bsd/kern/kern_cs.c`, `bsd/kern/ubc_subr.c`, …) | not needed; AMFI returns real entitlements |
| PMGR | absent; no `ApplePMGRNub`; no `sheng-pmgr` | `LumingPlatformPower`/DadaPlatformPower publishes `ApplePMGRNub`; `XNU_SHENG_PMGR=y`, `sheng-pmgr=2` |
| proved on dada? | root image mounted/first userland exec, then AMFI NULL panics (`known-values.md:349-352`) | launchd/backboardd/SpringBoard/runningboardd/lsd/cfprefsd/containermanage all run (`dada-full/README.md:47-58`) **[device]** |
| luming choice | compile/boot diagnostic fallback only | **target** |

For the target, the copied Dada device series already contains the final AMFI/PMGR/owner-cache
patches and the skeleton restores the 27-root/early-init shape (`agents/f2-luming/board.toml:43-47,
99-104`). The build must also carry the **trust-cache bundle** and **Data seed** the final path
needs; if those inputs are missing, use the no-AMFI fallback only for the console/root milestone,
not for launchd.

---

## 2. Components needed for luming

All paths below are local unless marked **[missing]**. The canonical catalog entries are in
`unixnu-format2/UniXNU/components.toml`; checked-out sources are in
`agents/a-ipados17/_extern/components/<ID>/` with `.revision` pins, and the Dada full reference is
`agents/official-crawl/recipe/cache/dada-full/`.

| Component / archive | Upstream source (local) | Build wrapper (sheng/dada pattern) | Luming-specific changes | Status |
| --- | --- | --- | --- | --- |
| **ArmDTPlatform** | `agents/a-ipados17/_extern/components/ArmDTPlatform/` rev `417ff95d…`; catalog `components.toml` | `component:ArmDTPlatform` → `build-arm-driver.py` | none in source; ADT must contain `/chosen` NVRAM proxy, `/options`, `/cpus`, `/arm-io`, `/defaults` (`ArmDTPlatform.cpp:8-16`) | **[ready]** |
| **ArmCpu** | `.../ArmCpu/` rev `9066b53b…`; catalog | `component:ArmCpu` | none in source; DTS/ADT must expose 8 CPUs with MPIDR Aff1 and GIC/timer nodes; `armcpu-spi-ipi` boot args if SGI missing (`ArmCpu.cpp:27-40`) | **[ready]** |
| **SoftwareAES** | `.../SoftwareAES/` rev `4a45326d…` | `component:SoftwareAES` + `build-software-aes-bindings.py` | none; uses source corecrypto/AES ABI (`NativeAES.cpp:1-40`) | **[ready]** |
| **build-corecrypto-14.py** | UniXNU base (`scripts/build-corecrypto-14.py`, profile-fed) | archive entry `build-corecrypto-14.py` and `... --namespace` (`sheng board.toml:20-21`; `dada-full/board.toml:49-51`) | none | **[ready]** |
| **build-libpthread-kernel.py** | UniXNU base | archive (`dada-full/board.toml:56`) | none | **[ready]** |
| **XnuPrelink** | `.../XnuPrelink/` rev `f876e3ee…`; catalog | profile prelink tool `kits/XnuPrelink/emit_prelink.py` | none; profile supplies tool/kernelcache/slide/roots | **[ready]** |
| **DarwinBoot** | `.../DarwinBoot/` rev `3325e352…`; catalog | firmware `loader = "firmware"` | none; luming firmware must embed it | **[ready] firmware side missing** |
| **RamBlock** | `.../RamBlock/` rev `25c57e0e…` | Dada builder `build-dada-ram-block.py`; luming analogue `scripts/build-luming-ram-block.py` exists | reuse LumingUfs storage bindings; publishes Data seed at `/private/var`; `NativeRamBlock.cpp` | **[adapted]** — builder exists but depends on `build/luming-ufs/compile-command.json`, which needs LumingUfs adaptation |
| **VirtioMmioBlock** | `.../VirtioMmioBlock/` rev `8ee3a5ab…` | `component:VirtioMmioBlock` / virtio-mmio bindings (sheng) | none for UFS root; dependency shape from Dada/Sheng; can stay unselected until needed | **[ready]** (generic) |
| **ShengUfs** (legacy placeholder) | `.../ShengUfs/` rev `e2b32cc4…`; catalog | `component:ShengUfs`; luming board currently selects it as placeholder | **do not use as-is**: SM8550 compatible/GCC/root partition; replace with LumingUfs | **[adapted → missing]** |
| **LumingUfs** (target) | **current `agents/f2-luming/drivers/LumingUfs/` is a stale DadaUfs copy**; reference DadaUfs full source at `dada-full/drivers/DadaUfs/` | new `component:LumingUfs` + `build-arm-driver.py`; storage class/binding archives | accept `qcom,ufshc`/`qcom,sm8735-ufshc`; GCC `gcc-tuna`; root partition `userdata`/SHNGROOT; keep `NativeUfs` class names; source file `LumingUfs.cpp`; catalog entry; update builders | **[missing]** (current files stale: `LumingUfs.cpp:150,1169`, `GccUfs.h:2-3`, `README.md:3-12`) |
| **IOStorageFamily class binding** | `refer/IOStorageFamily` input compiled by `scripts/build-storage-classes.py`; kernelcache `com.apple.iokit.IOStorageFamily` | `build-storage-classes.py` + `build-storage-kext-bindings.py --component LumingUfs` (config `CONFIG_XNU_NATIVE_UFS_ARCHIVE`) | change DadaUfs defaults → LumingUfs and build dir `build/luming-ufs`; rebind 190-slot vtable once (`build-storage-kext-bindings.py` docstring) | **[adapted]/[missing input]** |
| **LumingPlatformPower** | `agents/f2-luming/drivers/LumingPlatformPower/ShengPlatformPower.cpp` (copied DadaPlatformPower; 8,235 B) | `scripts/build-luming-platform-power.py` exists, binds kernelcache ApplePMGR/nub | rename `Dada*`/`sheng_pmgr_run` only if XNU patch naming changes; same kernelcache/slide means fixed bindings can be reused; verify addresses against luming kernelcache | **[adapted]** — host build not run |
| **GopFramebuffer/NativeMobileDisplay** | `.../GopFramebuffer/` rev `cf3b4297…`; `NativeGOPPresenter.cpp`, `NativeMobileDisplay.cpp`, `NativeLegacyDisplay.cpp`; Dada builder `build-dada-mobile-display.py` | `component:GopFramebuffer`; `build-gop-legacy-display.py`/luming clone | first boot uses **DarwinBoot GOP text console**, not this component; display service needs luming panel `o9_42_02_0a` 1236×2750, stride 4944 (provisional) and UEFI GOP handoff | **[adapted later]/[missing luming panel]** |
| **IOHID/touch** | sheng shape `.../ShengHidInput/` rev `5f3a37ce…`, `ShengNovatekTouch` rev `a1a6f2b1…` | `component:ShengHidInput` etc. | luming is **Synaptics TCM SPI** (`/soc/.../spi@a90000/synaptics_tcm@0`, IRQ GPIO 55/176, reset 55/189) — sheng Novatek/I²C not applicable; new component | **[missing]** |
| **AppleKeyStoreState** | `.../AppleKeyStoreState/` rev `42ff83e0…`; catalog | `component:AppleKeyStoreState` | optional owner-root/keybag path, not needed for no-AMFI fallback; Dada final may rely on trustcache/owner; retain checkout | **[ready]/[optional]** |
| **VerifiedRoot** | `.../VerifiedRoot/` rev `def02664…`; catalog | `component:VerifiedRoot`; storage policies | Dada first boot uses plain (unverified) path; VerifiedRoot no verified device; not required for first root if no owner policy; sheng uses it for owner root | **[ready]/[optional]** |
| **build-luming-boot-log.py** | script exists; expects `kits/luming/BootLog.c` and `BootProcessProbe.c` | `CONFIG_XNU_LUMING_BOOT_LOG=y` | **source files missing** (`scripts/build-luming-boot-log.py:11,35`; `kits/` only README) | **[missing]** |
| **build-luming-ram-block.py** | script exists | archive for Data seed | expects `/drivers/LumingUfs/LumingUfs.cpp` (`scripts/build-luming-ram-block.py:13`); current source has wrong filename | **[adapted]/[missing]** |
| **ShengHidInput/ShengNovatekTouch/ShengPreflight/Adreno740/Metal/Ath12kWifi/AirNir** | sheng-specific / gen8 GPU not Adreno 740 | not selected for first boot | do not port; different hardware | **[not applicable]** / **[missing later]** |

**Build-order dependency:** LumingUfs (with class bindings) → LumingRamBlock (reuses UFS bindings) →
LumingBootLog (compile-record based) → package/payload. The board's current archive list already
carries the intended commands (`agents/f2-luming/board.toml:78-92`), but several entries point at
scripts/sources that are stale or missing; validate each before G2.

---

## 3. Config fragments and defconfig delta

### 3.1 Three fragment layers and the target defconfig

The resolver applies `arch:configs/common.config`, `soc:configs/sm8735.config`,
`os:configs/ipados.config`, then the device `configs/luming_defconfig` last
(`board.toml:71`; `unixnu-format2/UniXNU-scripts` config merge semantics; sheng `porting.toml:10-15`).

**Arch fragment** `profiles/arch/arm64/configs/common.config` — 8 lines, **[ready]**:

```
CONFIG_XNU_BUILD_ARCHIVES=y
CONFIG_XNU_SOURCE_CORECRYPTO14=y
CONFIG_XNU_SOURCE_PTHREAD=y
CONFIG_XNU_ARM_DT_PLATFORM=y
CONFIG_XNU_ARMCPU=y
CONFIG_XNU_NATIVE_AES=y
CONFIG_XNU_NATIVE_ARCH_TIMER=y
CONFIG_XNU_NATIVE_PAN=y
```

**OS fragment** `profiles/os/ipados-17.7.11-21H461/configs/ipados.config` — 4 lines, **[ready]**:

```
CONFIG_XNU_TRUST_CACHE_RUNTIME=y
CONFIG_XNU_SOURCE_MOCKFS=y
CONFIG_XNU_NATIVE_CS_HASH_CACHE=y
CONFIG_XNU_CRYPTO_BOOTSTRAP="prelinked"
```

**SoC fragment** `configs/soc/sm8735.config` — currently only `CONFIG_XNU_NATIVE_ADRENO=n`
(`agents/f2-luming/soc/configs/sm8735.config:4-10`). Keep it minimal: SM8735 has a
`qcom,adreno-gpu-gen8-6-0` GPU, not the catalog's Adreno 740, so Adreno must stay off. The UFS
archive/PMGR/owner switches belong in the device defconfig, not the shared SoC fragment.

**Device defconfig** `configs/luming_defconfig` — the current skeleton is a direct Dada-final
adaptation (`agents/f2-luming/configs/luming_defconfig:9-56`), and this is the right target:

```
CONFIG_XNU_BUILD_ARCHIVES=y
CONFIG_XNU_SOURCE_CORECRYPTO14=y
CONFIG_XNU_SOURCE_PTHREAD=y
CONFIG_XNU_ARM_DT_PLATFORM=y
CONFIG_XNU_ARMCPU=y
CONFIG_XNU_NATIVE_UFS=y
CONFIG_XNU_NATIVE_UFS_ARCHIVE="{tree}/build/luming-ufs/libLumingUfs.a"
CONFIG_XNU_NATIVE_AES=y
CONFIG_XNU_TRUST_CACHE_RUNTIME=y
CONFIG_XNU_NATIVE_CS_HASH_CACHE=y
CONFIG_XNU_NATIVE_ARCH_TIMER=y
CONFIG_XNU_NATIVE_PAN=y
CONFIG_XNU_BOOT_PROGRESS=n
CONFIG_XNU_DT_PANIC_REGION=y
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
CONFIG_XNU_NATIVE_ADRENO=n
CONFIG_XNU_SHENG_PMGR=y
CONFIG_XNU_NATIVE_MOBILE_DISPLAY=n
CONFIG_XNU_ARMVIRT_PLATFORM=n
CONFIG_XNU_SOURCE_MOCKFS=n
CONFIG_XNU_NATIVE_LEGACY_DISPLAY=n
CONFIG_XNU_VERIFIED_ROOT_PROBE=n
```

This is Dada's **final proven shape** (`dada-full/configs/dada_defconfig:9-56`) with only
`DADA_BOOT_LOG→LUMING_BOOT_LOG` and the UFS archive renamed. The current file already matches it;
it is **[adapted]**, not invented.

### 3.2 Delta vs sheng (SM8550 full-UI) and dada (SM8750)

| Switch/feature | sheng defconfig | dada final | luming target |
| --- | --- | --- | --- |
| Native UFS | `y` (`ShengUfs` component) | `y` (`DadaUfs` + storage classes/bindings) | `y` (`LumingUfs`) |
| Native VirtioMmioBlock | `y` (`component:VirtioMmioBlock`) | dependency of DadaUfs | inherited as needed; not a boot feature |
| Native RamBlock | `y` | `y` + `DADA_BOOT_LOG` | `y` + `LUMING_BOOT_LOG` |
| VerifiedRoot probe | `y` + owner root trust/audit | not selected (plain reads; no policy) | `n`; owner path disabled |
| Owner cache / SystemOS / Data | `y` (sheng persistent store) | `y` (`OWNER_*` 6 switches) | `y` (same Dada final) |
| AMFI/PMGR prelink | AMFI early init, PMGR instrument via `build-sheng-platform-power.py` | AMFI+PMGR final | same final AMFI/PMGR from Dada; `SHENG_PMGR=y` |
| GPU/Adreno | `Adreno740`, `AdrenoMetal` | `n` (no Adreno 830) | `n` (gen8-6-0 has no catalog component) |
| Display/touch/WiFi | GopFramebuffer, ShengHidInput, Novatek, Ath12kWifi | `n`/not selected | `n` first; display/touch later (§6) |
| Legacy display/boot progress/zone pgz | `y`/`y`/`y` | `n` | `n` (text console via DarwinBoot/GOP) |
| 4K vs 16K granule | 4K `BCM2837` MACHINE profile | 4K same profile | 4K same profile |
| CPU count / GIC/timer | 8 CPUs; GIC/timer by ADT | 8 CPUs; same | 8 CPUs; `native-smp-secondary` MAX_CPUS=8; INTID 27 in DTS/ADT |

The **only functional deltas** from Dada final are the UFS transport name/archive and
`LUMING_BOOT_LOG`; the rest is luming hardware identity/DTS and the still-missing UFS
component/PHY/firmware work. This is why the Dada-final config is the right proven target.

### 3.3 Measured values that must flow into DTS/ADT (not defconfig)

* 8 CPUs, MPIDR Aff1 `0x0..0x700` (`agents/f2-luming/docs/KNOWN-VALUES.md` §2).
* GICD `0x17100000/0x10000`, GICR `0x17180000/0x200000` stride `0x40000`; virtual timer INTID **27**
  (`soc/dts/sm8735.dtsi`).
* UFS host `0x1d84000/0x3000`, ICE `0x1d88000/0x18000`, MCQ `0x1da5000`/`0x1da4000`, SPI 265,
  PHY `0x1d80000/0x2000` qmp-v4-niobe, SMMU stream `0x60`.
* DRAM `0x8c0000000/0x23ffff000` (may need 2 MiB alignment to `0x23ff00000`; early test).
* Splash/FB `0xfc800000/0x2b00000`, panel `qcom,mdss_dsi_o9_42_02_0a_dsc_cmd`, 1236×2750, stride
  4944 (provisional).
* `/chosen` security tuple, `amfi-only-platform-code` (profile value for AMFI final), `/pram` +
  `embedded-panic-log-size`, `/buttons` home-button-type 2, `/defaults` sleep-disabled.
* Current ADT converter lacks typed `/pram`, `/chosen/asmb`, `virtual-timer-intid`; see §1.5.

---

## 4. Exact build / prelink / package commands and validation gates

Run from the UniXNU checkout, using the official profile and the luming device repo. The commands
match sheng's documented flow (`unixnu-format2/UniXNU-sheng/README.md` build section) and Dada's
host build record (`dada-full/docs/evidence/kernel-build.json`):

```sh
# 1. resolve / validate (G0/G1)
cd D:/civitoip20/unixnu-format2/UniXNU
./unixnu defconfig luming_defconfig -D ../../agents/f2-luming
./unixnu fetch     -D ../../agents/f2-luming     # fetches xnu-10063.141.1 etc.; network needed
./unixnu status --json -D ../../agents/f2-luming
./unixnu tree      -D ../../agents/f2-luming

# 2. kernel + prelink (G2/G3)
./unixnu ipsw info  -D ../../agents/f2-luming
./unixnu ipsw fetch -D ../../agents/f2-luming
./unixnu build kernel -D ../../agents/f2-luming
# -> out/luming/ipados-17.7.11-21H461/luming/kernel/kernel.macho

# 3. package / payload / boot image (G4; payload also needs the platform seed/Data/trust inputs)
./unixnu build package -D ../../agents/f2-luming
./unixnu build payload -D ../../agents/f2-luming \
  --unique-chip-id "$UNIXNU_UNIQUE_CHIP_ID" \
  --data-ramdisk <data.dbr> --trust-cache <trust.bundle>
./unixnu build firmware -D ../../agents/f2-luming --uefi <uefi-luming checkout>
./unixnu bootimg -D ../../agents/f2-luming --uefi <uefi-luming checkout> --dtb <firmware.dtb>
```

**Expected artifacts (Dada final proportions, luming values to be recorded by CI):** prelinked
kernel ~50–51 MB / 27 components; package payload 192 MiB `LUMINGESP`; boot image Android header v4
~203 MB. The prelink report must show `slide=-0x1000000`, the 27 roots/closure, AMFI+PMGR, the
`early_security_init` value, and `runtime_qualified=false` (prelink is an ABI claim, not an
iPhone boot proof). Dada's build record is the reference: kernel 51,044,352 B,
`d47f4ac9…`; payload 201,326,592 B; boot 203,558,912 B; FD 3,145,728 B
(`dada-full/docs/evidence/kernel-build.json`).

### Gates

| Gate | Test | Pass criterion |
| --- | --- | --- |
| **G0 static** | `python agents/f2-luming/scripts/check-skeleton.py` and `scripts/check-luming.py`, TOML parse, series/file existence | Current skeleton: 255 pass / 7 missing / 4 warn / 0 error; `check-luming.py` must clear its `LumingUfs.cpp`/`userdata`/GCC/kit errors. No TOML errors; all series paths and referenced component/archive files resolve or are explicitly placeholder |
| **G1 resolver** | `./unixnu status --json`, `./unixnu tree` | device `luming`, SoC `sm8735` local feed, profile `ipados-17.7.11-21H461`, patch order arch→soc→os→device, components include `LumingUfs` (current include) and dependency closure (`VirtioMmioBlock`/`VerifiedRoot`) resolves |
| **G2 kernel build** | `./unixnu build kernel` | Native `xnu-10063.141.1` compiles and links; no missing archives; `kernel.macho` created; sha/size recorded |
| **G3 prelink** | inspect `kernel.macho`/prelink report | 27 components; AMFI/PMGR present; `early_security_init` set; slide `-0x1000000`; `AppleMobileFileIntegrity`/`ApplePMGR` not dropped by closure; UFS archive linked |
| **G4 package/payload/boot** | `build package/payload/bootimg` | payload 192 MiB, boot v4; ADT has `/cpus` 8/MPIDR Aff1, `/arm-io/intc`, `/arm-io/ufshc`/`ufsphy`, `/chosen dram-base/size`, splash node; payload.json hashes consistent |
| **G5 no-device validation** | unpack v4, mount FAT payload, parse ADT | Header offsets/pagesize/ramdisk match; kernel/ADT/payload hashes; no partition write |
| **Device S1–S7** | approval-gated only | firmware → ADT → bsd_init → UFS root → launchd/Hello; not part of this report |

**UFS-off first-build fallback:** if the UFS component cannot be linked yet, the kernel can be
built with `CONFIG_XNU_NATIVE_UFS=n` and the `build-storage-*`/LumingUfs-free archive list to prove
CPU/GIC/timer/console/`bsd_init` and the ADT. That is a **kernel diagnostic milestone only**, not a
root/boot target; record it as such and do not call it a Route ① completion. Dada's own history
used the same staged split (kernel first, storage then userland).

---

## 5. `arch`/`soc`/`os`/`device` summary

| Level | Exists now | SM8735-specific must-write | Status |
| --- | --- | --- | --- |
| arch | 53 official ARM64/Darwin-23 patches | none | **[ready]** |
| soc | sm8550-common 2 patches; sm8735 scaffold copies | only `native-smp-secondary.patch` adaptation/verification (8 CPUs/Aff1); no new SoC XNU patch for first boot | **[adapted]** |
| os | 3 profile patches | none (profile owns kernelcache/slide/roots/early init) | **[ready]** |
| device | 12 active Dada-copied patches + 5 inactive fallback | no new XNU patch required for first kernel if UFS stays a component; verify the copied rows against xnu-10063; `unixnu-dt-pram-asmb` upstream helper is the only missing non-device patch | **[adapted]** / one **[missing]** |
| components | ArmDTPlatform/ArmCpu/SoftwareAES/RamBlock/Virtio/xnu prelink/DarwinBoot ready; LumingUfs stale; display/touch/missing | LumingUfs adaptation + UFS PHY/firmware platform FDT; later display/touch | **[ready]** + **[missing]** |

---

## 6. Driver-borrowing map (concrete sources and expected effort)

This map tells the implementer **what to copy from where**, and what to expect once
`agents/luming-stock-kernel/` (hw-integrator's stock Android kernel source index) lands. That
directory is **not present yet** (checked); the local partial evidence already available is named.

| Luming driver | (a) format-2 source — best XNU IOKit style | (b) luming stock Android kernel + DTS (authoritative sequences; pending index) | (c) earlier NativeUfs SM8735 work | Classification / effort |
| --- | --- | --- | --- | --- |
| **UFS host/transport** | `agents/official-crawl/recipe/cache/dada-full/drivers/DadaUfs/` (full `LumingUfs.cpp`, `RootCommands.h`, `RootLayout.h`, `RootPublication.h`, `RootQueue.h`, `SmmuTakeover.h`); sheng `agents/a-ipados17/_extern/components/ShengUfs/` for the component shape | expected: `drivers/ufs/host/ufs-qcom.c`, `drivers/ufs/core/ufshcd.c`, `ufs-qcom` DT nodes, `xbl_config-fdt1-dump.txt` platform `/soc/ufs0` config | `agents/nativeufs-fix/patches/0001-0002`, `driver/GccUfsSm8735.h`, `driver/UfsStage.h/UfsSnapshot.h`; `agents/ufs-ci/REPORT-UFS-CI.md`, `REPORT-CLEAN*.md` | **[copy-adapt]**, 2–4 d host + 2–4 d hardware; blocker |
| **GCC/clock** | Dada `drivers/DadaUfs/GccUfs.h` (SM8750 table) as structure | expected: `drivers/clk/qcom/gcc-tuna.c`, `include/dt-bindings/clock/qcom,gcc-tuna.h`; local partial copies already exist: `agents/nativeufs-plan/evidence/gcc-tuna.c`, `qcom,gcc-tuna.h` | `agents/nativeufs-fix/driver/GccUfsSm8735.h` (transcribed UFS offsets/GDSC/BCR) | **[copy-adapt]** 0.5–1 d; GCC writes not needed for read-only probe |
| **UFS PHY qmp-v4-niobe** | no format-2 PHY component; sheng/dada both rely on firmware link and do **not** program PHY (`dada-full/docs/ufs-dada.md:180-200`) | expected: `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`, `phy-qcom-qmp.h`, DTS `ufsphy_mem@1d80000`, `xbl_config` `/soc/ufs0/ufs_phy_cfg` | no A-line PHY init; only facts in `agents/nativeufs-plan/REPORT-UFS-PLAN.md` §3/§8 | **[reimplement-from-sequence] / [missing]**, 3–6 d if firmware does not leave link up; 0 d if it does |
| **Display/panel** | `agents/a-ipados17/_extern/components/GopFramebuffer/` (`NativeGOPPresenter.cpp`, `NativeMobileDisplay.cpp`, `NativeLegacyDisplay.cpp`); Dada `scripts/build-dada-mobile-display.py` + `LegacyDisplayProbe.cpp` | expected: `techpack/display`/`drivers/gpu/drm/msm/dsi` DSI panel `o9_42_02_0a`, `dispcc-tuna`; DTS panel/timing | A-line framebuffer/panic console markers; f2 facts (`docs/KNOWN-VALUES.md` §5) | **[copy-adapt] / [reimplement-from-sequence]**; first boot uses **DarwinBoot GOP text console**, display service later 1–2 weeks |
| **Touch / keys (HID)** | sheng `ShengHidInput/` + `ShengNovatekTouch/` only as **Apple HID shape**; luming is different controller | expected: `drivers/input/touchscreen/synaptics_tcm_spi.c`, `synaptics_tcm_core.c`, DTS `synaptics_tcm@0` (IRQ GPIO 55/176, reset 55/189, SPI 15 MHz) | none | **[reimplement-from-sequence] / [missing]**, 1–2 weeks; after SpringBoard |
| **RPMh/PMIC** | `drivers/LumingPlatformPower/ShengPlatformPower.cpp` (copied Dada; ApplePMGRNub binding) + `scripts/build-luming-platform-power.py`; sheng package `QcomRpmh.c` reference | expected: `drivers/soc/qcom/rpmh-rsc.c`, `rpmh.c`, `drivers/mailbox/qcom-ipcc.c`, PMIC `qcom-spmi-pmic`/`qpnp-*`, DTS `rsc@17a00000`, PM8550 nodes | A-line has no PMGR; Dada final provides the kernelcache-bound PMGR instrument | **[copy-adapt]** PMGR 2–4 d; real PMIC/battery later 1–2 weeks; required for final AMFI path |
| **USB** | no selected format-2 USB component (sheng package is the closest; no luming port) | expected: `drivers/usb/dwc3/dwc3-qcom.c`, `drivers/phy/qualcomm/phy-qcom-qusb2.c`, role-switch/Type-C, DTS USB nodes | none (A-line had no XNU USB) | **[missing]** 1–2 weeks; not needed for first root/launchd |
| **PCIe** | `agents/a-ipados17/_extern/components/Ath12kWifi/` (PCIe/MSI/DMA/Wi-Fi stack, sheng verified) as XNU component shape | expected: `drivers/pci/controller/dwc/pcie-qcom.c`, `pcie-designware*`, `phy-qcom-qmp-pcie*`, DTS `pcie@...` | none | **[copy-adapt] / [reimplement]** 2–4 weeks; later, not first boot |

**Files to borrow once the stock index lands:** add a field to the index
(`agents/luming-stock-kernel/source-index.json` or `INDEX.md`, path TBD) with the exact tree
paths above and commit id; then copy:
`drivers/clk/qcom/gcc-tuna.c` (already partially captured), `drivers/ufs/host/ufs-qcom.c`,
`drivers/ufs/core/ufshcd.c`, `drivers/phy/qualcomm/phy-qcom-qmp-ufs.c`,
`drivers/phy/qualcomm/phy-qcom-qmp.h`, display/DSI panel sources, `synaptics_tcm_*`,
`drivers/soc/qcom/rpmh*`, `drivers/mailbox/qcom-ipcc.c`, `drivers/mfd/qcom-spmi-pmic.c`,
`drivers/usb/dwc3/dwc3-qcom.c`, `drivers/pci/controller/dwc/pcie-qcom.c`, and the matching
`arch/arm64/boot/dts/qcom/tuna*.dtsi`/luming board DTS. Confirm actual filenames against the index;
do not guess when copying.

---

## 7. Top risks / unknowns and early tests

| # | Risk | Why / early test (host-only) | Mitigation |
| --- | --- | --- | --- |
| **R1 (biggest)** | SM8735 UFS host/PHY/firmware not ready; LumingUfs is stale Dada source; controller may be unclocked at XNU entry | First test: host-compile LumingUfs after adaptation; run new `check_sm8735_facts.py` against stock DT and GCC table; verify uefi-luming platform FDT contains `/soc/ufs0` (string/DT scan) | Adapt LumingUfs/GCC; embed platform FDT; if firmware cannot leave link up, add QMP v4-niobe init; accept console-only kernel milestone in the meantime |
| R2 | Current skeleton is static-ready but its `check-luming.py` hard errors remain (LumingUfs source name/partition/GCC/kit) | `python scripts/check-skeleton.py` → 255/7; `python scripts/check-luming.py` shows the LumingUfs/BootLog errors | Fix the component and kit sources; keep both checks green before G2 |
| R3 | Current `LumingUfs` is Dada/SM8750: root partition `linux`, accepted `sm8750-ufshc`, AGGRE 0x770f0 (`DadaUfs.cpp:150,1169`; `GccUfs.h:2-3`) | `check-luming.py:279-315` fails on source name, partition, compatibles and AGGRE; host test `check_sm8750_facts.py` also wrong | Replace with SM8735 table; root partition `userdata`; rebuild bindings |
| R4 | `build-storage-kext-bindings.py` still defaults to `DadaUfs`/`build/dada-ufs` (`scripts/build-storage-kext-bindings.py:270,300`); board does pass `--component LumingUfs` | Dry-run builder with `--component LumingUfs` fails on catalog/component path/source file | Update defaults; verify archive `libLumingUfs.a` has bound object |
| R5 | `build-luming-boot-log.py` needs `kits/luming/BootLog.c`/`BootProcessProbe.c`, absent | Run builder; currently fails missing source (`:11,35`); `CONFIG_XNU_LUMING_BOOT_LOG=y` | Create the kit sources or set the switch off for first build |
| R6 | Official profile source xnu-10063.141.1 not local; `.tools/xnu-8796` is Darwin22 and cannot be substituted | Check `unixnu fetch`/CI log; `.tools/xnu-8796` version mismatch | Fetch on Linux/macOS CI; never point the profile at `xnu-8796` |
| R7 | UFS PHY relies on firmware; QMP v4-niobe cold-init not implemented | Inspect UEFI platform FDT and stage-0 GCC/HC snapshot; if GDSC off/clocks off, driver cannot read | Fix firmware platform FDT first; PHY cold-init only if needed |
| R8 | Trust-cache/Data seed/platform seed/root UUID inputs missing for the final AMFI path | Payload build fails or prelink lacks AMFI? Check `board.toml` trust pins/`--data-ramdisk`/`--unique-chip-id`; compare profile UUIDs | Use profile-pinned 21H461 inputs; keep no-AMFI fallback only for diagnostics |
| R9 | Device patches copied from Dada may not apply to xnu-10063 or to luming changes | `patch --dry-run`/CI apply log per file; check line context before `build kernel` | Rebase each patch; keep only Dada final active rows |
| R10 | `RootLayout`/`RootPublication` currently assumes Dada `linux` partition/window semantics; luming uses `userdata` + SHNGROOT | Host fixture tests `drivers/LumingUfs/tests/*`; check `kRootPartition`/window map | Adapt to luming name/GPT facts; run host tests |
| R11 | Memory window `0x23ffff000` not 2 MiB aligned | ADT build/`payload.dram_size` check; if XNU/loader rejects, use `0x23ff00000` | Record which value was used; keep DTS/payload consistent |
| R12 | Display/touch/USB/PCIe absent; userland after launchd will fail at GUI | First boot only targets console/root/launchd; check dmesg/panic for missing services | Defer M5, scope userland milestone to launchd evidence |
| R13 | Firmware integration (UniXNU/DarwinBoot/RamDisk/FAT, FD size/base) missing | Firmware preflight/G3/G4; inspect FD strings/module list; `bootimg` v4 validation | uefi-builder work; do not claim boot before FD exists |

**Host-only early tests today (no device):**
1. Parse all TOMLs (`tomllib`) and patch series; the board now parses.
2. Run `python agents/f2-luming/scripts/check-skeleton.py` (255/7) **and**
   `python agents/f2-luming/scripts/check-luming.py`; the latter enumerates the LumingUfs/BootLog
   hard errors to fix.
3. `python scripts/unixnu/porting-record` style check if available; at minimum `unixnu status` /
   `unixnu tree` on a host with fetched sources.
4. LumingUfs host tests: create `drivers/LumingUfs/tests/check_sm8735_facts.py` from the SM8750 test
   (`gcc-tuna` offsets, UFS windows, PHY compatible, root partition `userdata`); run
   `check_root_path_host.py`, `check_legacy_descriptors.py`, `check_arm64_root_commands.py`.
5. Verify `CONFIG_XNU_*` archive commands resolve to existing scripts/sources; fail early on
   `LumingUfs.cpp` filename, `kits/luming/BootLog.c`, `refer/IOStorageFamily`, etc.
6. Build kernel/prelink on CI with `CONFIG_XNU_NATIVE_UFS=n` first (console-only) and assert 27
   components/AMFI/PMGR/early init after configuring the final shape; then add UFS.

---

## 8. First three concrete files and sequence

1. `agents/f2-luming/drivers/LumingUfs/LumingUfs.cpp` — adapt from DadaUfs:
   `accepted = {"qcom,ufshc","qcom,sm8735-ufshc"}`; `kRootPartition = "userdata"`; include the
   SM8735 `GccUfs.h`; update comments/README; keep `NativeUfs`/`NativeUfsBlock` runtime names.
2. `agents/f2-luming/drivers/LumingUfs/GccUfs.h` — replace the SM8750 table with
   `agents/nativeufs-fix/driver/GccUfsSm8735.h` content (eight of nine branches differ; GDSC/BCR
   facts included).
3. `agents/f2-luming/firmware/fdt/luming-ufs-platform.dtb` — platform FDT fragment from stock
   `xbl_config` (`/soc/ufs0`, clocks, PHY config, volt regs) for luming's stock `UFSDxe`; hand to
   uefi-builder for embedding in the firmware image.

Then, in order:
4. `scripts/build-storage-kext-bindings.py`: `--component LumingUfs`, build dir `build/luming-ufs`,
   object/source names; verify the `LumingUfs` catalog patch is present.
5. `kits/luming/BootLog.c` + `BootProcessProbe.c` (required by `check-luming.py`; or set
   `CONFIG_XNU_LUMING_BOOT_LOG=n` for the first build); `scripts/build-luming-ram-block.py` then
   works from `compile-command.json`.
6. Add `drivers/LumingUfs/tests/check_sm8735_facts.py`; remove/rename the SM8750 test.
7. Re-run G0/`check-luming.py`; fetch xnu-10063 source/toolchain on CI; run G1–G5; only then request
   the device gate (S1–S7).

No device operations are proposed in this report. The first three files are still host-side; the
only hardware action is the later UFS stage test, which requires the user's approval.

---

## 9. Evidence index

| Evidence | Used for |
| --- | --- |
| `unixnu-format2/UniXNU/profiles/os/ipados-17.7.11-21H461/profile.toml:28-42` | profile choice, xnu-10063 pins, slide, roots, early init, trust pins |
| `unixnu-format2/UniXNU/profiles/arch/arm64/patches/xnu/series` (53 entries); `profiles/arch/arm64/configs/common.config`; `profiles/os/.../configs/ipados.config` | arch/os series/config |
| `unixnu-format2/UniXNU-sheng/board.toml:19-45,102-103`; `configs/sheng_defconfig:1-23`; `README.md` build section | sheng format-2 reference/full UI |
| `unixnu-format2/UniXNU-sm8550-common/patches/xnu/{series,native-smp-secondary.patch,sheng-platform-power.patch}` | soc series content |
| `unixnu-format2/UniXNU-sm8735-common/{soc.toml,configs/sm8735.config,dts/sm8735.dtsi,patches/xnu/series}` | scaffold status |
| `agents/official-crawl/recipe/cache/dada-full/board.toml:9-25,40-99`; `configs/dada_defconfig:9-56`; `README.md:47-58`; `docs/known-values.md:172,236-298,525-542`; `docs/evidence/kernel-build.json` | Dada final proven config/evidence, AMFI/no-AMFI phases |
| `agents/official-crawl/cache/repos/dada/board.toml` / `docs/patches` | official-crawl Dada board snapshot |
| `agents/a-ipados17/_extern/components/{ArmDTPlatform,ArmCpu,SoftwareAES,RamBlock,VirtioMmioBlock,GopFramebuffer,ShengUfs,VerifiedRoot}/` + `.revision` | component sources/build interfaces |
| `unixnu-format2/UniXNU/components.toml` (catalog revisions/build stages) | component selection |
| `agents/nativeufs-fix/REPORT-NATIVEUFS-FIX.md:1-120`; `driver/GccUfsSm8735.h`; `patches/0001-0004`; `agents/nativeufs-plan/REPORT-UFS-PLAN.md:0-8,2-4`; `evidence/{gcc-tuna.c,qcom,gcc-tuna.h,stock-dtb-ufs-nodes.txt,xbl_config-fdt1-dump.txt}` | UFS/GCC/PHY facts and previous driver work |
| `agents/f2-luming/drivers/LumingUfs/{README.md:3-12,GccUfs.h:2-3,LumingUfs.cpp:150,1169}` | current stale-copy state |
| `agents/f2-luming/{board.toml:33,43-47,71-92,99-104},configs/luming_defconfig:9-56,patches/xnu/device/series:11-24}` | current skeleton target/shape |
| `agents/f2-luming/drivers/{README.md:11-13,NativeUfs/README.md:3-36,LumingDisplayTouch/README.md:1-25}`; `docs/{FIRST-BUILD-PLAN.md:16-113,GAP-LIST.md:8-27,A-FIX-CROSSWALK.md,KNOWN-VALUES.md,REFERENCE-SOURCES.md}` | gaps, build gates, measured values |
| `agents/official-crawl/recipe/cache/dada-full/scripts/{build-storage-classes.py,build-storage-kext-bindings.py:1-80,270,300,build-dada-ram-block.py,build-dada-platform-power.py,build-dada-boot-log.py}` | storage class/kext-binding and board-builder patterns |
| `agents/f2-luming/scripts/{build-storage-kext-bindings.py:270,300,build-luming-ram-block.py:12-16,build-luming-boot-log.py:11,35,build-luming-platform-power.py:43-44}` | current builder adaptation state |
| `backup/analysis/device-live/luming-live/` (DT/iomem/dmesg); `agents/c-ios16-star/evidence/luming-shim-facts.txt` | measured luming hardware facts |
| `agents/ufs-ci/REPORT-UFS-CI.md`, `REPORT-CLEAN*.md`; `agents/roots-userspace/route-b/verified-inventory.json` | A-line UFS facts and retired Route B inventory |
| `unixnu-format2/UniXNU-sheng/README.md` build commands; `agents/f2-luming/docs/FIRST-BUILD-PLAN.md:16-113` | exact build/gate commands |
