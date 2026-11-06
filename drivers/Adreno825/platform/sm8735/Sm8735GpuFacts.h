/* SPDX-License-Identifier: MIT */
#ifndef SM8735_GPU_FACTS_H
#define SM8735_GPU_FACTS_H

/*
 * SM8735 (luming) GPU facts extracted from the stock vendor_boot device tree
 * (work/vendor_boot.dtb, nodes /soc/qcom,kgsl-3d0@3d00000 and /soc/qcom,gmu@3d37000).
 *
 * Values marked [measured] come from that DTB. Everything still unknown for the
 * Adreno825 driver is marked [missing] and must not be filled with A830/SM8750
 * values.
 */

/* [measured] /soc/qcom,kgsl-3d0@3d00000: reg-names order. */
#define SM8735_GPU_PHYS            0x03d00000ull
#define SM8735_GPU_BYTES           0x00040000ull
#define SM8735_RSCC_PHYS           0x03d50000ull
#define SM8735_RSCC_BYTES          0x00010000ull
#define SM8735_CX_DBGC_PHYS        0x03d61000ull
#define SM8735_CX_DBGC_BYTES       0x00003000ull
#define SM8735_CX_MISC_PHYS        0x03d9e000ull
#define SM8735_CX_MISC_BYTES       0x00002000ull

/* [measured] /soc/qcom,gmu@3d37000. */
#define SM8735_GMU_PHYS            0x03d37000ull
/* [missing] gmu_ao window: not exposed in the stock DTB; must be measured before S3. */

/* [measured] interrupts. */
#define SM8735_IRQ_GPU             300u   /* kgsl_3d0_irq */
#define SM8735_IRQ_CX_HOST         80u    /* cx_host_irq */
#define SM8735_IRQ_HFI             304u   /* gmu hfi */
#define SM8735_IRQ_GMU             305u   /* gmu gmu */

/* [measured] GPU SMMU (kgsl-smmu@3da0000). */
#define SM8735_GPU_SMMU_PHYS       0x03da0000ull
#define SM8735_GPU_SMMU_BYTES      0x00040000ull
#define SM8735_GPU_SMMU_GLOBAL_IRQ 673u
#define SM8735_GPU_SMMU_CB_IRQ0    677u
#define SM8735_GPU_SMMU_CB_IRQ1    678u
#define SM8735_GPU_SMMU_CB_IRQ2    679u
#define SM8735_GPU_SMMU_CB_IRQ3    680u
#define SM8735_GPU_SMMU_CB_IRQ4    681u
#define SM8735_GPU_SMMU_CB_IRQ5    682u
#define SM8735_GPU_SMMU_CB_IRQ6    683u

/* [measured] GMU IOM SID from iommus = <0x30 0x5 0x0>. */
#define SM8735_SID_GMU             5u
/* [missing] GPU and LPAC SIDs/slots/CB assignments: not in the stock GPU node. */

/* [measured] qcom,gmu-freq-table: {kHz, level} pairs. */
#define SM8735_GMU_KHZ0            500000u
#define SM8735_GMU_VLVL0           0x40u
#define SM8735_GMU_KHZ1            650000u
#define SM8735_GMU_VLVL1           0x80u

/* [measured] GPU model string and Gen8-6-0 compatible. */
#define SM8735_GPU_MODEL           "Adreno825"

/* [adapted] Vulkan deviceID reported for Adreno 825 is 0x44030000
 * (vulkan.gpuinfo.org report 43087). This is the best current candidate for the
 * KGSL/GPU chip id; it must be confirmed by reading GPU_ID after S1/S2.
 * Do not use the A830 0x44050001 here. */
#define SM8735_GPU_CHIP_ID_CANDIDATE 0x44030000u
#define SM8735_GPU_CHIP_ID_MISSING 1

#endif /* SM8735_GPU_FACTS_H */
