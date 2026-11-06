/* SPDX-License-Identifier: MIT */
#include "Sm8735GpuPower.h"
#include "Sm8735GpuFacts.h"

#include <stdio.h>
#include <string.h>

typedef struct Entry {
    uint64_t phys;
    uint32_t value;
} Entry;

typedef struct Fake {
    Entry entries[32];
    unsigned count;
    unsigned writes;
    unsigned reads;
    unsigned fail_at;
} Fake;

static int fake_read(void *cookie, uint64_t phys, uint32_t *value)
{
    Fake *f = (Fake *)cookie;
    ++f->reads;
    if (f->fail_at && f->reads == f->fail_at) {
        return -1;
    }
    for (unsigned i = 0; i < f->count; ++i) {
        if (f->entries[i].phys == phys) {
            *value = f->entries[i].value;
            return 0;
        }
    }
    *value = 0xdeadbeefu;
    return 0;
}

static int fake_write(void *cookie, uint64_t phys, uint32_t value)
{
    (void)phys;
    (void)value;
    ((Fake *)cookie)->writes++;
    return 0;
}

static int fake_delay(void *cookie, unsigned us)
{
    (void)cookie;
    (void)us;
    return 0;
}

static void put(Fake *f, uint64_t phys, uint32_t value)
{
    f->entries[f->count++] = (Entry){ phys, value };
}

int main(void)
{
    Fake f = {0};
    put(&f, SM8735_GPUCC_PHYS + 0x9080, 0x228000u);
    put(&f, SM8735_GPUCC_PHYS + 0x9094, 0x80000000u);
    put(&f, SM8735_GPUCC_PHYS + 0x907c, 0x1u);
    put(&f, SM8735_GPUCC_PHYS + 0x9084, 0x2u);
    put(&f, SM8735_GPUCC_PHYS + 0x00, 0x3u);
    put(&f, SM8735_GPUCC_PHYS + 0x10, 0x4u);
    put(&f, SM8735_GPUCC_PHYS + 0x20, 0x5u);
    put(&f, SM8735_GPUCC_PHYS + 0x9314, 0x6u);
    put(&f, SM8735_GPUCC_PHYS + 0x9318, 0x7u);
    put(&f, SM8735_GPUCC_PHYS + 0x93ec, 0x8u);
    put(&f, SM8735_GX_CLKCTL_PHYS, 0x9u);
    put(&f, SM8735_GPU_PHYS + 0x000, 0u);
    put(&f, SM8735_GPU_PHYS + 0x004, 0x44030000u);
    put(&f, SM8735_GPU_PHYS + 0x100, 0xffffffffu);

    Sm8735GpuPowerIo io = { &f, fake_read, fake_write, fake_delay };
    Sm8735GpuPowerSurvey s = {0};
    if (Sm8735GpuPowerSurveyRead(&io, &s) != 0) {
        printf("survey failed\n");
        return 1;
    }
    if (!s.ok || !s.cx_powered || s.gpu_id_candidate != 0x44030000u) {
        printf("bad survey ok=%u cx=%u id=%08x\n", s.ok, s.cx_powered, s.gpu_id_candidate);
        return 1;
    }
    if (f.writes != 0) {
        printf("survey wrote %u registers\n", f.writes);
        return 1;
    }

    Fake bad = {0};
    bad.fail_at = 1;
    Sm8735GpuPowerSurvey s2 = {0};
    if (Sm8735GpuPowerSurveyRead(&(Sm8735GpuPowerIo){ &bad, fake_read, fake_write, fake_delay }, &s2) == 0 || s2.ok) {
        printf("failure path did not fail\n");
        return 1;
    }

    if (Sm8735GpuPowerChooseId(0, 0x44030000u, 0xffffffffu) != 0x44030000u) {
        printf("id choice wrong\n");
        return 1;
    }

    printf("PASS sm8735 gpu power survey (no writes, id=%08x)\n", s.gpu_id_candidate);
    return 0;
}
