# A-FIX-CROSSWALK — A-line (prelinked CLEAN series) fixes/findings vs format-2

Purpose: for every fix or finding recorded by the A line on the **prelinked Darwin 22 luming
kernel** (`agents/ufs-ci/REPORT-CLEAN*.md`, the AQ..CW probe reports, `BOOT-SEQUENCE.md`,
`EC-STAGE-TABLE.md`), state whether format-2 needs it and, if yes, where it is reused.

Classification used below:
- **(a) architecture-eliminated** — format 2 removes the need for a binary/source workaround
  (source-built 4K XNU + official profiles + DarwinBoot handoff + native components).
- **(b) directly reusable** — a measured fact, ADT property, diagnostic technique or image
  artifact that this skeleton carries forward.
- **(c) needs rewrite** — the capability exists only as Sweet/SM8550/instrument code and must be
  reimplemented as a luming format-2 component.

Reference state of the A line (as of the latest reports available in this workspace,
2026-10-29 ~02:14): prelinked kernel reaches the kext-start stage on device; the CLEAN series
carries ~10 binary workarounds; the last device blocker was `com.apple.kec.corecrypto`'s kmod
start (CLEAN24 bypasses it). These are all symptoms of a **prelinked Apple-kernelcache route**;
format 2 does not link that artifact, so none of the binary patches below are on the format-2
critical path.

## (a) Architecture-eliminated fixes

| # | A-line fix / finding | Evidence | Why format 2 does not need it |
| --- | --- | --- | --- |
| a1 | **MMU-off entry preamble**: a stage-1 stub clears `SCTLR_EL1.M` before `_start_first_cpu` because the prelinked kernel was entered with translation enabled | `agents/ufs-ci/REPORT-CLEAN4.md` "What changed vs CLEAN3"; `BOOT-SEQUENCE.md` entry analysis | Format 2 enters XNU through DarwinBoot, which explicitly clears M/C/I and invalidates caches before `br x1` (`DarwinBootPkg/Driver/Entry.S`), and the kernel is built from source for the target profile. No binary preamble. |
| a2 | **BCM2837 / Apple CPU-override store NOP**: `str w1,[x0]` at `0xfffffff0073cb32c` writes `0xF0` to PA `0x40000040 + (MPIDR&0xff)*4`, an invalid address on luming (A-line got a Data Abort between stage 14 and 12) | `REPORT-CLEAN5.md` "extra patch"; `REPORT-AR.md:43`; `REPORT-AS.md:49`; `REPORT-AT.md:27` | The Apple CPU-override block is absent from the CI/GS source-built kernel (`REPORT-CLEAN3.md` static appendix) and is removed/guarded by the official arch machine-layer patches (`source-machine-layer.patch`, `armvirt-platform-personality.patch`). The format-2 kernel is that source-built kernel, not the prelinked Apple artifact. |
| a3 | **TTBR0 msr NOP and SCTLR readback "Yskip" self-loop NOP**: `msr ttbr0_el1` at `0xfffffff0073cf250` and a `b.ne` self-loop after the SCTLR readback were NOP'd during Uskip probes | `REPORT-AS.md:49`, `REPORT-AT.md:27,51`, `REPORT-AU.md:60`, `REPORT-CLEAN5.md` stage table | Same as a1/a2: these were workarounds around the prelinked image's entry/pagetable assumptions. DarwinBoot + 16K-native source build own the entry and bootstrap page tables. Keep the knowledge for debugging only. |
| a4 | **`pe_identify_machine` one-word NOP**: NOP the `cbz x0` early return after the DT machine-node lookup (real-ADT UBSAN workaround) | `REPORT-CLEAN9.md` "Patch (ONE word...)"; inherited by CLEAN10+ | The official `ArmDTPlatform`/`ArmCpu` components and the profile's platform code replace Apple's machine identification; format 2 does not run `pe_identify_machine` from a prelinked Apple platform expert. |
| a5 | **Console/video `ret` skips**: `_PE_create_console`, `_PE_initialize_console`, `_PE_init_printf` returned immediately to get past Apple video/console code | `REPORT-CLEAN16.md:200-204`; retained by CLEAN17+ | dada's first boot proves the valid path: DarwinBoot fills `boot_args.Video[6]` from the UEFI GOP and XNU's pexpert video console draws through it, with no binary console bypass. |
| a6 | **Kext security-extension / startup-extension skips**: `ret` at `KLDBootstrap::loadSecurityExtensions` (CLEAN18), `readStartupExtensions` and `_mac_policy_initmach` (CLEAN19); proved the wrong direction on device (stage 5, later init breaks) | `REPORT-CLEAN18.md`, `REPORT-CLEAN19.md` | Format 2 builds/ships its kernel with the profile's kext set; the prelink roots decide what is present. Skips are not carried forward (and are explicitly documented as wrong). |
| a7 | **AppleImage4 `start` trampoline bypass**: one word `cbz x2,+8` -> `b +8` so the kmod start returns success | `REPORT-CLEAN21.md`; A-line next-panic mapping | Format 2 keeps `com.apple.security.AppleImage4` as a normal prelink root (dada's 24-root list includes it) and builds the security path from source; no prelinked kext-start bypass. |
| a8 | **AppleARMPlatform/AppleARMCPU `IONameMatch` plist rename**: `AppleARM` -> `AppleARx`, `cpu` -> `zpu` in `__PRELINK_INFO` to stop Apple's CPU validator panic | `REPORT-CLEAN22.md` | Format 2's own `ArmCpu`/`ArmDTPlatform` components and generated prelink have no stale Apple personalities; no plist editing. |
| a9 | **corecrypto kmod-start trampoline bypass**: one word in `com.apple.kec.corecrypto`'s start trampoline | `REPORT-CLEAN24.md` | Format 2 builds source corecrypto (`build-corecrypto-14.py` + `--namespace`) and `SoftwareAES` from source; there is no prelinked corecrypto kext whose trampoline would hang. |
| a10 | **panic/assert log-and-return**: `_Assert`/`_panic_with_options` entry -> `ret` to silence the AppleImage4 panic | `REPORT-CLEAN20.md` | Not needed once the security path is built rather than bypassed; the real panic path is wanted. |
| a11 | **`_kprintf` / helper `ret` hacks** used by the A console instrumentation | `BOOT-SEQUENCE.md` findings | Format 2 uses a real console (DarwinBoot GOP video + pexpert); no ret hacks. |
| a12 | **`com.apple.driver.AppleMobileFileIntegrity`/`ApplePMGR` restore in the prelink roots** | dada current HEAD / clone recipe §2.1: 27 roots incl AMFI+PMGR+sandbox+AppleImage4, `early_security_init` restored, trust-cache runtime on; the earlier 24-root no-AMFI variant is documented history and dead-ends after launchd | Carried forward as the proven shape: board.toml `[kernel.prelink]` 27 roots + early init; defconfig trust-cache/owner switches; copied `build-luming-platform-power.py`; trust-cache pin |

**Result:** none of the A-line binary patches (a1-a11) are required by format 2. The only
A-line-derived configuration that is carried into a fix is a12 (no-AMFI prelink roots).

## (b) Directly reusable facts / findings

Landing means the value is present in this skeleton file with a source pointer; format-2
mechanisms limit where it can formally take effect (see notes).

| # | A-line fact / finding | A-line evidence | Landed in this skeleton | Notes |
| --- | --- | --- | --- | --- |
| b1 | **Virtual timer INTID 27** (Qualcomm PPI 11 + 16) | A-line/format-1 ADT; `ios-sweet#14` cross-check; live DT timer PPI 13/14/11/12 | `soc/dts/sm8735.dtsi` gic node: `virtual-timer-intid = <27>` + comment; `docs/KNOWN-VALUES.md` #2 | The format-2 ADT converter has no typed binding for `virtual-timer-intid`; the arch profile `architectural-timer-entry.patch` owns the generic timer path. Kept as hardware documentation; do not assume it reaches the ADT yet. |
| b2 | **GIC windows** GICD `0x17100000/0x10000`, GICR `0x17180000/0x200000`, stride `0x40000` | live DT `interrupt-controller@17100000`; A-line/format-1 ADT | `soc/dts/sm8735.dtsi` gic `reg` + `redistributor-stride`; `docs/KNOWN-VALUES.md` #2 | Converter translates `reg` and exports as `/arm-io/intc`. |
| b3 | **UFS controller/PHY**: host `0x1d84000/0x3000`, ICE/MCQ windows, SPI 265, PHY `0x1d80000/0x2000` `qcom,ufs-phy-qmp-v4-niobe`, SMMU stream `0x60`, GPT `userdata` LBAs | A-line/UFSCI; NUFSPLAN; live DT | `soc/dts/sm8735.dtsi` `ufshc`/`ufsphy`; `docs/UFS.md`; `drivers/NativeUfs/README.md`; board.toml `[userdata]` | Component adaptation is (c1); the DT nodes are ready. |
| b4 | **DRAM window** `0x8c0000000..0xaffffefff` (`0x23ffff000`, ~9 GiB) and A-line physBase/markers inside it | IOMEM; `REPORT-CLEAN.md` "physBase≈0x8c01e06a0"; markers PA `0x8c4000000` | `dts/luming.dts` memory node; board.toml `[payload].dram_size`; `docs/KNOWN-VALUES.md` #3 | Alignment risk recorded in KNOWN-VALUES #3; may need 2 MiB-aligned size. |
| b5 | **8 CPUs / MPIDR Aff1 0..0x700** | live DT `/cpus`; A-line/format-1 ADT | `soc/dts/sm8735.dtsi` cpus; board.toml `[payload.adt].cpu_regs`; soc patch `native-smp-secondary.patch` | Format-2 ADT generator takes CPU affinities from the hardware DTS. |
| b6 | **Debug UART** `0xA9C000/0x4000`, SPI 579, 115200 8N1 | format-1 ADT generator measured comments; `agents/uart-debug/REPORT-UART.md` | `soc/dts/sm8735.dtsi` `uart` node (`unixnu,adt-name = "uart"`); `docs/KNOWN-VALUES.md` #5 | SE7 is disabled in the stock firmware; no physical UART fixture. Console for the first boot comes from the framebuffer. |
| b7 | **Framebuffer/panel**: FB base `0xFC800000`, splash `0x2b00000`, stride 4944, 1236x2750 | A-line/format-1 facts; live DT splash; DMESG | `dts/luming.dts` reserved-memory splash; board.toml `[[bootimg.dtb_node]]`; `docs/KNOWN-VALUES.md` #5 | DarwinBoot provides the GOP video for the text console; display service is (c2). |
| b8 | **ADT required properties**: `/pram` + `/chosen/embedded-panic-log-size`; `/chosen/asmb` `lp-sip0=0x6f`/`lp-sip1=1`; security/activation status tuple; `no-effaceable-storage`; `display-scale`; product/buttons | A-line/A-FIX findings; ios-sweet/format-1 ADT (`UniXNU-luming/scripts/make-luming-adt.py`); A-line CLEAN16 console work | board.toml `[adt.chosen.u32] embedded-panic-log-size=1048576`; `[adt.defaults.u32] sleep-disabled=1`; product/buttons typed tables; `docs/GAP-LIST.md` #6 lists the converter gaps | **Partial landing:** the format-2 ADT generator supports typed `/chosen`, `/defaults`, `/product`, `/buttons` properties, but **not** a `/pram` child node or a `/chosen/asmb` child node; it also inherits the iPadOS profile identity on the chosen route, so the iOS16 `asmb`/security overrides are not applied. A converter patch is required (gap #6). `embedded-panic-log-size` alone is harmless and skipped when `/pram` is absent (dada's CONFIG_XNU_DT_PANIC_REGION behaviour). |
| b9 | **Marker/reader diagnostic system**: 32-byte record `{magic,stage,PC,nonce}` at PA `0x8C4000000` (high-water channel `0x5F000000` in QEMU twins), GI reader, boot nonce, staged breadcrumbs, panic-screen renderer | `REPORT-CLEAN.md`, `REPORT-CLEAN2/3`, `EC-STAGE-TABLE.md`, `windows-ci` reader images | Documented in this crosswalk only; `docs/FIRST-BUILD-PLAN.md` records the same technique for the format-2 kernel phase (direct-FB markers + persistent boot log as the format-2 equivalents) | Not embedded as binary patches: format-2 debugging uses the official bring-up stages S1-S7 and the log-capture tooling; keep the A-line marker technique as a fallback if the format-2 kernel dies before its console. |
| b10 | **J2 super / stage-0 payload / DarwinBoot handoff infrastructure**: J2 header/table/member CRCs, AI6 boot image, auto-xnu timeout-0 config, DarwinBoot v4 image | `agents/ufs-ci/REPORT-UFS-CI.md` §4; `agents/uefi-log/REPORT-AI6.md` | `docs/FIRST-BUILD-PLAN.md` lists the J2/AI6 handoff as the fastboot-only fallback; board.toml `payload/bootimg` use the official format-2 payload + header v4 | The format-2 route uses UniXNU/DarwinBoot, not the J2 partition hand-off; the infrastructure is a fallback if ABL refuses the v4 boot image. |
| b11 | **iOS16 20H392 SHNGROOT userdata image** (`build/ios16-root/luming/userdata/userdata-root.img`) | `agents/roots-userspace/route-b/verified-inventory.json` | Not used on the chosen route (official iPadOS 17.7.11 profile; sheng SHNGROOT recipe); recorded in `docs/KNOWN-VALUES.md` #4 as retired alternative | Reusable only if the project ever returns to an iOS16/Darwin22 profile. |
| b12 | **NativeUfs SM8735 experience**: compatible `qcom,ufshc`/SoC names, SM8735 GCC offsets, stage-0 read-only snapshot, ABL-left controller adoption, UFSDxe-initialises-UFS proof | `agents/nativeufs-fix/patches`, `agents/ufs-ci/REPORT-UFS-CI.md`, `agents/nativeufs-plan/REPORT-UFS-PLAN.md` | `docs/UFS.md`; `drivers/NativeUfs/README.md`; `configs/luming_defconfig` UFS switches; board.toml archives placeholder | The driver becomes a format-2 component in (c1); the measured facts are ready. |

## (c) Needs rewrite for luming format 2

| # | Capability | A-line/legacy state | What format 2 needs | Where started |
| --- | --- | --- | --- | --- |
| c1 | **UFS storage transport** | prelinked NativeUfs driver + J2/stage0 payloads; SM8735 probe/GCC patches in a device-repo build path; not a catalog component | `LumingUfs` component: sheng `ShengUfs` fork with SM8735 constants, storage-class/kext-binding archive steps (dada), catalog entry, `CONFIG_XNU_NATIVE_UFS_ARCHIVE`; root path through SHNGROOT + VerifiedRoot | `drivers/NativeUfs/README.md`, `docs/UFS.md`, `configs/luming_defconfig` placeholder, board.toml archives placeholder |
| c2 | **Display service** (`IOMobileFramebuffer`) | A-line only had text console/panic screen; format-1 used patches/legacy display instrument | format-2 display component for luming panel (or first a minimal GOP/console-only path for S1-S6, then a framebuffer service) | `drivers/LumingDisplayTouch/README.md`, `docs/GAP-LIST.md` #4/#5 |
| c3 | **Touch / keys / HID input** | none on luming (format-1 TODO); sheng has Novatek/Goodix-class components | luming input component: keys via PMIC/SPMI and touch from the stock DT node, delivered as Apple HID events | `drivers/LumingDisplayTouch/README.md`, gap #5 |
| c4 | **AMFI + PMGR (optional later)** | A-line bypassed both; dada keeps them out | if the owner-root/AMFI path is wanted: a sheng-style `build-luming-platform-power.py` instrument publishing `ApplePMGRNub`, AMFI in prelink roots, early security init restored | `docs/GAP-LIST.md` #9; not needed for first boot |

## Summary counts

| Classification | Fixes/findings | On the format-2 critical path? |
| --- | --- | --- |
| (a) architecture-eliminated | 12 (a1-a12) | no; a12 is a prelink *configuration* choice, carried into board.toml |
| (b) directly reusable | 12 (b1-b12) | b1-b8 landed as files; b9-b12 documented/handoff-only |
| (c) needs rewrite | 4 (c1-c4) | c1 required for root; c2/c3 required for GUI; c4 optional |

The one thing the A line **must not** carry into format 2 is its binary-patch methodology: the
format-2 path is source-built, so any A-line symptom that reappears should be fixed in the
corresponding source patch/component, not by patching the prelinked image.
