/* SPDX-License-Identifier: MIT */
#include "Adreno825BoardDefaults.h"

#include "platform/sm8735/Sm8735GpuBoardFacts.h"
#include "platform/sm8735/Sm8735GpuFacts.h"
#include "platform/sm8735/Sm8735GpuPwrLevels.h"

extern "C" const uint8_t native_adreno_firmware_image[];
extern "C" const uint64_t native_adreno_firmware_image_size;
extern "C" const uint8_t native_adreno_sqe_firmware_image[];
extern "C" const uint64_t native_adreno_sqe_firmware_image_size;
extern "C" const uint8_t native_adreno_aqe_firmware_image[];
extern "C" const uint64_t native_adreno_aqe_firmware_image_size;
extern "C" const uint8_t native_adreno_zap_image[];
extern "C" const uint64_t native_adreno_zap_image_size;

namespace {

Adreno830Firmware firmware(const uint8_t *bytes, uint64_t length, const uint8_t (&pin)[32])
{
    Adreno830Firmware f = {bytes, length, {}};
    for (unsigned i = 0; i < 32; ++i) {
        f.sha256[i] = pin[i];
    }
    return f;
}

/* [measured] stock vendor/firmware hashes; the ZAP file is absent on luming. */
const uint8_t gmuPin[32] = {
    0x75,0xb3,0x28,0x2a,0x40,0xe5,0x41,0x1a,0x1c,0x15,0x4f,0x69,0x8b,0x92,0x3a,0x91,
    0x6d,0x1a,0x6c,0x83,0x36,0xd0,0xad,0xa6,0x77,0xfe,0xab,0xb1,0x51,0x55,0xa8,0x0e,
};
const uint8_t sqePin[32] = {
    0x9c,0x8f,0x00,0x9b,0xea,0x11,0x2d,0x7c,0x06,0xdd,0x2c,0xcb,0x67,0xe8,0x89,0x99,
    0x94,0x59,0xe5,0x3b,0x92,0xf0,0xf4,0x85,0x9f,0x5e,0xa0,0xdb,0x06,0x7a,0xd6,0xb5,
};
const uint8_t aqePin[32] = {
    0xf0,0x4c,0xb9,0x7e,0x1e,0x62,0x9b,0x90,0x03,0xa2,0x6c,0x56,0x70,0xb8,0xf7,0xe5,
    0xb7,0xbf,0xec,0xa9,0x5d,0x35,0xb2,0xab,0xd5,0x81,0xfd,0x86,0x72,0xef,0xed,0x20,
};
const uint8_t zapPin[32] = {};

} // namespace

void Adreno825BoardFill(Adreno830Board *b)
{
    if (!b) {
        return;
    }
    *b = Adreno830Board{};

    b->magic = Adreno830BoardMagic;
    b->version = Adreno830BoardVersion;

    b->gpu = {SM8735_GPU_PHYS, SM8735_GPU_BYTES};
    b->rscc = {SM8735_RSCC_PHYS, SM8735_RSCC_BYTES};
    b->cx_dbgc = {SM8735_CX_DBGC_PHYS, SM8735_CX_DBGC_BYTES};
    b->cx_misc = {SM8735_CX_MISC_PHYS, SM8735_CX_MISC_BYTES};
    b->gmu = {SM8735_GPU_GMU_PHYS, SM8735_GPU_GMU_BYTES};
    b->gmu_ao = {SM8735_GPU_GMU_AO_PHYS, SM8735_GPU_GMU_AO_BYTES};
    b->gpucc = {SM8735_GPUCC_PHYS, SM8735_GPUCC_BYTES};
    b->gcc = {SM8735_GCC_PHYS, 0x1f4200ull};
    b->smmu = {SM8735_GPU_SMMU_PHYS, SM8735_GPU_SMMU_BYTES};
    b->cmd_db = {SM8735_CMD_DB_PHYS, SM8735_CMD_DB_BYTES};
    b->smem = {SM8735_SMEM_PHYS, SM8735_SMEM_BYTES};
    b->zap = {SM8735_GPU_ZAP_PHYS, SM8735_GPU_ZAP_BYTES};
    b->qfprom = {0x221c8000ull, 0x1000ull};

    b->chip_id = SM8735_GPU_CHIP_ID;
    b->soc_id = SM8735_SOC_ID;

    b->irq_gpu = SM8735_GPU_IRQ_GPU;
    b->irq_cx_host = SM8735_GPU_IRQ_CX_HOST;
    b->irq_hfi = SM8735_GPU_IRQ_HFI;
    b->irq_gmu = SM8735_GPU_IRQ_GMU;
    b->irq_smmu_global = SM8735_GPU_SMMU_IRQ_GLOBAL;
    b->irq_smmu_cb[0] = SM8735_GPU_SMMU_IRQ_CB0;
    b->irq_smmu_cb[1] = SM8735_GPU_SMMU_IRQ_CB1;
    b->irq_smmu_cb[2] = SM8735_GPU_SMMU_IRQ_CB2;
    b->irq_smmu_cb[3] = SM8735_GPU_SMMU_IRQ_CB3;
    b->irq_scm_waitq = SM8735_GPU_IRQ_SCM_WAITQ;

    b->sid_gpu = SM8735_GPU_SID_GPU;
    b->sid_lpac = SM8735_GPU_SID_LPAC;
    b->sid_gmu = SM8735_GPU_SID_GMU;
    b->slot_gpu = SM8735_GPU_SLOT_GPU;
    b->slot_lpac = SM8735_GPU_SLOT_LPAC;
    b->slot_gmu = SM8735_GPU_SLOT_GMU;
    b->cb_gpu = SM8735_GPU_CB_GPU;
    b->cb_gmu = SM8735_GPU_CB_GMU;
    b->smmu_actlr = SM8735_GPU_SMMU_ACTLR;

    b->pool_mib = 512;
    b->qfprom_speedbin_offset = SM8735_GPU_QFPROM_SPEEDBIN_OFFSET;
    b->speedbin_bits = SM8735_GPU_SPEEDBIN_BITS;

    for (unsigned i = 0; i < SM8735_GPU_BIN_COUNT; ++i) {
        b->levels[i] = sm8735_gpu_bins[i].levels;
        b->level_count[i] = sm8735_gpu_bins[i].count;
        b->initial_level[i] = sm8735_gpu_bins[i].initial;
        b->bin_speed[i] = sm8735_gpu_bins[i].speed;
        b->bin_sku_count[i] = 0;
    }
    b->common_level_count = SM8735_GPU_COMMON_LEVEL_COUNT;

    b->ddr_kbps = sm8735_gpu_ddr_kbps;
    b->ddr_levels = SM8735_GPU_DDR_KBPS_COUNT;
    b->cnoc_levels[0] = sm8735_gpu_cnoc_levels[0];
    b->cnoc_levels[1] = sm8735_gpu_cnoc_levels[1];
    b->gmu_khz[0] = sm8735_gpu_gmu_khz[0];
    b->gmu_khz[1] = sm8735_gpu_gmu_khz[1];
    b->gmu_vlvl[0] = sm8735_gpu_gmu_vlvl[0];
    b->gmu_vlvl[1] = sm8735_gpu_gmu_vlvl[1];

    b->ubwc_mode = 5;
    b->highest_bank_bit = SM8735_GPU_HIGHEST_BANK_BIT;
    b->min_access_length = 32;

    b->gmu_fw = firmware(native_adreno_firmware_image, native_adreno_firmware_image_size, gmuPin);
    b->sqe_fw = firmware(native_adreno_sqe_firmware_image, native_adreno_sqe_firmware_image_size, sqePin);
    b->aqe_fw = firmware(native_adreno_aqe_firmware_image, native_adreno_aqe_firmware_image_size, aqePin);
    b->zap_fw = firmware(native_adreno_zap_image, native_adreno_zap_image_size, zapPin);

    b->flags = 0;
}
