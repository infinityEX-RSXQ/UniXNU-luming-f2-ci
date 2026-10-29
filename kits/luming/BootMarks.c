/*
 * luming diagnostic boot marks (bring-up only).
 *
 * Paints one solid full-width colour band per boot stage into the framebuffer that DarwinBoot
 * mapped from the UEFI GOP (physical 0xFC800000, 32 bpp, 1236x2750, stride 4944). The stage bands
 * are visible even when the XNU video console has not attached/flushed yet, which distinguishes
 * "kernel died before PE_init_iokit" (partial band) from "console path dead but kernel alive"
 * (all five bands) on the STAGE3/logo screen.
 *
 * This is a clearly-marked diagnostic archive member built into libLumingBootLog.a; it is not a
 * production driver. Remove the boot-marks patch/source for production builds. The framebuffer
 * mapping uses the proper VM API (ml_io_map), not a raw physical-address probe.
 */
/*
 * This diagnostic TU is compiled from the BootLog compile record, whose include set does not
 * expose osfmk/vm private headers in the CI xnu-work tree. Keep the ABI types self-contained
 * (arm64 LP64) and declare the VM mapper directly.
 */
typedef unsigned long vm_offset_t;
typedef unsigned long vm_size_t;

extern vm_offset_t ml_io_map(vm_offset_t phys_addr, vm_size_t size);

#define LUMING_FB_PHYS    0xFC800000UL
#define LUMING_FB_SIZE    0x2B00000UL
#define LUMING_FB_WIDTH   1236U
#define LUMING_FB_HEIGHT  2750U
#define LUMING_FB_STRIDE  4944U      /* width * 4, as printed by DarwinBoot */
#define LUMING_MARKS      5U

static volatile unsigned int *luming_fb;
static int luming_fb_state;          /* 0 = unmapped, 1 = mapped, -1 = failed */

static const unsigned int luming_colors[LUMING_MARKS + 1] = {
	0x00000000,                  /* 0 unused */
	0x00FF0000,                  /* 1 red */
	0x0000FF00,                  /* 2 green */
	0x000000FF,                  /* 3 blue */
	0x00FFFF00,                  /* 4 yellow */
	0x00FF00FF,                  /* 5 magenta */
};

void
luming_boot_mark(unsigned int stage)
{
	unsigned int first, last, y, x;

	if (stage < 1 || stage > LUMING_MARKS) {
		return;
	}
	if (!luming_fb_state) {
		vm_offset_t va = ml_io_map(LUMING_FB_PHYS, LUMING_FB_SIZE);
		if (!va) {
			luming_fb_state = -1;
			return;
		}
		luming_fb = (volatile unsigned int *)va;
		luming_fb_state = 1;
	}
	if (luming_fb_state < 0) {
		return;
	}

	/* Five equal bands over the 2750-row panel (the lead's example rows assumed a 6000-row FB). */
	first = (LUMING_FB_HEIGHT / LUMING_MARKS) * (stage - 1);
	last = (stage == LUMING_MARKS) ? LUMING_FB_HEIGHT : (LUMING_FB_HEIGHT / LUMING_MARKS) * stage;
	for (y = first; y < last; y++) {
		volatile unsigned int *row =
		    (volatile unsigned int *)((unsigned long)luming_fb + (unsigned long)y * LUMING_FB_STRIDE);
		for (x = 0; x < LUMING_FB_WIDTH; x++) {
			row[x] = luming_colors[stage];
		}
	}
	/* Device memory writes; make sure they have reached the FB before continuing. */
	__asm__ volatile("dsb sy" ::: "memory");
}
