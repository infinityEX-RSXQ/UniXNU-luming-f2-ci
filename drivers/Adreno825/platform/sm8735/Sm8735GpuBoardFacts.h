/* SPDX-License-Identifier: MIT */
#ifndef SM8735_GPU_BOARD_FACTS_H
#define SM8735_GPU_BOARD_FACTS_H

#include <stdint.h>

/*
 * [measured] stock luming vendor_boot.dtb, /soc/qcom,kgsl-3d0@3d00000,
 * /soc/kgsl-smmu@3da0000 and /soc/qcom,gmu@3d37000.
 *
 * Only values that are present in the stock DTB are listed. Values that still
 * have to come from a measured register read are marked [missing]; do not fill
 * them with A830/SM8750 numbers.
 */

/* [measured] DTB root qcom,msm-id = <0x28f 0x10000>; 0x28f is the SMEM socinfo
 * id compared in S0. */
#define SM8735_SOC_ID               0x28fu

#define SM8735_GPU_IRQ_GPU          300u   /* kgsl_3d0_irq */#define SM8735_GPU_IRQ_CX_HOST      80u    /* cx_host_irq */
#define SM8735_GPU_IRQ_HFI          304u   /* GMU hfi */
#define SM8735_GPU_IRQ_GMU          305u   /* GMU gmu */

/* qcom,actlr = <0 0x3ff 0x32b>; the third cell is the ACTLR value. */
#define SM8735_GPU_SMMU_ACTLR       0x32bu

/* [measured] qcom,gmu@3d37000: reg-names "gmu", "gmu_ao_blk_dec0". */
#define SM8735_GPU_GMU_PHYS         0x03d37000ull
#define SM8735_GPU_GMU_BYTES        0x00068000ull
#define SM8735_GPU_GMU_AO_PHYS      0x03d40000ull
#define SM8735_GPU_GMU_AO_BYTES     0x00010000ull

/* [measured] reserved-memory: gpu_microcode_region@94e9a000 is the ZAP carveout
 * (zap-shader memory-region phandle 0x304). There is no zap firmware file in the
 * stock vendor tree. */
#define SM8735_GPU_ZAP_PHYS         0x94e9a000ull
#define SM8735_GPU_ZAP_BYTES        0x00002000ull

/* [measured] reserved-memory/smem_region@81d00000 and aop_cmd_db_region@81c60000. */
#define SM8735_SMEM_PHYS            0x81d00000ull
#define SM8735_SMEM_BYTES           0x00200000ull
#define SM8735_CMD_DB_PHYS          0x81c60000ull
#define SM8735_CMD_DB_BYTES         0x00020000ull

/* [adapted] Gen8 convention, not present in the stock GPU node: GPU SID 0,
 * LPAC SID 1, GMU SID 5 (the GMU SID is [measured] from iommus = <&gpu_smmu 5 0>).
 * Confirm with the SMMU SMR registers or a stock KGSL log before trusting it. */
#define SM8735_GPU_SID_GPU          0u
#define SM8735_GPU_SID_LPAC         1u
#define SM8735_GPU_SID_GMU          5u
#define SM8735_GPU_SLOT_GPU         0u
#define SM8735_GPU_SLOT_LPAC        3u
#define SM8735_GPU_SLOT_GMU         1u
#define SM8735_GPU_CB_GPU           0u
#define SM8735_GPU_CB_GMU           2u

/* [adapted] The driver attaches four SMMU CB interrupts. A825 exposes 11
 * (677..687); the first four are used for bring-up until the actual mapping is
 * measured. */
#define SM8735_GPU_SMMU_CB_USED     4u

/* [missing] SCM waitq IRQ: /firmware/qcom_scm in this DTB has no interrupts
 * property. Keep it 0 (not attached) until a real SPI is measured. */
#define SM8735_GPU_IRQ_SCM_WAITQ    0u

/* SMMU global interrupt plus 11 context-bank interrupts: 677..687. */
#define SM8735_GPU_SMMU_IRQ_GLOBAL  673u
#define SM8735_GPU_SMMU_CB_COUNT    11u
#define SM8735_GPU_SMMU_IRQ_CB0     677u
#define SM8735_GPU_SMMU_IRQ_CB1     678u
#define SM8735_GPU_SMMU_IRQ_CB2     679u
#define SM8735_GPU_SMMU_IRQ_CB3     680u
#define SM8735_GPU_SMMU_IRQ_CB4     681u
#define SM8735_GPU_SMMU_IRQ_CB5     682u
#define SM8735_GPU_SMMU_IRQ_CB6     683u
#define SM8735_GPU_SMMU_IRQ_CB7     684u
#define SM8735_GPU_SMMU_IRQ_CB8     685u
#define SM8735_GPU_SMMU_IRQ_CB9     686u
#define SM8735_GPU_SMMU_IRQ_CB10    687u

/* qcom,bus-table-ddr, 12 entries in kHz. */
#define SM8735_GPU_DDR_KBPS_COUNT   12u
static const uint32_t sm8735_gpu_ddr_kbps[SM8735_GPU_DDR_KBPS_COUNT] = {
    0u, 781250u, 2136718u, 5285156u, 6074218u, 6671875u,
    8171875u, 10687500u, 12449218u, 14398437u, 16500000u, 18597656u,
};

/* qcom,bus-table-cnoc: the stock table has the single 100 level. */
#define SM8735_GPU_CNOC_LEVELS_COUNT 2u
static const uint32_t sm8735_gpu_cnoc_levels[SM8735_GPU_CNOC_LEVELS_COUNT] = {0u, 100u};

/* nvmem gpu_speed_bin@138: reg <0x138 2>, nine bits. */
#define SM8735_GPU_QFPROM_SPEEDBIN_OFFSET 0x138u
#define SM8735_GPU_SPEEDBIN_BITS          9u

/* qcom,gmu-freq-table: {500 MHz, 0x40}, {650 MHz, 0x80}. */
#define SM8735_GPU_GMU_KHZ_COUNT    2u
static const uint32_t sm8735_gpu_gmu_khz[SM8735_GPU_GMU_KHZ_COUNT] = {500000u, 650000u};
static const uint32_t sm8735_gpu_gmu_vlvl[SM8735_GPU_GMU_KHZ_COUNT] = {0x40u, 0x80u};

/* [missing] GPU and LPAC SIDs/slots/CB assignments: the stock GPU node has no
 * iommus property; only the GMU SID 5 is present in its node. Read the SMMU
 * stream-match registers or the stock KGSL log before choosing. */

#endif /* SM8735_GPU_BOARD_FACTS_H */
