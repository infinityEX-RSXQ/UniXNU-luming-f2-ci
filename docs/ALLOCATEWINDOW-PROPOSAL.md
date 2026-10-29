# PROPOSAL — DarwinBoot window below 4 GiB covering the luming GOP framebuffer

Status: proposal for **uefi-builder / device-builder**; not applied here (`firmware/` is uefi-builder's
tree). Source facts: `docs/BOOT-DEBUG-2026-10-29.md` §Framebuffer console investigation and
`firmware/uefi/DarwinBootPkg/Driver/DarwinBoot.c` (`AllocateWindow`, `WINDOW_SIZE`).

## Problem

On the real luming:

- The GOP framebuffer is physically `0xFC800000` and is `1236x2750x4` = `0x2B00000` bytes, so the
  panel spans `0xFC800000..0xFF300000`.
- The kernel physmap window chosen by `AllocateWindow` is 256 MiB at `0xE387C000`, ending at
  `0xF387C000` — **the framebuffer is outside the kernel window**.
- Forcing 1 GiB makes `AllocateWindow` pick an address above 4 GiB (`0x8C007C000`), also outside.
- Kernel reaches `PE_init_iokit` (PSCI marker bisection) but faults there and never paints the video
  console. The next experiment is to give XNU a window that contains the framebuffer.

## Proposed diagnostic patch (DarwinBoot.c)

1. For the bring-up/diagnostic build only, force the window to 512 MiB after the ADT read (keep the
   production `WINDOW_SIZE SIZE_256MB` under a macro):

```c
/* diagnostic only; remove for production */
#define LUMING_DIAG_WINDOW_SIZE  SIZE_512MB
#define LUMING_DIAG_WINDOW_BASE  0xDFE00000ULL   /* below 4 GiB, see alignment below */
#define LUMING_FB_PHYS           0xFC800000ULL
#define LUMING_FB_END            0xFF300000ULL
```

2. In `Boot`, after `if (WindowSize == 0) { WindowSize = WINDOW_SIZE; }`:

```c
#ifdef LUMING_DIAG_WINDOW_SIZE
  if (WindowSize < LUMING_DIAG_WINDOW_SIZE) {
    WindowSize = LUMING_DIAG_WINDOW_SIZE;   /* 512 MiB */
  }
#endif
```

3. At the top of `AllocateWindow` (after `GetMap`), try the preferred range before the first-fit loop:

```c
  /*
   * luming diagnostic: prefer a 512 MiB window below 4 GiB whose end is above the FB end.
   * Address must keep the same low 2 MiB bits as Kernel.Base (the existing allocator does this).
   * Candidate = 0xDFE7C000, end = 0xFFE7C000: below 4 GiB and covers 0xFC800000..0xFF300000.
   */
  Candidate = LUMING_DIAG_WINDOW_BASE | (Kernel->Base & (BLOCK_SIZE - 1));
  if ((Candidate + WindowSize) <= 0x100000000ULL) {
    for (Offset = 0; Offset + Stride <= Size; Offset += Stride) {
      Descriptor = (EFI_MEMORY_DESCRIPTOR *)((UINT8 *)Map + Offset);
      if (Descriptor->Type != EfiConventionalMemory) { continue; }
      if (Descriptor->PhysicalStart > Candidate) { continue; }
      if (Descriptor->PhysicalStart + EFI_PAGES_TO_SIZE (Descriptor->NumberOfPages) <
          Candidate + WindowSize) { continue; }
      Status = gBS->AllocatePages (AllocateAddress, EfiLoaderCode,
                                   EFI_SIZE_TO_PAGES (WindowSize), &Candidate);
      if (!EFI_ERROR (Status)) {
        *Address = Candidate;
        FreePool (Map);
        return EFI_SUCCESS;
      }
    }
    /* Leave a visible breadcrumb; then fall through to the existing first-fit path. */
    DiagDraw (L"PREFERRED WINDOW FAILED", 1);
  }
```

`0xDFE7C000 + 0x20000000 = 0xFFE7C000`, so the window stays strictly below 4 GiB and includes:
- FB start `0xFC800000`
- FB end `0xFF300000`

The `Kernel->Base & 0x1FFFFF` low bits (`0x7C000`) mirror the current allocator's alignment rule; if
the kernel does not actually require that physical/virtual low-bit match, the simpler base
`0xE0000000` (end exactly `0x100000000`) is the Lead's example and is equivalent in coverage.

## Important memory-map caveat

`gBS->AllocatePages (AllocateAddress, ...)` succeeds only when the **entire** 512 MiB range is one
`EfiConventionalMemory` run. The FB range may be marked reserved/MMIO in the UEFI map; if so the
preferred allocation fails and the existing `NO WINDOW`/`FREE` diagnostics should be captured (this
is itself useful: it tells us whether the FB is allocatable at all).

If the preferred range cannot be allocated:

1. Do **not** fall back to a window above 4 GiB; keep the existing 256 MiB first-fit path and report
   the free list.
2. Then evaluate the alternative "FB is mapped by `ml_io_map` only" path: boot marks use
   `ml_io_map(0xFC800000, 0x2B00000)`, so if the bands still do not appear even though the window
   experiment failed, the problem is in `ml_io_map`/`vcattach`, not only physmap coverage.
3. Only if the FB is conventional and allocatable, re-run the boot-mark/PE_init_iokit bisection with
   the 512 MiB window and the same kernel/payload.

## Validation sequence after the patch

- Rebuild the diagnostic FD with the patch and rebuild `boot.img` with the #51 payload/kernel + new
  FD (local host path already validated to reproduce #51 byte-for-byte).
- Device: confirm big-text `SIZE 0x20000000` and a window address `< 0x100000000`; boot-mark bands
  should now be visible if the physmap hypothesis is right.
- Then bisect `PE_init_iokit` (`InitIOKit`, `ConfigureIOKit`, `/chosen/memory-map` lookups,
  `vc_progress_initialize`) with PSCI-reset markers.
- Remove all diagnostic macros/patches for production.
