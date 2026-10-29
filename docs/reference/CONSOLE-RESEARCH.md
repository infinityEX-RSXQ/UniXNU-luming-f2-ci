# CONSOLE-RESEARCH — how format-2 ports get early framebuffer console, and the smallest fix for luming

Research task (no shared-task id). Read-only investigation; **no device operations** and **no edits outside
this file**. Sources: local caches (`agents/official-crawl/...`, `unixnu-format2/UniXNU`, `refs/UniXNU-sheng`,
`agents/a-ipados17/_extern/components`, `agents/f2-luming/docs/*`, `agents/ufs-ci/*`) and the local XNU
Darwin-22 source tree (`D:\civitoip20\.tools\xnu-8796`). All paths are workspace-relative; line numbers are from
those local copies.

## TL;DR / recommendation

1. **How the supported format-2 ports do it:** DarwinBoot hands XNU the **GOP framebuffer as a physical
   address** (`Video[0]=FrameBufferBase`, `Video[1]=1`), and they rely on **stock XNU pexpert**: `arm_init()`
   → `PE_create_console()` → `PE_initialize_console()` → `initialize_screen()` → `ml_io_map_unmappable()`
   runs **while `kernel_map == VM_MAP_NULL`** and maps the framebuffer through the **pre-VM `io_map()` →
   `pmap_map_bd()` bootstrap path**. There is **no official identity-VA handoff and no official
   `makeMapping`/`PE_create_console` patch**; the only video_console changes in the official format-2 stack
   are the boot-progress bindings (`zzz-boot-progress.patch`), not mapping logic. sheng additionally passes
   `serial=3` as a belt-and-braces early console; dada has no serial and proves the video console alone works
   (its own notes + measured boot showed kernel console text on the panel).
2. **Pages:** every format-2 profile builds **native 4 KiB** XNU (machine config `BCM2837`, `ARM_PGSHIFT=12`);
   16 KiB kernels are *not* used by format-2. The `native-4k-*` patch set is the official one (bootstrap-table
   capacity, user ABI, signature-hash cache, 64-bit PA sync). `video_console.c` has exactly one page-size
   conditional — `if (!TEST_PAGE_SIZE_4K && lastVideoMapSize) pmap_remove(...)` on re-map — and no port patches
   `makeMapping` behaviour. So luming's 4 KiB build is not special *per se*; luming's divergence is the
   pre-VM mapping **inputs** (FB outside the DarwinBoot window / bootstrap-table budget), not the granule.
3. **QEMU:** the official QEMU flow also goes **AAVMF/EDK2 GOP → UniXNU menu → DarwinBoot → `boot_args.Video`**
   (boot-chain doc step 8 “Read framebuffer information from GOP”); `qemu-run.py --no-gop` exists for a
   text-only console, and the XNU-entry fixture is validated by its **serial log**, not by a paravirt
   framebuffer console. There is no separate QEMU FB-console code path to borrow.
4. **Smallest format-2-consistent fix for luming (recommended, in order):**
   - **Fix A (firmware, one field, proven precedent): DarwinBoot must set `Video[1] = 0` (`v_display=0`).**
     With `v_display=1` `PE_create_console()` takes the `kPEGraphicsMode` branch and the later
     `kPEAcquireScreen` keeps `gc_enable(FALSE)`, i.e. the text console stays off even after a successful
     mapping. The UniXNU-picasso port hit exactly this and fixed it in its vendored DarwinBoot
     (`drivers/DarwinBoot`, `v_display=0`); after that their free run “text console came up and the kernel log
     scrolled”. This is a one-line change to the board's DarwinBoot copy (`BootVideo.h:31` → `Video[1] = 0`),
     no XNU patch, no new format-2 deviation.
   - **Fix B (XNU device patch, ~15 lines) — only if the pre-VM mapping itself is the fault (your current
     report: exception confirmed inside the `initialize_screen → ml_io_map_unmappable` path with
     `kernel_map==VM_MAP_NULL`): defer video-console creation to a phase where `kernel_map` exists.** Keep
     `PE_init_platform(FALSE)` (it only *captures* `PE_state.video`), then in `arm_init()` guard
     `PE_create_console()` with `if (kernel_map != VM_MAP_NULL)` and add the deferred
     `PE_create_console()` in `kernel_bootstrap_thread()` **after**
     `kernel_startup_initialize_upto(STARTUP_SUB_KMEM)` and **before** `PE_init_iokit()`. At that point
     `io_map()` takes the post-VM branch (`kmem_alloc(kernel_map …) + pmap_map`), and the already-present
     `zzzzz-fix-darwinboot-physical-framebuffer.patch` makes the even, low physical address map instead of
     being treated as a VA. No DarwinBoot window change, no physmap enlargement.
   - **Fix C (fallback only): serial early console** (`serial=3`, sheng recipe) — robust for logs but needs the
     GENI UART path; the measured luming UART (`0xA9C000/0x4000`, SPI 579) is disabled in stock firmware, so
     this is not the first choice.
   - **Not recommended first:** the “identity/physmap window covering the FB” route (ALLOCATEWINDOW proposal)
     — it needs DarwinBoot to allocate one conventional-memory run that *includes* the FB, which is normally
     reserved/MMIO, and a kernel change to use `phystokv(FB)` instead of mapping; keep it as the *structural*
     fix once bring-up is unblocked.
5. **Do not ship the current bring-up diagnostics:** `zzzzz-luming-start-signals.patch`,
   `zzzzz-luming-boot-marks.patch`, `zzzzz-luming-early-console-flush.patch` are device-bisection aids
   (PSCI resets, colour bands, forced flush) and must be dropped for production; they also fight any console
   investigation by rebooting/halting at instrument points.

---

## 1. Evidence: what the supported format-2 ports actually do

### 1.1 DarwinBoot passes a **physical** GOP address with `display=1` (no identity VA)

Reference DarwinBoot (the same component pinned by the profiles: `UniXNU/DarwinBoot` @
`3325e352d7df68a9f9ad74832ed94a6acbbd7390`, copied in `agents/a-ipados17/_extern/components/DarwinBoot/`):

```c
/* agents/f2-luming/firmware/uefi/DarwinBootPkg/Driver/BootVideo.h:27-31 */
  if ((Gop->Mode->FrameBufferBase == 0) || (Gop->Mode->FrameBufferBase & 3) ||
      ...
  Video[0] = Gop->Mode->FrameBufferBase;
  Video[1] = 1;
  Video[2] = RowBytes;                       /* Video[]: base, display, rowBytes, width, height, depth */
```

`DarwinBoot.c` copies those six words into `boot_args.Video` (`CopyMem (Args->Video, Video, sizeof (Video))`,
`DarwinBoot.c:721`) and prints `DARWINBOOT: video base=… display=1 …` (`:755`). On luming the firmware log shows
`video base=0xFC800000 display=1 row=4944 width=1236 height=2750 depth=32`
(`agents/f2-luming/docs/BOOT-DEBUG-2026-10-29.md:64`). The base is an **even physical** address — it carries
neither a pre-mapped kernel VA nor the iBoot “b0 = physical” marker bit that `video_console.c` expects when
`kernel_map != NULL`.

### 1.2 XNU’s stock path runs `initialize_screen()` **before** `kernel_map` exists

(from `D:\civitoip20\.tools\xnu-8796`, Darwin-22 source):

```c
/* osfmk/arm/arm_init.c */
364:  PE_init_platform(FALSE, args);      /* only captures PE_state.video (boot_args.Video) */
516:  arm_vm_init(xmaxmem, args);         /* pmap/physmap; kernel_map is created later, in kmem_init() */
...
571:  PE_create_console();                /* -> PE_initialize_console -> initialize_screen */
574:  PE_init_printf(FALSE);

/* pexpert/arm/pe_init.c */
406:  PE_state.video.v_baseAddr = boot_args_ptr->Video.v_baseAddr;
416:  PE_state.video.v_display = boot_args_ptr->Video.v_display;
507:  PE_create_console(void)
515:      if (PE_state.video.v_display) PE_initialize_console(... kPEGraphicsMode)
         else                         PE_initialize_console(... kPETextMode)

/* osfmk/console/video_console.c */
2837:  newVideoVirt = boot_vinfo->v_baseAddr;
2838:  makeMapping = (kernel_map == VM_MAP_NULL) || (0 != (1 & newVideoVirt));
2839:  if (makeMapping) { new_vinfo.v_physaddr = boot_vinfo->v_baseAddr & ~3UL; ... }
2875:  newVideoVirt = ml_io_map_unmappable(phys, newMapSize, VM_WIMG_WCOMB/VM_WIMG_IO);
```

`kernel_map` is created later by `kmem_init()` in the bootstrap thread
(`osfmk/vm/vm_kern.c:3781` `kernel_map = vm_map_create_options(...)`, reached through `vm_mem_bootstrap`),
which the task’s own bisection confirmed: `T39 vm_mem_bootstrap` and `T41 kmem_init`
(`agents/f2-luming/docs/BOOT-DEBUG-2026-10-29.md:50-51`) come *after* `T30 PE_create_console`
(`:48`). Therefore at `PE_create_console()` time `kernel_map == VM_MAP_NULL`, `makeMapping` is forced TRUE,
and the framebuffer is mapped through the **pre-VM** path:

```c
/* osfmk/arm/io_map.c:100-114 */
if (startup_phase < STARTUP_SUB_KMEM) {          /* VM not initialized */
        start = virtual_space_start; virtual_space_start += round_page(size);
        assert(flags == VM_WIMG_WCOMB || flags == VM_WIMG_IO);
        if (flags == VM_WIMG_WCOMB) pmap_map_bd_with_options(start, phys, end, prot, PMAP_MAP_BD_WCOMB);
        else                        pmap_map_bd(start, phys, end, prot);
}
```

This is Apple’s designed early-console path: iBoot/Apple booters give a physical FB, and the kernel maps it
with `pmap_map_bd` before Mach VM exists. The comment in `video_console.c:2838` (“If VM is up, we are given a
virtual address, unless b0 is set to indicate physical”) is the same contract read in reverse.

### 1.3 The official format-2 stack does **not** patch this path

- `unixnu-format2/UniXNU/patches/xnu/zzz-boot-progress.patch` is the only official patch that touches
  `video_console.c`: it adds `boot_progress_bind(...)` calls next to the existing initialize/acquire paths and a
  `vcputc_options` hook; it does **not** change `makeMapping`, `ml_io_map_unmappable`, addresses or ordering.
- The OS profile series (`profiles/os/ipados-17.7.11-21H461/patches/xnu/series`) contains
  `zzz-boot-progress.patch`, `component:XnuPrelink/...security-init`, `...sparse-index` — nothing console/4K-IO
  related beyond the arch `native-4k-*` set.
- sheng (`agents/official-crawl/cache/repos/sheng/board.toml:74`) passes **`serial=3`** in `kernel_args` (plus
  `offline-legacy-gop=1`) — serial is a *parallel* early channel, not a replacement of the video console;
  sheng also selects `GopFramebuffer` (`:103`) but that component presents frames later (survey/service), it is
  not the pexpert console.
- dada passes **no `serial=`** at all; its board notes state the console model explicitly:
  `agents/official-crawl/recipe/cache/dada-full/docs/known-values.md:324-326` —
  *“The text console does not need it [the legacy display instrument]. DarwinBoot fills `boot_args.Video[6]`
  from the UEFI GOP (… base, display=1, rowBytes, width, height, depth=32) and XNU's own `pexpert` video
  console draws through that.”* And its measured boot (“kernel console output, then a panic screen with a
  message”, `known-values.md:346`) is device evidence that the stock pre-VM path works on format-2 hardware.
- Independent format-2 confirmation: the kebab (SM8250) port record says it “reaches MMU enablement, `arm_init`,
  `PE_init_platform` and the **early framebuffer console** on hardware”
  (`unixnu-format2/UniXNU/docs/devices/kebab.md:13`).

**Conclusion:** supported ports use the stock `PE_create_console → initialize_screen → ml_io_map_unmappable`
pre-VM path with a physical GOP base and no special kernel patch; extra `serial=3` only on sheng. The
`zzzzz-fix-darwinboot-physical-framebuffer.patch` currently in `agents/f2-luming/patches/xnu/device/series`
is **not** part of the official shape — it is our local fix for the post-VM case (see §3).

### 1.4 QEMU / ArmVirt

Official QEMU is a host-test path, not a second console implementation:

- `docs/concepts/boot-chain.md:76`: step 8 of the boot chain is *“Read the framebuffer information from GOP”*
  — the same DarwinBoot `BootVideo` path is exercised under AAVMF/EDK2;
- `docs/zh/reference/qemu.md:52`: `--no-gop` = “no display device, text console only”;
- the XNU-entry fixture (`scripts/qemu-entry/make-dt.py`, `gdb-stop.py`) is validated by its **serial log**
  (`qemu-run.py --log/--expect`), and screenshots are taken by QMP at the UniXNU menu, not from an XNU
  framebuffer console.

So QEMU has **no separate early-FB path** to copy; it confirms the intended handoff (GOP → DarwinBoot →
`boot_args.Video`) and gives a serial-only fallback.

---

## 2. 16 KiB vs 4 KiB — what the official profiles use

From `agents/official-crawl/cache/unixnu-docs/zh/xnu/four-k-page-tables.md` (and the same doc in
`unixnu-format2/UniXNU/docs/xnu/four-k-page-tables.md`):

| Model | `ARM_PGSHIFT` | `ARM_PGBYTES` | Notes |
| --- | --- | --- | --- |
| `BCM2837` (format-2 native) | 12 | 4096 | TG0 = 4 KiB, TG1 = 4 KiB |
| `VMAPPLE` | 14 | 16384 | Apple paths only |

- Format-2 builds XNU with the **`BCM2837` machine config**, i.e. native 4 KiB pages, and patches XNU where it
  assumes 16 KiB. Official arch patches (all under `unixnu-format2/UniXNU/patches/xnu/`):
  `native-4k-bootstrap-capacity.patch`, `native-4k-user-abi.patch`, `native-4k-signature-hash-cache.patch`,
  plus `zzx-pmap-sync-64bit-pa.patch`, `non-apple-pmap-field.patch`, `pgz-aligned-validation.patch`, etc.
- The bootstrap budget patch is the one relevant to early IO mapping:

```c
/* native-4k-bootstrap-capacity.patch */
+#elif !defined(APPLE_ARM64_ARCH_FAMILY) && !__ARM_16K_PG__
+/* Native 4 KiB: two roots plus up to seven L2 pages per 6 GiB mapping. */
+#define BOOTSTRAP_TABLE_SIZE (ARM_PGBYTES * 16)
```

  and `start.s` gains a capacity guard (`cmp $4, $6 / b.hs Lbootstrap_tables_exhausted`) plus a full-pool
  invalidation. This is the *only* bootstrap-capacity budget in the native 4 KiB path; it is sized for the
  kernel+physmap mapping, **not** for extra pre-VM IO mappings.
- `video_console.c` has exactly one 4 KiB conditional, and it only affects *re-mapping cleanup*:
  `osfmk/console/video_console.c:2898` `if (!TEST_PAGE_SIZE_4K && lastVideoMapSize) pmap_remove(...)`
  (“XXX why only !4K?”). There is no 4 KiB-specific mapping-size or address-translation code in the console.

**Conclusion:** sheng/dada/luming all run the same 4 KiB native build and patch set; 16 KiB is not used by
format-2. The granule does not explain luming’s failure by itself; the pre-VM IO mapping inputs do.

---

## 3. Why luming diverges (local evidence)

From `agents/f2-luming/docs/BOOT-DEBUG-2026-10-29.md`:

- PSCI-marker bisection: `T30 PE_create_console` / `T31 initialize_screen` / `T32 ml_io_map_unmappable` /
  `T33 vcattach` / `T34 PE_init_printf` are all reached (`:48-49`), and the kernel later reaches
  `T45 PE_init_iokit` (`:51`). With the boot-mark diagnostics replaced by `ret` the run freezes; an exception
  rather than a panic is proven (T37/T20/T46, `:52-54`).
- Firmware: `video base=0xFC800000 display=1 row=4944 1236x2750 depth=32`; `initialize_screen` takes the
  makeMapping path and calls `ml_io_map_unmappable(0xFC800000, ~13.6 MiB, VM_WIMG_WCOMB)` (`:66-68`).
- Window facts: with the 256 MiB ADT window DarwinBoot allocates at `0xE387C000` (window ends `0xF387C000`,
  below the FB); forcing 1 GiB picks `0x8C007C000` (above 4 GiB). **The framebuffer is outside the kernel
  physmap window in both configurations** (`:74-77`); the boot-mark bands, whose helper calls
  `ml_io_map(0xFC800000, 0x2B00000)`, never appear (`:68-69`).
- `ALLOCATEWINDOW-PROPOSAL.md` records the proposed next experiment (window below 4 GiB covering the FB) and
  notes the caveat: allocating one *conventional-memory* run that includes the FB may simply be impossible
  because the FB is reserved.
- The Lead’s current report (newer than the doc): the exception is confirmed inside
  `initialize_screen → ml_io_map_unmappable` with `kernel_map == VM_MAP_NULL` — i.e. the **pre-VM
  `io_map/pmap_map_bd`** path. That is consistent with the doc’s finding that the FB lies outside the
  DarwinBoot window and with the native-4K bootstrap budget being sized for the kernel+physmap only: the
  pre-VM IO mapping has no headroom/validated physmap range for `0xFC800000..0xFF300000`.

Two independent defects are visible and should be separated:

1. **Mode defect (independent of mapping):** `Video[1]=1` → `PE_create_console` selects `kPEGraphicsMode`;
   with graphics boot the text console is kept disabled until `kPEAcquireScreen` (`gc_enable(FALSE)`), which is
   why even a successful mapping can show nothing. The UniXNU-picasso port diagnosed exactly this and fixed it
   by setting `v_display=0` in its vendored DarwinBoot; its free run then showed the text console
   (`agents/official-crawl/cache/repos/picasso-yincql/board.toml:237-247`).
2. **Pre-VM mapping defect (if the exception is there):** the physical FB is outside the DarwinBoot window and
   the pre-VM `pmap_map_bd` mapping of it is not valid on this board/4 KiB bootstrap budget; defer the mapping
   until `kernel_map` exists.

The local `zzzzz-fix-darwinboot-physical-framebuffer.patch` only fixes the **post-VM address interpretation**
(an even, low `v_baseAddr` must be treated as physical rather than as a VA). It cannot fix the pre-VM mapping
and does not address `v_display`.

---

## 4. Options analysis (smallest → largest)

| Option | What changes | Evidence / precedent | Cost / risk | Verdict |
| --- | --- | --- | --- | --- |
| **A. `Video[1]=0` (v_display=0)** | DarwinBoot `BootVideo.h:31` (`Video[1]=1` → `0`); no XNU patch | UniXNU-picasso vendored DarwinBoot fixed the “console stays off” exactly so; after free run the text console scrolled (picasso board.toml:237-247). `PE_create_console` then takes `kPETextMode` (`pe_init.c:515-519`), and `kPEAcquireScreen` keeps text mode instead of `gc_enable(FALSE)`. | One field in our board DarwinBoot; no format-2 mechanism change; keeps the stock XNU console path byte-compatible. | **Do first.** |
| **B. Defer `PE_create_console()` to post-`kmem_init`** | Small device XNU patch: in `arm_init.c` guard `PE_create_console()` with `if (kernel_map != VM_MAP_NULL)`; add `PE_create_console()` in `kernel_bootstrap_thread()` after `kernel_startup_initialize_upto(STARTUP_SUB_KMEM)` (startup.c) and before `PE_init_iokit()`. Keep the existing physical-FB `makeMapping` patch so the post-VM `ml_io_map_unmappable` maps `0xFC800000`. | `io_map()` takes `kmem_alloc(kernel_map…)+pmap_map` once `startup_phase >= STARTUP_SUB_KMEM` (`osfmk/arm/io_map.c:100-125`); `kmem_init()` is `T41` in our own bisection, `PE_init_iokit` is `T45`; so the deferred call has a valid `kernel_map` and a safe location before IOKit prints. | ~15 lines in one `device:` patch, applies after the existing physical-FB patch; no DarwinBoot/window/physmap changes. Loses console output for the earliest `arm_init` prints unless the existing early-console-flush patch is kept as a one-shot replay; panic screen before VM stays unavailable (boot marks/UART fallback). Diverges from stock ordering (a bring-up-only deviation, removable later). | **Do second if A alone still faults/hangs at `initialize_screen`/`ml_io_map_unmappable`.** |
| **C. Serial early console** | Add `serial=3` (and a GENI/UART serial component); keep video for later | sheng uses `serial=3` (board.toml:74); luming UART measured `0xA9C000/0x4000`, SPI 579 (`agents/f2-luming/docs/A-FIX-CROSSWALK.md` b6), but SE7/UART is disabled in stock firmware and no physical fixture | Needs UART driver + wiring; not a framebuffer console | **Fallback/log channel only.** |
| **D. Identity-VA / physmap window covering FB** | DarwinBoot allocates a window below 4 GiB covering `0xFC800000..0xFF300000`; kernel uses `phystokv(FB)` (no mapping) or the existing `makeMapping` with `kernel_map` | `ALLOCATEWINDOW-PROPOSAL.md` (exact patch sketch); `BOOT-DEBUG` window facts | Requires the FB range to be one conventional-memory run (usually false — reserved/MMIO), changes `owned_memory_size`/physmap coverage, larger blast radius | **Structural fix later; not first.** |
| **E. `makeMapping`-only patch** | Already present (`zzzzz-fix-darwinboot-physical-framebuffer.patch`) | Fixes post-VM even-low address = physical | Insufficient alone for the pre-VM path; keep it, since B needs it | **Keep, not sufficient.** |

### Recommended patch set for the next device test

1. **DarwinBoot:** `Video[1] = 0` (board copy `firmware/uefi/DarwinBootPkg/Driver/BootVideo.h:31`; also make
   the diagnostic print show `display=0`). Acceptance: `DARWINBOOT: video base=0xFC800000 display=0 …`.
2. **Keep** `zzzzz-fix-darwinboot-physical-framebuffer.patch` as the **first** device-series patch (already
   first in `patches/xnu/device/series`).
3. **If the device still dies in `initialize_screen → ml_io_map_unmappable` (the Lead’s current exception):**
   add one device patch `zzzzz-luming-defer-video-console.patch`:
   - `osfmk/arm/arm_init.c`: change `PE_create_console();` (~:571) to
     `if (kernel_map != VM_MAP_NULL) { PE_create_console(); }`
   - `osfmk/kern/startup.c`: inside `kernel_bootstrap_thread()`, after
     `kernel_startup_initialize_upto(STARTUP_SUB_KMEM)` and before `#ifdef IOKIT / PE_init_iokit()`, call
     `PE_create_console();` (declared in `<pexpert/pexpert.h>`).
   - Acceptance: text appears before `PE_init_iokit` output; the `initialize_screen` log line shows
     `b=0xFC800000` and a mapped VA; no exception at the same PC.
4. **Disable the bring-up diagnostics for this test** (`zzz-boot-progress-min`/start-signals/boot-marks/
   early-console-flush) or at minimum keep them out of the console path; they PSCI-reset or force-flush and
   confound the result. Keep only the minimal `PE_init_printf`/kprintf path.

If neither A nor A+B shows text, the remaining suspect is the **drawing path inside `PE_init_iokit`**
(BOOT-DEBUG T27/T37/T46: freeze is an exception after `PE_init_iokit` starts; not a panic, not the flush), not
`initialize_screen`. In that case do not add more mapping patches blindly: instrument the first post-console
draw (`vcattach`/`vcputc`/`PE_init_printf`) with a single PSCI marker and compare the mapped VA with the PA
the boot marks use (`phystokv(0xFC800000)` vs the mapped VA) before choosing option D.

---

## 5. Direct answers to the three questions

1. **How do the officially supported format-2 ports get early console?** DarwinBoot passes the GOP
   framebuffer as a **physical address** (`BootVideo.h:30-31`), and XNU’s stock pexpert path maps it before
   Mach VM in `PE_create_console → initialize_screen → ml_io_map_unmappable` using the pre-VM
   `io_map/pmap_map_bd` route. They do **not** pass a virtual address, do **not** use an identity-VA handoff,
   do **not** patch `makeMapping`, `PE_create_console`, `arm_init` ordering, or video console code (the only
   video_console patch in the official stack is `zzz-boot-progress` binding progress). sheng adds
   `serial=3`; dada relies on the video console alone and its measured boot proves it works on format-2
   hardware; kebab independently records an early framebuffer console on hardware.
2. **Do they use 16 KiB pages / any pmap or video_console 4K patches?** No 16 KiB for format-2: they use the
   native 4 KiB `BCM2837` build with the official `native-4k-*` patch set (bootstrap capacity 16 pages, user
   ABI, signature hash cache, 64-bit PA sync). `video_console.c`’s only page-size conditional is the
   `TEST_PAGE_SIZE_4K` guard in re-map cleanup (`video_console.c:2898`); no port patches 4K-specific console
   mapping. (The Apple 16 KiB/`VMAPPLE` path is not used by format-2.)
3. **Does official UniXNU have a QEMU/ArmVirt framebuffer path?** QEMU is a host-test path: AAVMF/EDK2 supplies
   GOP, boot-chain step 8 reads framebuffer info from GOP (`boot-chain.md:76`), `qemu-run.py --no-gop` gives a
   text-only console, and the XNU-entry fixture is validated by **serial log** (`--log/--expect`), not by a
   paravirt framebuffer console. There is no QEMU-specific early-FB path to copy.

---

## 6. Evidence index (local, read-only)

| Evidence | Path:line |
| --- | --- |
| DarwinBoot video handoff (physical base, display=1) | `agents/f2-luming/firmware/uefi/DarwinBootPkg/Driver/BootVideo.h:30-31`; `DarwinBoot.c:721,755`; official copy `agents/a-ipados17/_extern/components/DarwinBoot/` |
| `arm_init` console ordering | `.tools/xnu-8796/osfmk/arm/arm_init.c:364,516,571,574` |
| Video capture / console creation | `.tools/xnu-8796/pexpert/arm/pe_init.c:406,416,507-519` |
| `initialize_screen` mapping logic | `.tools/xnu-8796/osfmk/console/video_console.c:2837-2838,2875,2898` |
| pre-VM `io_map` path | `.tools/xnu-8796/osfmk/arm/io_map.c:100-125`; `osfmk/vm/vm_kern.c:3781` (`kernel_map` in `kmem_init`) |
| Official boot-progress-only video patch | `unixnu-format2/UniXNU/patches/xnu/zzz-boot-progress.patch:57-95` (+ profile series `ipados-17.7.11-21H461/patches/xnu/series`) |
| Native 4 KiB / bootstrap capacity | `unixnu-format2/UniXNU/patches/xnu/native-4k-bootstrap-capacity.patch`; `docs/xnu/four-k-page-tables.md` (granule table, `BOOTSTRAP_TABLE_SIZE = ARM_PGBYTES*16`) |
| dada console model | `agents/official-crawl/recipe/cache/dada-full/docs/known-values.md:324-326,346`; `configs/dada_defconfig:40-46` |
| sheng serial + components | `agents/official-crawl/cache/repos/sheng/board.toml:74,103` |
| Format-2 early FB console on hardware | `unixnu-format2/UniXNU/docs/devices/kebab.md:13` |
| QEMU GOP/text paths | `agents/official-crawl/cache/unixnu-docs/zh/reference/qemu.md:52`; `.../zh/concepts/boot-chain.md:76,112` |
| luming console bisection | `agents/f2-luming/docs/BOOT-DEBUG-2026-10-29.md:48-54,63-77` |
| Window/proposal | `agents/f2-luming/docs/ALLOCATEWINDOW-PROPOSAL.md` |
| Picasso's `v_display=0` fix | `agents/official-crawl/cache/repos/picasso-yincql/board.toml:237-247` |
| Our current device patches | `agents/f2-luming/patches/xnu/device/series` + `zzzzz-fix-darwinboot-physical-framebuffer.patch` |

No files outside this document were modified; no device command was run.
