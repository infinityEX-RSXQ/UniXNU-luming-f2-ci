/* SPDX-License-Identifier: MIT */
#include "Sm8735GpuPower.h"

#include "Sm8735GpuFacts.h"

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

enum : uint32_t { Sm8735GpuPowerPwrOn = 1u << 31 };

static int rd(const Sm8735GpuPowerIo *io, uint64_t phys, uint32_t *value)
{
    if (!io || !io->read32) {
        return -1;
    }
    return io->read32(io->cookie, phys, value) ? -1 : 0;
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
    if (rd(io, Sm8735GpuccPll0Mode, &out->pll0_mode) ||
        rd(io, Sm8735GpuccPll0L, &out->pll0_l) ||
        rd(io, Sm8735GpuccPll0Config, &out->pll0_config) ||
        rd(io, Sm8735GpuccCxBcr, &out->cx_bcr) ||
        rd(io, Sm8735GpuccCxGdscr, &out->cx_gdscr) ||
        rd(io, Sm8735GpuccCxCfgGdscr, &out->cx_cfg_gdscr) ||
        rd(io, Sm8735GpuccCxGdsHwCtrl, &out->cx_gds_hw_ctrl) ||
        rd(io, Sm8735GpuccGmuBcr, &out->gmu_bcr) ||
        rd(io, Sm8735GpuccGmuRcg, &out->gmu_rcg) ||
        rd(io, Sm8735GpuccHubRcg, &out->hub_rcg) ||
        rd(io, SM8735_GX_CLKCTL_PHYS, &out->gx_clkctl) ||
        rd(io, SM8735_GPU_PHYS + 0x000, &out->gpu_id0) ||
        rd(io, SM8735_GPU_PHYS + 0x004, &out->gpu_id4) ||
        rd(io, SM8735_GPU_PHYS + 0x100, &out->gpu_id100)) {
        *out = (Sm8735GpuPowerSurvey){};
        return -1;
    }
    out->cx_powered = (out->cx_gds_hw_ctrl & Sm8735GpuPowerPwrOn) ? 1u : 0u;
    out->gpu_id_candidate = Sm8735GpuPowerChooseId(out->gpu_id0, out->gpu_id4, out->gpu_id100);
    out->ok = 1;
    return 0;
}
