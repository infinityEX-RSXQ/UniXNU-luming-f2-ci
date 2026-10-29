# SM8735-VALUES — UFS parameter candidates for `drivers/LumingUfs`

Machine-readable superset of the deep-graft report §3 (`deep-graft/REPORT-COMPONENT-GRAFT-MAP.md`).
Every value the `DadaUfs` fork actually consumes is listed with its SM8735 candidate, evidence and
status. **No invented values:** [measured] = read from luming's stock system/live DT/stock kernel
source; [from-dada] = byte-identical SM8750 value carried over because the register/layout is the
same family; [needs-stock-source] = needs a stock kernel/UEFI/source artifact not yet in the
workspace; [unknown] = not reproduced yet.

Status legend: **BLOCK** = first-boot cannot proceed without it; **STUB** = the driver does not
need it for the first boot (firmware hand-off/polled path), can be stubbed/omitted.

## A. GCC UFS branch registers (9 + GDSC + RCG2) — the only differing offset is AGGRE

Source for SM8735: stock `gcc-tuna.c` (evidence copy
`agents/nativeufs-plan/evidence/gcc-tuna.c`, lines 1459-1491 for `gcc_aggre_ufs_phy_axi_clk`,
whose `halt_reg` is `0x770f4`; `qcom,gcc-tuna.h` for IDs). Live DT aliases confirm GDSC regs:
`gcc_ufs_phy_gdsc = 0x177004` (GCC offset `0x77004`) and
`gcc_ufs_mem_phy_gdsc = 0x19e000` (offset `0x9e000`).

| # | `GccUfs.h` macro | SM8735 (luming "tuna") | SM8750 (dada) | Evidence | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | `GCC_BASE` | `0x100000` | `0x100000` | live DT `qcom,tuna-gcc` | [measured] BLOCK |
| 2 | `GCC_UFS_PHY_GDSCR` | `0x77004` | `0x77004` | live DT alias gdsc@177004 | [measured] BLOCK |
| 3 | `GCC_UFS_MEM_PHY_GDSCR` | `0x9e000` | `0x9e000` | live DT alias gdsc@19e000 | [measured] BLOCK |
| 4 | `GCC_UFS_PHY_AXI_ENABLE` | `0x77018` | `0x77018` | gcc-tuna.c branch list | [measured] BLOCK |
| 5 | `GCC_UFS_PHY_AHB_ENABLE` | `0x77028` | `0x77028` | gcc-tuna.c branch list | [measured] BLOCK |
| 6 | `GCC_UFS_PHY_TX_SYMBOL0_ENABLE` | `0x7702c` | `0x7702c` | gcc-tuna.c branch list | [measured] BLOCK |
| 7 | `GCC_UFS_PHY_RX_SYMBOL0_ENABLE` | `0x77030` | `0x77030` | gcc-tuna.c branch list | [measured] BLOCK |
| 8 | `GCC_UFS_PHY_UNIPRO_CORE_ENABLE` | `0x7706c` | `0x7706c` | gcc-tuna.c branch list | [measured] BLOCK |
| 9 | `GCC_UFS_PHY_ICE_CORE_ENABLE` | `0x7707c` | `0x7707c` | gcc-tuna.c branch list | [measured] BLOCK |
| 10 | `GCC_UFS_PHY_PHY_AUX_ENABLE` | `0x770bc` | `0x770bc` | gcc-tuna.c branch list | [measured] BLOCK |
| 11 | `GCC_UFS_PHY_RX_SYMBOL1_ENABLE` | `0x770d8` | `0x770d8` | gcc-tuna.c branch list | [measured] BLOCK |
| 12 | **`GCC_AGGRE_UFS_PHY_AXI_ENABLE`** | **`0x770f4`** | `0x770f0` | `gcc-tuna.c:1459-1491` (`gcc_aggre_ufs_phy_axi_clk`, halt_reg `0x770f4`, `BRANCH_HALT_VOTED`, `hwcg_bit=1`) | **[measured] BLOCK — fixed in GccUfs.h** |
| 13 | RCG2 `gcc_ufs_phy_axi_clk_src` | `0x77034` | `0x77034` | gcc-tuna.c RCG2 `.cmd_rcgr` | [measured] STUB (driver never reprograms clocks) |
| 14 | RCG2 `gcc_ufs_phy_ice_core_clk_src` | `0x7708c` | `0x7708c` | same | [measured] STUB |
| 15 | RCG2 `gcc_ufs_phy_unipro_core_clk_src` | `0x770a4` | `0x770a4` | same | [measured] STUB |
| 16 | RCG2 `gcc_ufs_phy_phy_aux_clk_src` | `0x770c0` | `0x770c0` | same | [measured] STUB |
| 17 | branch bits | enable `0x1`, halt bit 0, `BRANCH_HALT_VOTED`, `hwcg_bit=1` for AXI/AHB/UNIPRO/ICE/AUX/AGGRE | same | gcc-tuna.c branch defs | [from-dada]/[measured] BLOCK (read path) |

**Verdict:** all nine UFS branch offsets are identical to SM8750 except AGGRE (`0x770f4` vs
`0x770f0`). `GccUfs.h` now carries `0x770f4`; `check-luming.py` re-checks it.

## B. Host / PHY / SMMU / ICE / interrupt / reset / power windows

Source: live DT `backup/analysis/device-live/luming-live/dtb-dump.json`, `/proc/iomem`, dmesg;
stock UEFI platform FDT `agents/nativeufs-plan/evidence/xbl_config-fdt1-dump.txt`.

| # | Parameter used by the fork | SM8735 candidate | Source | Status |
| --- | --- | --- | --- | --- |
| 18 | `UFS_HC_BASE` / `UFS_HC_SIZE` | `0x1d84000` / `0x3000` | live DT `/soc/ufshc@1d84000`, iomem `01d84000-01d86fff ufs_mem` | [measured] **BLOCK** |
| 19 | `kRootPartition[]` | `"userdata"` | measured GPT (first_lba 3124736, last 128619514 @4096) — luming has **no `linux` partition** | [measured] **BLOCK — fixed in LumingUfs.cpp** |
| 20 | accepted compatible strings | `qcom,ufshc`, `qcom,sm8735-ufshc` | live DT `compatible = "qcom,ufshc"` | [measured] **BLOCK — fixed** |
| 21 | SMMU base mapped by takeover | `0x15000000`, map `0xd0000` (live iomem window is `0x15000000-0x150fffff`, 1 MiB) | live DT `apps-smmu@15000000/0x100000`; iomem | [measured] **BLOCK** (map size may safely grow to `0x100000`) |
| 22 | SMMU stream ID | `0x60` | live DT `iommus = <&apps_smmu 0x60 0>`; recommended `NativeUfs` stream | [measured] **BLOCK** |
| 23 | PHY node | `qcom,ufs-phy-qmp-v4-niobe` at `0x1d80000/0x2000`, 2 lanes | live DT `/soc/ufsphy_mem@1d80000` | [measured] **BLOCK** only for attach/DT node; the driver **does not program the PHY** (`[from-dada]` hand-off assumption) |
| 24 | PHY init/tuning tables (qmp v4 niobe) | — | not in local assets; stock PHY driver/PHY firmware not captured | [needs-stock-source] **STUB if firmware leaves the link up**; BLOCK otherwise |
| 25 | ICE window | `0x1d88000/0x18000` | live DT reg/reg-names `ice`; iomem `01d88000-01d9ffff ice` | [measured] STUB (driver does not touch ICE) |
| 26 | MCQ SQD / MCQ VS | `0x1da5000/0x2000`, `0x1da4000/0x10` | live DT reg-names; iomem | [measured] STUB |
| 27 | interrupt | SPI 265 (`<0 0x109 4>`) | live DT | [measured] STUB (driver polled; no IRQ programming) |
| 28 | GCC reset (`resets = <&gcc 0x13>`) | `GCC_UFS_PHY_BCR` reg `0x77000`, id 0x13 | live DT; `qcom,gcc-tuna.h` (`GCC_UFS_PHY_BCR 19`) | [measured] STUB (firmware deasserts) |
| 29 | reset GPIO | `tlmm` GPIO 191, active-low flag 1 | live DT `reset-gpios = <&tlmm 0xbf 1>` | [measured] STUB |
| 30 | ref clock | `RefClock = 0x249f000` (38.4 MHz) | stock UEFI platform FDT `/ufs0@1D80000` (`xbl_config-fdt1-dump.txt`) | [measured] STUB (firmware clocks) |
| 31 | UFS rails | `vcc`, `vccq`, `vccq2`, `vddp-ref-clk`, `vdda-phy`, `vdda-pll`, `vdd-phy-gdsc` (phandles in DT) | live DT `ufshc` supplies; platform FDT `volt_regs` names `ldob12/ldof3/ldob4/ldof1/ldob2` | [measured] names STUB; **rail state at hand-off = [needs-stock-source]** |
| 32 | speed/timeout defaults | `EnableHighSpeed=1`, `NumGears=5`, `NumLanes=2`, `Rate=2`, `FDeviceInitTimeoutUs=0x2625a0`, `UTRDPollTimeoutUs=0x1c9c380`, `FUA_Value=1`, `LinkStartupRetryCount=5`, `BatteryThresholdMv=0xe10` | stock UEFI platform FDT (`/ufs0@1D80000` + children) | [measured] STUB (firmware hand-off) |
| 33 | block size / LUN | UFS LUN0, **4096-byte logical blocks**; GPT LBAs at 4096 B | dmesg (`4096-byte logical blocks`, `sda`/`sde`), GPT capture | [measured] **BLOCK** (root layout arithmetic) |
| 34 | device identity | SKhynix `HN8T271EJKX152`; ICE v4.0.3; MCQ 16 queues / depth 64 (Android's driver) | dmesg 2026-10-22 | [measured] INFO/stub (logs only) |
| 35 | MCQ-vs-legacy mode left by firmware | — | stock UEFI `UFSDxe.efi` has no MCQ strings, suggesting legacy UTRL; not verified on luming | [needs-stock-source] **BLOCK risk** (legacy UTRL takeover vs MCQ mode) |
| 36 | DMA placement rule | driver refuses DMA >4 GiB when CAP bit24 (`0x01000000`) is clear; luming kernel DRAM window starts at `0x8c0000000` (>4 GiB) | `LumingUfs.cpp` `hostBringUp`; A-line/format-1 DMA evidence | [from-dada] **BLOCK risk** — verify during stage-0/1 or grow the DMA window/choose a <4 GiB buffer if CAP bit is clear |
| 37 | UFS device power mode at hand-off | active vs sleep/PowerDown unknown | not captured | [unknown] STUB (driver has SCSI wake path) |
| 38 | ICE config / hwkm | not configured by the driver; firmware-left | n/a | [from-dada] STUB |
| 39 | policy args | `luming-log`, `luming-data-persist`, `luming-log-reserve` (renamed; no `dada-` args) | `LumingUfs.cpp` data-store helpers; board kernel_args | [measured from copy] STUB first boot (read-only root) |

## C. What is blocking vs stubbable (first boot)

**Blocking (host fix then stage-0/1 device test):**
1. AGGRE GCC offset `0x770f4` — fixed in `GccUfs.h`; host-checked.
2. `kRootPartition` = `"userdata"` — fixed in `LumingUfs.cpp`; host-checked.
3. accepted compatibles = `qcom,ufshc` / `qcom,sm8735-ufshc` — fixed.
4. Host base/size `0x1d84000/0x3000` — already in source/DT.
5. SMMU base `0x15000000` + stream `0x60` — already; verify bank geometry on hardware stage-0.
6. GPT/userdata geometry/4096-byte block size — board values host-checked.
7. DMA<4GiB/CAP-bit24 rule vs luming's high DRAM window — host-check the CAP bit at stage-0; may
   require a below-4GiB DMA buffer or a different allocation strategy.

**Assumed by the proven route but firmware-dependent (verify in stage-0 first):**
- PHY/link left enabled by firmware (`qcom,ufs-phy-qmp-v4-niobe` hand-off; driver does not program
  the PHY). If the firmware brought the link down, the qmp-v4 niobe init tables are
  **[needs-stock-source]** and become a multi-day blocker.
- Legacy UTRL left by firmware (MCQ disabled) — [needs-stock-source], stage-0 will read the host
  config registers.
- ICE/MCQ/reset/interrupt/rails/clocks — not touched by the driver, firmware hand-off assumed; all
  values above are recorded for stage-0 readback and for a future full-init path.

**Can be stubbed today:** items marked STUB in the tables (RCG2, ICE/MCQ windows, IRQ, reset BCR,
reset GPIO, rails, speed/timeout defaults, device identity strings, power-mode wake, ICE config,
policy args). They belong to a full-init/PHY path, not the adopted-controller route.

## D. Evidence sources

- `agents/nativeufs-plan/evidence/{gcc-tuna.c, qcom,gcc-tuna.h, xbl_config-fdt1-dump.txt}`
- `agents/nativeufs-plan/REPORT-UFS-PLAN.md` (UFS/GCC/SMMU analysis and offsets)
- `agents/ufs-ci/REPORT-UFS-CI.md`, `agents/ufs-ci/STATUS.md` (AI7 platform-FDT/UFSDxe log, stage-0)
- `agents/ufs-ci/REPORT-CLEAN*.md` (A-line stage-0 markers, DMA/DRAM constraints)
- `backup/analysis/device-live/luming-live/{dtb-dump.json,iomem.txt,dmesg.txt}`
- `agents/official-crawl/recipe/cache/dada-full/{board.toml,docs/ufs-dada.md,scripts/build-*}` (fork lineage)
- `agents/f2-luming/deep-graft/REPORT-COMPONENT-GRAFT-MAP.md` (§3 UFS graft detail)


## E. Stock-source verification (onyx-v-oss, 2026-10-29)

Sources now available under `agents/luming-stock-kernel/sources/`:
`MiCode_Xiaomi_Kernel_OpenSource-onyx-v-oss/drivers/{clk/qcom/gcc-tuna.c, ufs/host/ufs-qcom.c,
 phy/qualcomm/phy-qcom-ufs-qmp-v4-niobe.c,.h}` and the LineageOS-23.2 devicetrees
(`...-devicetrees-lineage-23.2/qcom/{tuna.dtsi,tuna-gdsc.dtsi,...}`).

| Value | Stock-source result | Status change |
| --- | --- | --- |
| AGGRE UFS branch | `gcc-tuna.c:1459-1491`: `halt_reg/hwcg_reg/enable_reg = 0x770f4` | **CONFIRMED [stock-source]** (was [measured] from the same file via evidence copy) |
| Other 8 branch offsets | `gcc-tuna.c:2630-2844`: AHB 0x77028, AXI 0x77018, ICE 0x7707c, AUX 0x770bc, RX0 0x77030, RX1 0x770d8, TX0 0x7702c, UNIPRO 0x7706c | **CONFIRMED [stock-source]**, identical to SM8750 |
| RCG2 commands | `gcc-tuna.c:1204/1238/1270/1293`: AXI 0x77034, ICE 0x7708c, AUX 0x770c0, UNIPRO 0x770a4 | **CONFIRMED [stock-source]**, identical to SM8750 |
| UFS GDSC | `tuna-gdsc.dtsi`: `gcc_ufs_mem_phy_gdsc` at `0x19e000`; live-DT alias `gcc_ufs_phy_gdsc` at `0x177004` -> GCC offsets 0x9e000 / 0x77004 | **CONFIRMED** (live DT + stock DTS); GDSC definitions are DTS-only in gcc-tuna (no C table) |
| Controller compatible | `ufs-qcom.c:6437-6441` of_match is only `{ "qcom,ufshc" }`; stock UFS node uses `qcom,ufshc` | **CONFIRMED**: keep `qcom,ufshc`; the extra `qcom,sm8735-ufshc` in the accepted list is harmless, stock uses bare name |
| UFS DTS node | Lineage `ufshc@1d84000`: reg 4 ranges (mem 0x3000 / ice 0x18000 / mcq_sqd 0x2000 / mcq_vs 0x10), SPI 265 level-high, lanes 2, `qcom,ice-use-hwkm`, masks, 9 clocks + freq-table | **CONFIRMED** for reg/irq/lanes; **deltas** vs our DTS listed below |
| PHY v4-niobe tables | **source exists**: `drivers/phy/qualcomm/phy-qcom-ufs-qmp-v4-niobe.c` + `.h` (and the Lineage copy) | **UPGRADED: [needs-stock-source] -> [stock-source available]**; only needed if the firmware link is down or a full PHY-init path is written. The adopted-controller route still does not program the PHY. |
| ICE | `qcom,ice-use-hwkm` in stock DT; live dmesg ICE v4.0.3; `ufs-qcom.c` uses `of_qcom_ice_get`; driver still does not touch ICE | ICE windows/policy [measured]; ICE register programming remains **STUB** (firmware hand-off) |
| Reset BCR / reset GPIO | live DT `resets=<&gcc 0x13>`, `reset-gpios=<&tlmm 0xbf 1>`; `gcc-tuna.h` has `GCC_UFS_PHY_BCR 19` | **CONFIRMED** (measured); not programmed by driver -> STUB |
| Rails / IRQ / ref clock / speed params | live DT supplies + stock platform FDT (`RefClock=0x249f000` = 38.4 MHz, HS G5 2 lanes rate 2, timeouts, FUA, LinkStartupRetryCount); IRQ SPI 265 | **CONFIRMED** from live DT/stock FDT; STUB (firmware hand-off) |
| MCQ-vs-legacy mode at hand-off | not derivable from sources: the stock Linux driver enables MCQ, but the UEFI path uses legacy UTRL; needs a device stage-0 register read | **still [unknown] BLOCK risk** (unchanged) |
| DMA<4 GiB / CAP bit24 vs DRAM 0x8c0000000 | driver rule unchanged; luming DRAM window above 4 GiB | **still BLOCK risk** (unchanged; verify at stage-0/1) |

### DTS deltas vs LineageOS onyx `tuna.dtsi`/`tuna-gdsc.dtsi`

Stock `ufshc@1d84000` carries properties our format-2 DTS intentionally omits because the common ADT
converter has no binding for them; they are documented here instead of being invented:

| Stock DTS property | Our DTS | Why / action |
| --- | --- | --- |
| `phys = <&ufsphy_mem>; phy-names = "ufsphy"` | omitted | converter reference/string binding not validated; the driver uses the adt-named `ufsphy` node (already exported) |
| `#reset-cells = <1>` | added now | safe u32 cell |
| `qcom,ice-use-hwkm`, `qcom,prime-mask`, `qcom,silver-mask`, `qcom,cluster-mask`, `qcom,esi-affinity-mask` | omitted | ICE/policy not programmed by the driver; record for the future ICE component |
| clocks/clocks-names (9) + `freq-table-hz` | omitted (documented) | GCC provider disabled in our DTS; driver uses GCC constants. Re-add when a GCC clock component exists |
| `interconnects`/`interconnect-names` | omitted | no interconnect component in format 2 yet |
| GDSC nodes (`gcc_ufs_mem_phy_gdsc@19e000`, `gcc_ufs_phy_gdsc@177004`) | omitted as separate nodes; documented in KNOWN-VALUES | no GDSC binding; driver reads the raw GCC registers |
| `status` on UFS/PHY | `okay` in luming.dts, exported via `unixnu,adt-name` | matches stock enabled state |
| GIC `redistributor-stride` 0x40000, GICD/GICR windows | match | no delta |

