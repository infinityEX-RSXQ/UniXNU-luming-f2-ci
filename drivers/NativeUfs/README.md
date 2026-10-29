# drivers/NativeUfs — [missing] luming SM8735 UFS transport component

This directory is intentionally empty except for this note: the luming UFS driver is **not** a
format-2 component yet. `board.toml` selects `ShengUfs` (official catalog, legacy name
`NativeUfs`) as the placeholder transport and pins
`CONFIG_XNU_NATIVE_UFS_ARCHIVE="{tree}/build/luming-ufs/libLumingUfs.a"` ([placeholder]).

## What exists in the workspace

| Artifact | Path | State |
| --- | --- | --- |
| SM8735 probe/GCC/stage-0 driver patches | `agents/nativeufs-fix/patches/0001-nativeufs-sm8735-probe-gcc.patch`, `0002-nativeufs-stage0-snapshot.patch` | reviewed, compiled by CI into the prelinked kernel; not a component |
| Stage-0 diagnostics plan / SMMU/GCC facts | `agents/nativeufs-plan/REPORT-UFS-PLAN.md` | analysis only |
| UFS root bring-up surface | `agents/ufs-ci/REPORT-UFS-CI.md`, `agents/ufs-ci/STATUS.md` | prelinked J2 artifacts; controller state/handoff still being validated |
| Format-1 bindings builder | `UniXNU-luming/scripts/build-native-ufs-bindings.py`, `scripts/native-ufs-bindings.S` | format-1 script |
| Board facts | `docs/UFS.md`, `soc/dts/sm8735.dtsi` (`ufshc`, `ufsphy`) | adapted here |

## Format-2 port outline (from dada's proven `DadaUfs` route)

1. Fork `ShengUfs` sources (catalog `ShengUfs`, repository `UniXNU/ShengUfs`, class `NativeUfs`)
   into `drivers/LumingUfs`; keep filenames/classes/bundle IDs.
2. Replace the SM8550 constants with the SM8735 values: compatible match `qcom,ufshc` +
   SoC-qualified names; GCC `tuna` branch offsets (AXI 0x77018, AHB 0x77028, TX0 0x7702c,
   RX0 0x77030, UNIPRO 0x7706c, ICE 0x7707c, AUX 0x770bc, RX1 0x770d8, AGGRE 0x770f4); host
   0x1d84000/0x3000, ICE 0x1d88000/0x18000, MCQs 0x1da5000/0x1da4000; PHY 0x1d80000
   (`qcom,ufs-phy-qmp-v4-niobe`); apps-SMMU stream 0x60; GPT partition `userdata` (measured LBAs
   in board.toml).
3. Add the storage-class/kext-binding archive steps copied from dada
   (`build-storage-classes.py`, `build-storage-kext-bindings.py --component LumingUfs`) and the
   `CONFIG_XNU_NATIVE_UFS_ARCHIVE` override.
4. Add the catalog entry (`components.toml`, `kind/path/repository/revision/build/outputs`) and a
   `feeds.toml`/`.gitmodules` pin, then select `LumingUfs` in board.toml.
5. Hardware acceptance is the same as `agents/ufs-ci` stage 0/1: controller adopted, GPT read,
   SHNGROOT windows published, root UUID matches `04769D26-2CA0-4825-B443-E2E5F88300F2`.

[placeholder] Do not add the prelinked NativeUfs binary here; format 2 builds the transport from
source through the archive plan.
