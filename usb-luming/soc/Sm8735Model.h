/* MODEL ONLY. QSCRATCH, IOVA and inherited state are NOT device-qualified. */
/* SPDX-License-Identifier: MIT
 * Kalama GCC + QSMMUv500 + DWC3. Values from the socrates live-DT and pinned
 * SM8550 sources listed in docs/sources-and-evidence.md. Inherited PHY/power only.
 */
#ifndef QUD_SM8735_MODEL_H
#define QUD_SM8735_MODEL_H
#ifndef QUD_SM8735_MODEL_ONLY
#error "SM8735 profile is model-only: DMA handoff and PHY are not qualified"
#endif
#define QUD_SOC_NAME "sm8735-model-not-device-qualified"
/* Development IDs inherited from m1n1, not a new product allocation. */
#define QUD_USB_VID 0x1209u
#define QUD_USB_PID 0x316du
#define QUD_USB_SERIAL "QcomXnuUsbDebug"
#define QUD_USB_PRODUCT "Qualcomm XNU Debug"
#define QUD_GCC_BASE 0x00100000ULL
#define QUD_GCC_BYTES 0x40000u
#define QUD_DWC3_BASE 0x0a600000ULL
#define QUD_DWC3_BYTES 0x100000u
#define QUD_SMMU_BASE 0x15000000ULL
#define QUD_SMMU_BYTES 0x100000ULL
#define QUD_STREAM_ID 0x40u
#define QUD_DMA_IOVA 0x90000000ULL
#define QUD_GCC_CBCR_OFFSETS {0x39018u, 0x39090u, 0x39094u, 0x3902cu, 0x39028u}
#define QUD_GCC_BCR_OFFSET 0x39000u
#define QUD_GCC_GDSCR_OFFSET 0x39004u
#define QUD_GCC_CFG_GDSCR_OFFSET 0x39008u
#define QUD_QSCRATCH_HS_PHY_CTRL_OFFSET 0xf8810u
#define QUD_QSCRATCH_VBUS_MASK (1u << 20)
/* Only set after the board's PSCI SYSTEM_RESET through SMC is qualified. */
#define QUD_PSCI_SMC_RESET 0
#endif
