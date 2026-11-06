/* SPDX-License-Identifier: MIT */
#include "Sm8735GpuPower.h"

#include "Sm8735GpuFacts.h"
#include <stddef.h>

enum : uint64_t {
    Sm8735GpuccPll0Mode = SM8735_GPUCC_PHYS + 0x00,
    Sm8735GpuccPll0L = SM8735_GPUCC_PHYS + 0x10,
    Sm8735GpuccPll0Config = SM8735_GPUCC_PHYS + 0x20,
    Sm8735GpuccCxBcr = SM8735_GPUCC_PHYS + 0x907c,
    Sm8735GpuccCxGdscr = SM8735_GPUCC_PHYS + 0x9080,
    Sm8735GpuccCxCfgGdscr = SM8735_GPUCC_PHYS + 0x9084,
    Sm8735GpuccCxGdsHwCtrl = SM8735_GPUCC_PHYS + 0x9094,
    Sm8735GpuccGmuBcr = SM8735_GPUCC_PHYS + 0x9314,
    Sm8735GpuccGmuRcg = SM8735_GPUCC_PHYS + 0x9318,
    Sm8735GpuccHubRcg = SM8735_GPUCC_PHYS + 0x93ec,
};

enum : uint32_t {
    Sm8735GpuPowerPwrOn = 1u << 31,
    Sm8735GpuPowerGdscMask = 0x00fff007u,
    Sm8735GpuPowerGdscOn = 0x00228000u,
    Sm8735GpuPowerRetainFf = 1u << 11,
};

static int rd(const Sm8735GpuPowerIo *io, Sm8735GpuPowerTrace *trace,
    uint64_t phys, uint32_t *value)
{
    if (!io || !io->read32) {
        return -1;
    }
    if (trace) {
        trace->offset = phys;
        trace->reads++;
    }
    if (io->read32(io->cookie, phys, value)) {
        return -1;
    }
    if (trace) {
        trace->value = *value;
    }
    return 0;
}

static int wr(const Sm8735GpuPowerIo *io, Sm8735GpuPowerTrace *trace,
    uint64_t phys, uint32_t value)
{
    if (!io || !io->write32) {
        return -1;
    }
    if (trace) {
        trace->offset = phys;
        trace->value = value;
        trace->writes++;
    }
    return io->write32(io->cookie, phys, value) ? -1 : 0;
}

static int wait_us(const Sm8735GpuPowerIo *io, unsigned us)
{
    if (!io || !io->delay_us) {
        return -1;
    }
    return io->delay_us(io->cookie, us) ? -1 : 0;
}

static int update(const Sm8735GpuPowerIo *io, Sm8735GpuPowerTrace *trace,
    uint64_t phys, uint32_t mask, uint32_t value)
{
    uint32_t old;
    if (rd(io, trace, phys, &old)) {
        return -1;
    }
    if ((old & mask) == value) {
        return 0;
    }
    return wr(io, trace, phys, (old & ~mask) | value);
}

uint32_t Sm8735GpuPowerChooseId(uint32_t id0, uint32_t id4, uint32_t id100)
{
    const uint32_t ids[3] = { id0, id4, id100 };
    for (unsigned i = 0; i < 3; ++i) {
        if (ids[i] != 0 && ids[i] != 0xffffffffu) {
            return ids[i];
        }
    }
    return 0;
}

int Sm8735GpuPowerSurveyRead(const Sm8735GpuPowerIo *io, Sm8735GpuPowerSurvey *out)
{
    if (!out) {
        return -1;
    }
    *out = (Sm8735GpuPowerSurvey){};
    if (rd(io, NULL, Sm8735GpuccPll0Mode, &out->pll0_mode) ||
        rd(io, NULL, Sm8735GpuccPll0L, &out->pll0_l) ||
        rd(io, NULL, Sm8735GpuccPll0Config, &out->pll0_config) ||
        rd(io, NULL, Sm8735GpuccCxBcr, &out->cx_bcr) ||
        rd(io, NULL, Sm8735GpuccCxGdscr, &out->cx_gdscr) ||
        rd(io, NULL, Sm8735GpuccCxCfgGdscr, &out->cx_cfg_gdscr) ||
        rd(io, NULL, Sm8735GpuccCxGdsHwCtrl, &out->cx_gds_hw_ctrl) ||
        rd(io, NULL, Sm8735GpuccGmuBcr, &out->gmu_bcr) ||
        rd(io, NULL, Sm8735GpuccGmuRcg, &out->gmu_rcg) ||
        rd(io, NULL, Sm8735GpuccHubRcg, &out->hub_rcg) ||
        rd(io, NULL, SM8735_GX_CLKCTL_PHYS, &out->gx_clkctl) ||
        rd(io, NULL, SM8735_GPU_PHYS + 0x000, &out->gpu_id0) ||
        rd(io, NULL, SM8735_GPU_PHYS + 0x004, &out->gpu_id4) ||
        rd(io, NULL, SM8735_GPU_PHYS + 0x100, &out->gpu_id100)) {
        *out = (Sm8735GpuPowerSurvey){};
        return -1;
    }
    out->cx_powered = (out->cx_gds_hw_ctrl & Sm8735GpuPowerPwrOn) ? 1u : 0u;
    out->gpu_id_candidate = Sm8735GpuPowerChooseId(out->gpu_id0, out->gpu_id4, out->gpu_id100);
    out->ok = 1;
    return 0;
}

Sm8735GpuPowerStatus Sm8735GpuPowerEnableCxGdsc(const Sm8735GpuPowerIo *io,
    Sm8735GpuPowerTrace *trace)
{
    if (trace) {
        *trace = (Sm8735GpuPowerTrace){};
    }
    if (update(io, trace, Sm8735GpuccCxGdscr, Sm8735GpuPowerGdscMask,
            Sm8735GpuPowerGdscOn)) {
        return Sm8735GpuPowerIoError;
    }
    if (wait_us(io, 1)) {
        return Sm8735GpuPowerIoError;
    }
    for (unsigned spent = 0; spent <= 2000; ++spent) {
        uint32_t value;
        if (rd(io, trace, Sm8735GpuccCxGdsHwCtrl, &value)) {
            return Sm8735GpuPowerIoError;
        }
        if (value & Sm8735GpuPowerPwrOn) {
            if (update(io, trace, Sm8735GpuccCxGdscr,
                    Sm8735GpuPowerRetainFf, Sm8735GpuPowerRetainFf)) {
                return Sm8735GpuPowerIoError;
            }
            return Sm8735GpuPowerOk;
        }
        if (spent == 2000) {
            return Sm8735GpuPowerTimeout;
        }
        if (wait_us(io, 1)) {
            return Sm8735GpuPowerIoError;
        }
    }
    return Sm8735GpuPowerTimeout;
}
