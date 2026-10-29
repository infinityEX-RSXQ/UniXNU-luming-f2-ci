# REFERENCE-SOURCES — where every [adapted] file came from

This skeleton was built offline on 2026-10-29 from local, read-only references. Reproduce the
copies with `python agents/f2-luming/tools/adapt-references.py`; the script records each copy in
its output. Original files are never modified.

## Copied/adapted files

| Skeleton path | Reference path | Status | Notes |
| --- | --- | --- | --- |
| `.gitignore`, `.gitattributes`, `LICENSE` | `unixnu-format2/UniXNU-sheng/` | copied | sheng format-2 scaffolding |
| `configs/arch/common.config` | `unixnu-format2/UniXNU/profiles/arch/arm64/configs/common.config` | copied | reference copy; official owner is UniXNU |
| `configs/os/ipados-17.7.11-21H461.config` | `unixnu-format2/UniXNU/profiles/os/ipados-17.7.11-21H461/configs/ipados.config` | copied | reference copy |
| `patches/xnu/arch/series`, `patches/xnu/os/series` | `unixnu-format2/UniXNU/profiles/.../patches/xnu/series` | copied | reference copies; board.toml uses the official prefixes |
| `soc/soc.toml`, `soc/README.md`, `soc/AGENTS.md`, `soc/LICENSE`, `soc/.gitignore` | `unixnu-format2/UniXNU-sm8735-common/` | copied | local SM8735 scaffold ("not validated") |
| `soc/configs/sm8735.config` | `unixnu-format2/UniXNU-sm8735-common/configs/sm8735.config` | edited | ADRENO off (no matching component) |
| `soc/patches/xnu/native-smp-secondary.patch` | `unixnu-format2/UniXNU-sm8735-common/patches/xnu/` | copied | SM8735/8-CPU SMP patch |
| `soc/patches/xnu/sheng-platform-power.patch` | same | copied, inactive | SM8550/sheng board code; kept as reference |
| `soc/patches/xnu/series` | same | edited | only `native-smp-secondary.patch` active |
| `soc/dts/sm8735.dtsi` | derived from `UniXNU-sm8735-common/dts/sm8735.dtsi` | **rewritten** | measured GIC/timer/UFS/PHY/UART/GPU facts + source comments; original kept at `soc/dts/sm8735.dtsi.scaffold` |
| `dts/luming.dts` | structure from `UniXNU-sheng/dts/sheng.dts` | **rewritten** | luming memory/splash/HTML hardware, measured facts |
| `package/unixnu.toml`, `package/LumingKit/Kit.toml`, `package/README.md` | `UniXNU-luming/package/` | copied | format-1 board package; re-derive for format 2 (gap #11) |
| `scripts/reference/check-luming-format1.py` | `UniXNU-luming/scripts/check-luming.py` | copied | format-1 preflight reference only |
| `docs/reference/luming-format1_defconfig` | `UniXNU-luming/configs/luming_defconfig` | copied | format-1 kernel settings reference |
| `docs/reference/dada-board.toml`, `docs/reference/dada-known-values.md`, `docs/reference/dada-ufs.md` | `agents/official-crawl/recipe/cache/dada-full/` | copied | dada (SM8750) format-2 reference: board shape, no-AMFI rationale, UFS facts |
| `firmware/patches/*.patch` | `agents/official-crawl/recipe/cache/dada-full/docs/patches/` | copied | Mu-Silicium + UniXNU patches from the proven dada route |
| `patches/unixnu/*.patch` | same | copied | UniXNU-side header v4 / owner-cache patches |
| `proposals/profiles/os/ios-16.7.16-20H392/*` | `agents/official-crawl/cache/repos/picasso-suzukir1n/` | copied | public iOS16 profile skeleton (`abi_qualified=false`); NOT the active profile |
| `ci/unixnu-macos-reference.yml` | `unixnu-format2/UniXNU/.github/workflows/macos.yml` | copied | unmodified upstream reference for the adapted workflow |
| `docs/reference/unixnu-example.toml` | `unixnu-format2/UniXNU/unixnu.example.toml` | copied | local build-input reference |

## Written from the measured luming facts (no reference file)

| File | Fact sources |
| --- | --- |
| `board.toml` | dada/sheng formats, luming measured values (`docs/reference/...`, `UniXNU-luming/board.toml`, live DT/iomem); see comments per field |
| `configs/luming_defconfig` | dada defconfig shape + luming decisions |
| `feeds.toml`, `unixnu.lock`, `local.toml.example` | sheng/dada format-2 shape + the local `soc/` feed |
| `firmware/README.md`, `docs/FIRMWARE` references | sheng/dada firmware integration + local `uefi-luming` inventory |
| `docs/*.md`, `README.md`, `AGENTS.md`, `porting.toml` | this analysis; every claim points at an evidence path |

## Evidence pointers used throughout

- `backup/analysis/device-live/luming-live/{dtb-dump.json,iomem.txt,dmesg.txt}` — stock live capture.
- `docs/reference/dada-known-values.md` — dada's measured values and no-AMFI rationale.
- `agents/ufs-ci/REPORT-CLEAN*.md`, `BOOT-SEQUENCE.md`, `EC-STAGE-TABLE.md` — A-line fixes/findings.
- `agents/nativeufs-plan/REPORT-UFS-PLAN.md`, `agents/ufs-ci/REPORT-UFS-CI.md` — UFS facts.
- `uefi-luming/` — local Mu-Silicium luming firmware tree (read-only for this skeleton).
- `agents/official-crawl/REPORT-OFFICIAL-PATH.md` — official format-2 device matrix and gaps.
