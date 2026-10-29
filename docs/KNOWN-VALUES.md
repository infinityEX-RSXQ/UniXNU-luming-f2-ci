# KNOWN-VALUES — luming (SM8735) hardware and image facts used by this skeleton

Every value below is either measured on the luming device from the read-only stock Android capture
(2026-10-22) or adapted from a named reference; nothing is invented. Values that only a boot can
produce are marked [placeholder]/[missing] and listed in docs/GAP-LIST.md.

Source abbreviations:
- `DT` = `backup/analysis/device-live/luming-live/dtb-dump.json` (stock merged live device tree)
- `IOMEM` = `backup/analysis/device-live/luming-live/iomem.txt`
- `DMESG` = `backup/analysis/device-live/luming-live/dmesg.txt`
- `F1` = `UniXNU-luming/board.toml` (format-1 luming repo, measured values, capture 2026-10-22)
- `UFSCI` = `agents/ufs-ci/REPORT-UFS-CI.md`, `agents/ufs-ci/REPORT-CLEAN*.md`
- `NUFSPLAN` = `agents/nativeufs-plan/REPORT-UFS-PLAN.md`
- `GREP` = `agents/ufs-ci/REPORT-CLEAN*.md` / `EC-STAGE-TABLE.md` (A-line marker/boot findings)
- `DADA` = `docs/reference/dada-known-values.md` (cached format-2 reference)
- `SHENG` = `unixnu-format2/UniXNU-sheng/board.toml` + official docs

## 1. Board and SoC

| Fact | Value | Source |
| --- | --- | --- |
| Device / codename | Xiaomi Civi 5 Pro / `luming` | workspace README, F1 |
| SoC | Qualcomm SM8735 "Tuna" (`qcom,tuna` / `qcom,tunap`) | DT |
| RAM SKU | 12 GiB (11.27 GiB after carve-outs; MemTotal 11,503,328 kB) | F1, DT |
| GCC | `qcom,tuna-gcc`, `0x100000/0x1f4200`, syscon | DT |
| Apps SMMU | `qcom,qsmmu-v500`, `0x15000000/0x100000`, UFS stream `0x60` | DT; F1 |
| UFS host | `0x1d84000/0x3000`; ICE `0x1d88000/0x18000`; MCQ SQD `0x1da5000/0x2000`; MCQ VS `0x1da4000/0x10`; SPI 265 | DT; F1 |
| UFS PHY | `qcom,ufs-phy-qmp-v4-niobe`, `0x1d80000/0x2000`, 2 lanes | DT |
| GPU | `qcom,adreno-gpu-gen8-6-0` `0x3d00000`, GMU `0x3d37000`, GPU SMMU `0x3da0000` (no component yet) | DT; migration notes |
| Debug UART | GENI `0xa9c000/0x4000`, SPI 579 (0x243), 115200 8N1; SE7 disabled in stock firmware; pins TLMM GPIO30 TX / GPIO31 RX | F1 `make-luming-adt.py` measured comments; `agents/uart-debug/REPORT-UART.md` |

## 2. CPUs, timer, GIC

| Fact | Value | Source |
| --- | --- | --- |
| CPUs | 8 × `qcom,kryo`, `reg` MPIDR Aff1 = 0x000,0x100,...,0x700 (Aff0 = 0) | DT `/cpus/cpu@*`; F1 |
| PSCI | `enable-method = "psci"`, conduit SMC, timebase 19,200,000 Hz | DT; F1 |
| GIC | `arm,gic-v3`: GICD `0x17100000/0x10000`, GICR `0x17180000/0x200000`, redistributor stride `0x40000` | DT `interrupt-controller@17100000`; migration notes |
| Timer PPIs | `arm,armv8-timer` interrupts `<PPI 13>,<PPI 14>,<PPI 11>,<PPI 12>` | DT `/soc/timer` |
| **Virtual timer INTID** | **27** (= 16 + PPI 11), physical timer 30 (= 16 + PPI 14) | DT; same as the SM8350 star port (ios-sweet #14); NOT sheng's 19 |
| A-line prelinked kernel physBase / markers | physBase ≈ `0x8c01e06a0`; marker channel PA `0x8c4000000` (high-water) | GREP (REPORT-CLEAN*.md, EC-STAGE-TABLE) |

## 3. DRAM window (format-2 ADT requires exactly one contiguous range)

| Fact | Value | Source |
| --- | --- | --- |
| Low bank | `0x80000000..0xffffffff` (2 GiB, many XPU carve-outs) | IOMEM |
| Upper System RAM | `0x880000000..0xaffffefff`, holes at `0x8af8fe000..0x8afffffff`, `0x8b7f00000..0x8b80fffff`, `0x8b9f00000..0x8bffffff` | IOMEM |
| Largest contiguous window | **`0x8c0000000..0xaffffefff` = `0x23ffff000` (8.999996 GiB)** | IOMEM arithmetic |
| Chosen for board.toml | `dts/luming.dts` memory node `0x8c0000000/0x23ffff000`; `payload.dram_size = "0x23ffff000"` | this skeleton |
| Risk | `0x23ffff000` is not 2 MiB aligned; format-2 has no alignment check but XNU pmap may prefer a 2 MiB aligned memSize. If the first build rejects it, use `0x23ff00000` (2 MiB aligned, 8.999 GiB) and update both the DTS and payload.dram_size together. [placeholder: measure DarwinBoot acceptance] | GAP-LIST #8 |

## 4. Storage / root

| Fact | Value | Source |
| --- | --- | --- |
| userdata GPT | first_lba 3124736, last_lba 128619514, lba_bytes 4096 (478.7 GiB) | F1, DT GPT capture |
| Recipe (route 1, chosen) | SHNGROOT manifest windows `OS` + `SystemOS`, root selected by APFS volume UUID, `VerifiedRoot` hooks (sheng working recipe) | SHENG; board.toml [userdata] |
| Root image build | `./unixnu build userdata` from the active profile's IPSW; do not use the retired iOS16 20H392 image | SHENG; Lead direction 2026-10-29 |
| Root volume UUID | `04769D26-2CA0-4825-B443-E2E5F88300F2` (SystemOS volume of the 21H461 image, same value sheng/dada pin) [adapted] | SHENG; DADA |
| Data seed | `DBRDISK1` packed Data seed via `[payload.adt] packed_data_ramdisk` + `--data-ramdisk data.dbr`; `RamBlock` publishes it at `/private/var` | SHENG; DADA |
| Existing luming SHNGROOT image (NOT used now) | `build/ios16-root/luming/userdata/userdata-root.img`, 8,380,219,392 B, sha256 `2c2aca3f...`, SHNGROOT v1 windows OS/SystemOS (iOS16 20H392) | `agents/roots-userspace/route-b/verified-inventory.json` |
| A-line evidence | adopted controller, GPT read, stage-0 snapshot; UFSDxe initialization verified after the platform-FDT fix (AI8 log) | UFSCI |

## 5. Framebuffer / panel (console-first; display service later)

| Fact | Value | Source |
| --- | --- | --- |
| ABL splash / framebuffer | base `0xFC800000`, reserved size `0x2b00000` (44,032 KiB), label `cont_splash_region` | DT `/reserved-memory/splash_region`; DMESG |
| Geometry (A-line/format-1) | stride 4944 B, width 1236, height 2750, 32 bpp | F1; A-line video base logged `0xFC800000` |
| Panel | `qcom,mdss_dsi_o9_42_02_0a_dsc_cmd`, cell `AGY553R049AH3`, DSC command panel | DT `/chosen` bootargs (stock) |
| First-boot plan | XNU text console only: DarwinBoot fills `boot_args.Video[6]` from the UEFI GOP, pexpert draws (dada first boot) | DADA; `docs/A-FIX-CROSSWALK.md` (a)/(b) |

## 6. Boot image / firmware

| Fact | Value | Source |
| --- | --- | --- |
| Stock luming boot.img | Android header **v4**, header_size 1584, pagesize 4096, kernel_offset 0x8000, ramdisk_offset 0x01000000, tags_offset 0x100 | F1; recovery BoardConfig |
| vendor_boot DTB | 966,814 B (stock vendor_boot), live merged DTB 794,887 B | F1; `uefi-luming/PORTING.md` |
| Firmware baseline | local `uefi-luming` build 2026-10-23 (Mu-Silicium 42fe563, onyx-based lumingPkg, stock luming vendor DXE) | `uefi-luming/working-baseline/` |
| Required FD modules | UniXNU, UniXNUDxe, UniXNURamDiskDxe, DarwinBoot, DiskIoDxe, FAT | SHENG/DADA; `firmware/README.md` |
| FD size/base | [missing] not measured for the format-2 path; FD base/size must match the Mu-Silicium config and boot-image assembly | GAP-LIST #7 |

## 7. OS profile / identity (chosen route)

| Fact | Value | Source |
| --- | --- | --- |
| Active profile | `ipados-17.7.11-21H461` (Darwin 23.6.0, xnu-10063.141.1) — proven official profile | SHENG; DADA; Lead direction |
| Alternate (not chosen) | `ios-16.7.16-20H392`, Darwin 22.6.0, xnu-8796.142.1.703.8~1 — no official profile; picasso skeleton is abi_qualified=false | `proposals/profiles/os/ios-16.7.16-20H392/` |
| Identity props | inherited from the OS profile typed `[adt]` tables (iPad7,1 / J120), overridden only where the board needs it | SHENG; DADA |
| AMFI/PMGR | **restored to the proven dada shape**: 27 prelink roots include AppleMobileFileIntegrity + ApplePMGR + sandbox + AppleImage4; `early_security_init` = profile value; trust-cache runtime on; copied `build-luming-platform-power.py` publishes the ApplePMGRNub | DADA `docs/known-values.md` "Trust cache lock"/"PMGR instrument"; clone recipe §2 |
| Trust-cache pin | `7416ca4f...a7323a7` (21H461 bundle of two v2 modules); payload `--trust-cache` input, never stored in the repo | profile `[payload] trust_cache_sha256`; clone recipe §2.2 |
