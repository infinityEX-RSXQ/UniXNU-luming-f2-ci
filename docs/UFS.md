# UFS / storage plan — luming (SM8735) in format 2

The first-boot storage goal is the sheng route: adopt the UFS controller the firmware left running,
publish the `userdata` SHNGROOT windows (OS + SystemOS), mount the root APFS volume by UUID, and
publish the DBRDISK1 Data seed at `/private/var`. No UFS writes are needed for the first root mount.

## What this skeleton contains

| Item | File | Status |
| --- | --- | --- |
| `ufshc` node (host, ICE, MCQ windows, SPI 265) | `soc/dts/sm8735.dtsi` | [adapted] measured live-DT values |
| `ufsphy` node (`qcom,ufs-phy-qmp-v4-niobe`) | `soc/dts/sm8735.dtsi` | [adapted] measured |
| userdata GPT geometry | `board.toml` `[userdata]` | [measured] |
| root UUID (SystemOS of the 21H461 image) | `board.toml` `[payload.adt]` | [adapted] same value sheng/dada pin |
| Data seed staging | `board.toml` `[payload.adt] packed_data_ramdisk/persistent_data` | [placeholder] seed file missing |
| storage component selection | `board.toml` `[components] include` = `ShengUfs` | [placeholder] the luming fork is not a component yet |
| defconfig switches | `configs/luming_defconfig` `CONFIG_XNU_NATIVE_UFS*` | [adapted] |
| component work order | `drivers/NativeUfs/README.md` | [missing] |

## Measured facts (source pointers)

- Host: `0x1d84000/0x3000`; ICE `0x1d88000/0x18000`; MCQ SQD `0x1da5000/0x2000`; MCQ VS
  `0x1da4000/0x10`; interrupts `<0 0x109 4>` (SPI 265); `iommus = <&apps_smmu 0x60 0>`.
  Source: live DT `/soc/ufshc@1d84000`; `/proc/iomem` `01d84000-01d86fff ufs_mem`,
  `01d88000-01d9ffff ice`, `01da0000-01da03ff mcq`, `01da5000-01da6fff mcq_sqd`.
- PHY: `/soc/ufsphy_mem@1d80000`, `qcom,ufs-phy-qmp-v4-niobe`, `0x1d80000/0x2000`, 2 lanes,
  ref/aux/qref + rx/tx symbol mux clocks, vdda/vdda-pll/qref/vdd-phy-gdsc supplies.
- GCC `qcom,tuna-gcc` `0x100000/0x1f4200`: UFS branch offsets from `gcc-tuna.c`
  (evidence copy `agents/nativeufs-plan/evidence/gcc-tuna.c`):
  AXI `0x77018`, AHB `0x77028`, TX0 `0x7702c`, RX0 `0x77030`, UNIPRO `0x7706c`, ICE `0x7707c`,
  AUX `0x770bc`, RX1 `0x770d8`, AGGRE `0x770f4`; GDSC `0x77004`/`0x9e000`; reset BCR `0x77000`
  (reset id 0x13); RCG2 cmds `0x77034/0x7708c/0x770a4/0x770c0`.
- Apps SMMU: `qcom,qsmmu-v500` `0x15000000/0x100000`; UFS stream `0x60`.
- GPT/userdata: first_lba 3124736, last_lba 128619514, 4096-byte LBAs (478.7 GiB);
  LUN 0 uses 4096-byte logical blocks.
- Device: SKhynix `HN8T271EJKX152`; Android's own driver uses ICE v4.0.3 and MCQ 16 queues, but
  the UEFI/DarwinBoot route adopts the firmware-left controller (legacy UTRL path).
- Firmware hand-off evidence: after the platform-FDT fix (task-60/UFS-FW), stock luming `UFSDxe`
  initialised UFS; the AI8 QR log contains `Successfully Enabled UFS Cache Coherency` and the
  UFSDxe init lines (`agents/uefi-log/REPORT-AI8.md`, `agents/ufs-ci`).

## A-line experience that the component must port

- The driver matches `qcom,ufshc` (plus SoC-qualified names), adopts the firmware request list,
  takes a stage-0 read-only snapshot (GCC/HC/SMMU) before any DMA, and only then issues a NOP/TUR
  and GPT reads (`agents/nativeufs-fix/patches/0001-0002`, `agents/ufs-ci/REPORT-UFS-CI.md`).
- Do **not** reintroduce the binary workarounds from the prelinked CLEAN series; the format-2
  component is compiled from source (see `docs/A-FIX-CROSSWALK.md` (a)/(c1)).
- SMMU handling: the sheng transport's bypass/planning path works with the measured luming SMMU
  base/window and stream id; keep the stage-0 snapshot and explicit failure reasons
  (`agents/nativeufs-plan/REPORT-UFS-PLAN.md`).
- DMA: the request-list/DMA buffer must be reachable with the controller's address width; the
  A-line used a window inside `0x8c0000000..` (see `docs/KNOWN-VALUES.md` #3). The format-2
  DarwinBoot owned-memory window is `0x10000000` [placeholder] and may need to grow.

## Component shape (from dada's proven DadaUfs, copied into drivers/LumingUfs)

1. `drivers/LumingUfs/` = SM8735 fork of `ShengUfs` (catalog ID `ShengUfs`, legacy name
   `NativeUfs`); keep source filenames/runtime identifiers.
2. Replace SM8550 constants with the SM8735 values above and the `userdata` partition name.
3. Board-owned builders: `build-storage-classes.py` (reference `IOBlockStorageDevice` object) and
   `build-storage-kext-bindings.py --component LumingUfs` (rebind base-class imports to the
   prelinked `com.apple.iokit.IOStorageFamily` addresses) - otherwise `OSMetaClass` panics with a
   duplicate class. Source: dada repo `scripts/` (not cached in this workspace yet).
4. Add the catalog entry + `.gitmodules` pin + `feeds.toml` source; set
   `CONFIG_XNU_NATIVE_UFS_ARCHIVE="{tree}/build/luming-ufs/libLumingUfs.a"`.
5. Root path: publish the SHNGROOT windows and match the root UUID; VerifiedRoot hooks are the
   sheng recipe for the owner-signed root policy (the no-AMFI first boot keeps them off).

## Acceptance (device phase; approval-gated)

1. Stage 0: read-only GCC/HC/SMMU snapshot matches the measured values; HCE/HCS show an adoptable
   controller (firmware-init state).
2. GPT readable; `userdata` window matches `board.toml`; OS/SystemOS windows within it.
3. SCSI READ CAPACITY and known-block reads match the stock image.
4. Root APFS volume UUID `04769D26-2CA0-4825-B443-E2E5F88300F2` mounts; launchd starts.
5. Data seed DBRDISK1 is published by `RamBlock` at `/private/var`; optional persistence works.

No device operations are included in this skeleton; see `docs/FIRST-BUILD-PLAN.md` §4.

## DTS deltas vs LineageOS onyx (stock sources, 2026-10-29)

The stock LineageOS-23.2 `tuna.dtsi` UFS node carries `phys/phy-names`, `#reset-cells`, ICE policy masks, 9 clocks + freq-table, `interconnects` and the GDSC nodes. The format-2 ADT converter has bindings only for the subset in our DTS; the rest are documented in `drivers/LumingUfs/SM8735-VALUES.md` section E instead of being invented. Safe deltas applied: `#reset-cells = <1>` and `lanes-per-direction = <2>` on `ufshc`. Kept out until a component/binding exists: `phys` reference, ICE masks (`qcom,ice-use-hwkm` etc.), clocks/freq-table, interconnect paths, GDSC nodes. Controller reg/IRQ/reg-names and the PHY compatible `qcom,ufs-phy-qmp-v4-niobe` match stock exactly.

