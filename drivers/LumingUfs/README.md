# LumingUfs

luming's UFS storage driver. Owns the SM8735 host-controller bring-up, the SMMU takeover, the
request queue, GPT/window parsing and the read-only root publication.

This is the board's own driver, derived from dada's SM8750 `DadaUfs` (which in turn forks the
`ShengUfs`/`NativeUfs` component). The fork changes only the board parameters:

- accepted controller names: `qcom,ufshc` and `qcom,sm8735-ufshc` (luming's stock DT uses the bare
  name; the SM8750 name and the SM8550 name are gone).
- GCC clock offsets: SM8735 "tuna" values in `GccUfs.h` (AXI 0x77018, AHB 0x77028, TX0 0x7702c,
  RX0 0x77030, UNIPRO 0x7706c, ICE 0x7707c, AUX 0x770bc, RX1 0x770d8, **AGGRE 0x770f4**; GDSC
  0x77004/0x9e000; sources: stock `gcc-tuna.c`, live DT).
- root partition: GPT entry **`userdata`** (`kRootPartition`), where the SHNGROOT manifest and the
  OS/SystemOS windows live (measured LBAs 3,124,736..128,619,514 at 4096 B).
- SMMU stream `0x60`, apps_smmu `0x15000000`; the driver adopts the firmware-left SMMU mapping
  (see `SmmuTakeover.h`, `docs/UFS.md`).
- PHY `qcom,ufs-phy-qmp-v4-niobe` `0x1d80000/0x2000`: the driver does not program the PHY; it relies
  on the firmware hand-off exactly like dada/sheng.
- optional policy arguments use the `luming-` prefix (`luming-log`, `luming-data-persist`,
  `luming-log-reserve`).
- `NativeUfs`/`NativeUfsBlock` runtime classes and the `Info.plist` bundle ID stay as the upstream
  ABI expects (`org.blu-sharky.NativeUfs`); the source file is `LumingUfs.cpp` because the board
  builders resolve it by name.

Linked into XNU by `unixnu build kernel` through `component:LumingUfs`. See
`docs/UFS.md`, `docs/reference/dada-ufs.md` and
`agents/f2-luming/deep-graft/REPORT-COMPONENT-GRAFT-MAP.md` for the value-by-value graft map.
