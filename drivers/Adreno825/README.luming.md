# Adreno825 staging source

This directory is the work-in-progress Adreno 825 (SM8735, `qcom,adreno-gpu-gen8-6-0`)
driver for luming. The source is staged from the working Adreno830 (SM8750) driver and
is not yet selected by `board.toml`; it must not affect the current boot until the SM8735
platform layer and board glue are complete.

## Facts

- GPU model: `Adreno825`
- GPU base: `0x3d00000`, GMU: `0x3d37000`, GPU SMMU: `0x3da0000`
- GPU IRQ: 300, CX host IRQ: 80, GMU IRQ: 304/305
- A825 GMU firmware: `gen80600_gmu.bin` (88,964 B)
- Shared SQE/AQE: `gen80000_sqe.fw`, `gen80000_aqe.fw`
- Stock luming vendor has no gen8 ZAP; A830 uses `gen80000_zap.mbn` on the OnePlus 13T
- A830 chip id: `0x44050001`; A825 chip id still needs a hardware read or a stock KGSL log

## TODO (in order)

1. Rename/parameterize the board interface (`Adreno830Board` -> `Adreno825Board`) without
   touching `NativeAdrenoABI.h`.
2. Add the SM8735 platform layer (GPUCC/CX/GX power, RPMh, SCM) — the SM8750 platform
   sources are not reusable as-is.
3. Add the luming board glue with the DTB facts, A825 firmware and a default-off master
   switch.
4. Port `scripts/build-adreno830.py` to an A825 archive recipe and list the component in
   the CI-only catalog.
5. Only then add `Adreno825` to `board.toml` and start with a stage trace (S0-S2).

Until step 5 is complete this directory is inert; it is source staging only.
