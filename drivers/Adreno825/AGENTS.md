# Agent instructions — Adreno825 staging

This directory is the **staging copy** of the Adreno830 (SM8750) driver for the luming
SM8735 / Adreno 825 port. It is inert until `board.toml` selects it.

## Rules

- Do not change `NativeAdrenoABI.h`; AdrenoMetal and the Turnip Darwin backend include it.
- Hardware values must come from `vendor_boot.dtb`, the stock vendor firmware, or a measured
  register read; mark them `[measured]`, `[adapted]` or `[placeholder]` in the porting notes.
- Keep A830 names until the board interface is parameterized; rename as one mechanical change,
  not file-by-file.
- No binary patching, no closed firmware blobs in Git (firmware stays out of the tree).
- The SM8750 `platform/sm8750` layer is reference only; SM8735 needs its own GPUCC/CX/GX
  power and RPMh/SCM layer.
- Build only after `Sm8735*` and the luming board glue exist; a failed archive is not a
  runtime result.

## Source

Imported from `IssacL04/UniXNU-Pagani-Drivers` `drivers/Adreno830` (MIT). The original
README, docs and AGENTS.md content remain for reference; read `README.luming.md` first.
