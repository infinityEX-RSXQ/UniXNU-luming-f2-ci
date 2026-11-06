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
    int power_on_gdsc;
    int pll_lock_on_run;
} Fake;

static Entry *find(Fake *f, uint64_t phys)
{
    for (unsigned i = 0; i < f->count; ++i) {
        if (f->entries[i].phys == phys) {
            return &f->entries[i];
        }
    }
    return NULL;
}

static int fake_read(void *cookie, uint64_t phys, uint32_t *value)
{
    Fake *f = (Fake *)cookie;
    ++f->reads;
    if (f->fail_at && f->reads == f->fail_at) {
        return -1;
    }
    Entry *e = find(f, phys);
    *value = e ? e->value : 0xdeadbeefu;
    return 0;
}

static int fake_write(void *cookie, uint64_t phys, uint32_t value)
{
    Fake *f = (Fake *)cookie;
    ++f->writes;
    Entry *e = find(f, phys);
    if (!e) {
        e = &f->entries[f->count++];
        e->phys = phys;
    }
    e->value = value;
    if (f->pll_lock_on_run && phys == SM8735_GPUCC_PHYS + 0x04 && value == 1u) {
        Entry *m = find(f, SM8735_GPUCC_PHYS + 0x00);
        if (!m) {
            m = &f->entries[f->count++];
            m->phys = SM8735_GPUCC_PHYS + 0x00;
        }
        m->value = 0x80000000u;
    }
    if (f->power_on_gdsc && phys == SM8735_GPUCC_PHYS + 0x9080) {
        Entry *hw = find(f, SM8735_GPUCC_PHYS + 0x9094);
        if (!hw) {
            hw = &f->entries[f->count++];
            hw->phys = SM8735_GPUCC_PHYS + 0x9094;
        }
        hw->value = 0x80000000u;
    }
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
    Entry *e = &f->entries[f->count++];
    e->phys = phys;
    e->value = value;
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

    Fake gdsc = {0};
    gdsc.power_on_gdsc = 1;
    Sm8735GpuPowerIo io2 = { &gdsc, fake_read, fake_write, fake_delay };
    Sm8735GpuPowerTrace trace = {0};
    Sm8735GpuPowerStatus st = Sm8735GpuPowerEnableCxGdsc(&io2, &trace);
    if (st != Sm8735GpuPowerOk) {
        printf("gdsc enable failed st=%d writes=%u\n", (int)st, gdsc.writes);
        return 1;
    }
    if (gdsc.writes < 1) {
        printf("gdsc writes=%u\n", gdsc.writes);
        return 1;
    }

    Fake timeout = {0};
    put(&timeout, SM8735_GPUCC_PHYS + 0x9094, 0u);
    Sm8735GpuPowerIo io3 = { &timeout, fake_read, fake_write, fake_delay };
    if (Sm8735GpuPowerEnableCxGdsc(&io3, NULL) != Sm8735GpuPowerTimeout) {
        printf("timeout path did not time out\n");
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

    Fake pll = {0};
    pll.pll_lock_on_run = 1;
    put(&pll, SM8735_GPUCC_PHYS + 0x00, 0u);
    put(&pll, SM8735_GPUCC_PHYS + 0x04, 0u);
    Sm8735GpuPowerIo io4 = { &pll, fake_read, fake_write, fake_delay };
    if (Sm8735GpuPowerProgramPll(&io4, NULL) != Sm8735GpuPowerOk) {
        printf("pll program failed writes=%u\n", pll.writes);
        return 1;
    }

    Fake running = {0};
    put(&running, SM8735_GPUCC_PHYS + 0x00, 1u);
    Sm8735GpuPowerIo io5 = { &running, fake_read, fake_write, fake_delay };
    if (Sm8735GpuPowerProgramPll(&io5, NULL) != Sm8735GpuPowerUnexpectedState) {
        printf("running pll was not rejected\n");
        return 1;
    }

    Fake nolock = {0};
    put(&nolock, SM8735_GPUCC_PHYS + 0x00, 0u);
    put(&nolock, SM8735_GPUCC_PHYS + 0x04, 0u);
    Sm8735GpuPowerIo io6 = { &nolock, fake_read, fake_write, fake_delay };
    if (Sm8735GpuPowerProgramPll(&io6, NULL) != Sm8735GpuPowerTimeout) {
        printf("pll lock timeout not detected\n");
        return 1;
    }

    Fake s1 = {0};
    s1.pll_lock_on_run = 1;
    s1.power_on_gdsc = 1;
    put(&s1, SM8735_GPUCC_PHYS + 0x00, 0u);
    put(&s1, SM8735_GPUCC_PHYS + 0x04, 0u);
    put(&s1, SM8735_GPUCC_PHYS + 0x9094, 0u);
    put(&s1, SM8735_GPU_PHYS + 0x000, 0u);
    put(&s1, SM8735_GPU_PHYS + 0x004, 0x44030000u);
    put(&s1, SM8735_GPU_PHYS + 0x100, 0xffffffffu);
    Sm8735GpuPowerIo io7 = { &s1, fake_read, fake_write, fake_delay };
    uint32_t id = 0;
    Sm8735GpuPowerStatus s1st = Sm8735GpuPowerOnS1(&io7, NULL, &id);
    if (s1st != Sm8735GpuPowerOk || id != 0x44030000u) {
        printf("s1 failed st=%d id=%08x\n", (int)s1st, id);
        return 1;
    }

    printf("PASS sm8735 gpu power survey + CX GDSC + PLL + S1 (id=%08x)\n", id);
    return 0;
}




