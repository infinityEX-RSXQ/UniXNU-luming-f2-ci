# CONSOLE-PATH — deferred console creation and physical msgbuf dump for luming (format-2 XNU)

Task `task-340`. Scope: `agents/f2-luming/patches/xnu/device/`, this design doc and
`docs/VALIDATION-HOST.log`. No device operations were performed.

Pinned target: Apple XNU `d8b80295118ef25ac3a784134bcf95cd8e88109f` / `xnu-10063.141.1` (the
iPadOS 17.7.11 profile source). Anchors below were generated against pristine files fetched from
that commit, not against the local `.tools/xnu-8796` (which is Darwin 22 and only used as a
structural cross-check). Line numbers are from the pristine target files.

## 1. Observed failure

Device bring-up now boots the format-2 prelinked kernel from the J2 super payload and reaches
`PE_init_iokit`, but there is no console output:

```
PE_create_console()
  -> PE_initialize_console()
    -> initialize_screen()
      -> ml_io_map_unmappable(0xFC800000, ~13.6 MiB, VM_WIMG_WCOMB)
        -> io_map()
          -> kernel_map-dependent path while kernel_map == VM_MAP_NULL
             => fault / freeze (exception confirmed by exception-vector PSCI-reset experiments)
```

The DarwinBoot window is `0xE387C000 + 0x8F84000`, ending at `0xF387C000`, exactly below the GOP
framebuffer at `0xFC800000`; with the 1 GiB-window experiment the window starts above 4 GiB. In
both configurations the framebuffer is outside the kernel V=P/physmap window, so `phystokv()`-
based access is not possible and `initialize_screen()` must create a real VM mapping.

The immediate host-side bug is not "the framebuffer is missing"; it is that
`PE_create_console()` is called from `arm_init()` **before Mach VM exists**, and the
`initialize_screen()` mapping path assumes a VM map. The target `io_map()` has two paths
(`osfmk/arm/io_map.c:101-131`):

* `startup_phase < STARTUP_SUB_KMEM`: bootstrap path, `pmap_map_bd[_with_options]` at
  `virtual_space_start`; no `kernel_map`, but the KVA must already have a bootstrap PTE.
* `startup_phase >= STARTUP_SUB_KMEM`: `kmem_alloc(kernel_map or io_submap)`, which cannot work
  while `kernel_map == VM_MAP_NULL`.

`arm_init()` calls `kernel_startup_initialize_upto(STARTUP_SUB_KPRINTF)` (target
`osfmk/arm/arm_init.c:530`) and then `PE_create_console()` at `arm_init.c:577`; at that point VM is
not initialized. The 4 KiB native patches change the bootstrap-page-table layout and the PTE
coverage of `virtual_space_start`, making the early `pmap_map_bd` path unsafe as well. Deferring the
console removes both variants from the early path.

## 2. Patch A — deferred console creation

File: `patches/xnu/device/zzzzz-luming-defer-console-init.patch` (git apply clean, LF only).

Changes:

| File | Anchor | Change |
| --- | --- | --- |
| `pexpert/arm/pe_init.c` | `PE_create_console()` at target line 520 | Add `#include <vm/vm_kern.h>`; make `PE_create_console()` return immediately while `kernel_map == VM_MAP_NULL` (the early `arm_init()` call). |
| `osfmk/kern/startup.c` | `console_init()` at target line 480 | Add `#include <pexpert/pexpert.h>`; after `vm_mem_bootstrap()` has created `kernel_map` and `console_init()` has set up the console ring, call `PE_create_console()`. The normal `PE_init_printf(TRUE)`/vcattach remains at `PE_init_iokit()` (`pexpert/arm/pe_init.c:258`). |

Why this is safe/effective:

* The early `arm_init()` call becomes a no-op only while `kernel_map == VM_MAP_NULL`; it does not
  remove the call or change `PE_create_console()`'s behavior once VM exists. The early-point skip is
  implemented inside `PE_create_console()` (rather than editing the `arm_init.c` call site) so the
  existing boot-marks/start-signals diagnostic patch context remains valid; behavior at the early
  call is identical to `/* deferred */` — it returns before `check_for_panic_log()` or any video
  access.
* `vm_mem_bootstrap()` (`osfmk/kern/startup.c:436`) runs `vm_map_init()`/`kmem_init()` and creates
  the real `kernel_map` (`osfmk/vm/vm_kern.c:3767-3784`). The later call therefore enters `io_map()`
  in the `startup_phase >= STARTUP_SUB_KMEM` branch and allocates the FB mapping from `kernel_map`
  (or `io_submap` for non-unmappable callers).
* `console_init()` runs at `startup.c:480` before the deferred call and initializes the console
  ring/lock; `msgbufp` is the statically initialized `&msgbuf`, and `vcattach()` later replays it.
  The screen creation itself is safe at this point because the required VM map exists.
* `PE_init_printf(FALSE)` remains in `arm_init()`; it only installs `PE_putc = console_write_char`,
  and `kprintf` output before the screen is created is captured by the console code and later
  replayed by `vcattach()`.
* The pre-existing `zzzzz-fix-darwinboot-physical-framebuffer.patch` is still required: after VM
  exists, `initialize_screen()` must treat the even low GOP address as physical and take the
  `makeMapping` path. With that patch + deferral, `ml_io_map_unmappable()` runs with a real
  `kernel_map` and returns a mapped VA.
* `zzzzz-luming-early-console-flush.patch` is **inactive** in the series: it called
  `PE_init_printf(TRUE)` right after the now-deferred early call, before the screen existed. The
  normal `PE_init_printf(TRUE)` in `PE_init_iokit()` remains the attach/flush point.

## 3. Patch B — msgbuf/early-ring physical dump

File: `patches/xnu/device/zzzzzzzzzzzzzzzzzzz-luming-msgbuf-phys-dump.patch` (git apply clean,
LF only).

Purpose: if the kernel still dies in `PE_init_iokit` (or later) after the console is deferred, the
device screen may remain blank and no panic log is reachable. With a debug boot arg, copy the early
console ring to a fixed physical address inside the DarwinBoot kernel window and reset; the next
boot's firmware MEMDUMP/DarwinBoot can read the magic/header/log.

Changes:

| File | Anchor | Change |
| --- | --- | --- |
| `osfmk/console/serial_console.c` | `console_write_char()` at target line 624 | Add an ARM64-only 128 KiB early ring; every console character is captured before `console_write()`. Add `luming_dump_msgbuf(const char *)`. |
| `osfmk/kern/debug.c` | `PE_panic_hook(message)` in `panic_trap_to_debugger()` at target line 901 | Declare and call `luming_dump_msgbuf(message)` after `PE_panic_hook()`. |

Dump format at the fixed PA:

```
offset  content
0x000   magic[8] = "LUMDUMP1", version=1, log_bytes, log_capacity, pa
0x020   kernel_slide, CNTPCT timestamp, reserved
0x040   reason[64] (panic message)
0x080   early console ring bytes (up to 128 KiB)
```

Boot args:

| Arg | Meaning |
| --- | --- |
| `luming-dump=1` | enable the dump+reset on panic (default off; no effect in production) |
| `luming-dump-pa=0xE4000000` | optional fixed PA override; default `0xE4000000` |

The default PA is inside the observed DarwinBoot window (`0xE387C000..0xF387C000`); it is written
through `phystokv(pa)`, cleaned with `flush_dcache(..., phys=0)`, followed by `dsb sy` and PSCI
`SYSTEM_RESET` (`0x84000009`, SMC then HVC fallback). `kernel_map` must exist (checked) and the PA
must be inside the kernel physmap window; if the DarwinBoot window changes, pass a PA inside it.

**Freeze limitation:** this patch hooks the panic path. A pure freeze (no panic) does not execute
`debug.c`. For freeze capture, the same `luming_dump_msgbuf()` function can be called from an
exception-vector/abort hook (e.g. the existing PSCI-reset experiment); that hook is intentionally
not part of this patch because the source exception-vector path is still under investigation. The
function is exported for the next step; it performs no device I/O and only writes normal memory.

Do not enable `luming-dump` in production: it writes a fixed physical page and resets on panic,
which would destroy the normal panic/reboot policy. It is a bring-up diagnostic.

## 4. 4 KiB early-mapping analysis

### 4.1 What the 4 KiB native patches change

* `BOOTSTRAP_TABLE_SIZE` in pristine target `osfmk/arm/pmap/pmap.h:117-120` is
  `ARM_PGBYTES * 34` for large memory and `ARM_PGBYTES * 8` otherwise. The native-4K arch patch
  `patches/xnu/native-4k-bootstrap-capacity.patch` adds a non-Apple-4K branch:
  `#define BOOTSTRAP_TABLE_SIZE (ARM_PGBYTES * 16)` and an `Lbootstrap_tables_exhausted` guard in
  `osfmk/arm64/start.s` so a new L2 table cannot overwrite adjacent kernel globals.
* `start.s` allocates 1 L1 page for V=P and 1 L1 page for KVA, then a variable number of L2 pages
  from the bootstrap pool (`start.s:588-612`); the target comment explicitly sizes the worst case
  for a "2G 4k page device" (`start.s:594-596`). With 4K granule, L2 blocks cover 2 MiB each and
  an L1 table covers 1 GiB; the 4K native patch enlarges/invalidates the pool using `PGBYTES` and
  `BOOTSTRAP_TABLE_BYTES`.
* The 4K changes to `arm_init.c`/`vm_map.c` set `PAGE_SHIFT_CONST`/`page_shift_user32` and VM map
  page shifts to 4K; they do not create a VM map early. `vm_mem_bootstrap()` still runs later in
  `kernel_bootstrap()`.

### 4.2 Why early `ml_io_map_unmappable()` is fragile

At the early call, two cases are possible depending on the exact startup phase/patch set:

1. **Phase < KMEM**: `io_map()` takes `pmap_map_bd[_with_options]()` at `virtual_space_start`.
   `pmap_map_bd()` walks `pmap_pte(kernel_pmap, vaddr)` and panics/faults if the bootstrap page
   tables do not already contain the PTE for that KVA. With 16K the bootstrap/KVA layout used by
   the round-table mapping happens to cover the first free KVA page(s); with the 4K native layout
   the same `virtual_space_start` can land in a 2 MiB/4K range for which no L2/L3 page was
   allocated. The 13.6 MiB framebuffer mapping itself needs ~7 L3 pages at 4K (512 entries × 4K =
   2 MiB per L3 page) and the bootstrap pool is only 64 KiB (16 × 4K) in the native-4K patch; this
   is tight and layout-sensitive.
2. **Phase >= KMEM** (or a later call): `io_map()` takes `kmem_alloc(kernel_map, ...)`; with
   `kernel_map == VM_MAP_NULL` this faults before any mapping is installed.

The observed freeze is consistent with case 2 (kernel_map NULL) or a 4K PTE miss in case 1. The
deferred patch removes both from the early path: it guarantees `kernel_map` exists and the call
happens after `console_init()`/`kmem_init()`.

### 4.3 Smallest safe fix and fallback order

1. **Primary (implemented):** defer `PE_create_console()` until after
   `vm_mem_bootstrap()`+`console_init()`, and rely on the normal `PE_init_printf(TRUE)`/vcattach in
   `PE_init_iokit()` for the flush. No pmap changes, no forged mappings, no bootstrap table
   growth.
2. **If the screen is still blank after deferral:** verify the physical-framebuffer patch is in
   the series and that `makeMapping` is true; then check the return of `ml_io_map_unmappable()` and
   log `initialize_screen`/`vcattach` state via the early ring. If `ml_io_map_unmappable()` fails
   only for the 13.6 MiB FB mapping, map it through `kernel_map` after `kmem_init()` (already the
   deferred path) rather than trying to reserve a larger bootstrap mapping.
3. **If early boot marks/diagnostics still call `ml_io_map()` before VM:** defer those calls too.
   BootMarks should not touch the FB before the deferred console; use the deferred call window.
4. **Do not simply enlarge `BOOTSTRAP_TABLE_SIZE` as the first fix.** It may avoid a table
   exhaustion guard but does not create PTEs for arbitrary `virtual_space_start` and does not
   supply `kernel_map`. The native-4K capacity patch already has a fail-closed
   `Lbootstrap_tables_exhausted` guard; keep it.
5. **Do not forge a V=P mapping for `0xFC800000`.** The DarwinBoot window does not cover it
   (`0xF387C000` end), and the 1 GiB window starts above 4 GiB. The only correct route is a real
   VM mapping via `kernel_map` after VM init, or fixing DarwinBoot's window allocator to cover the
   FB (not done here; it would be a firmware change, outside this task).

### 4.4 What was not changed

* `BOOTSTRAP_TABLE_SIZE`, `ARM_PGSHIFT`, `TCR`, start.s bootstrap mapping and pmap early paths are
  untouched. If future evidence shows a 4K bootstrap PTE miss, the next minimal change is to
  reserve/initialize the first free KVA L3 page in the bootstrap table (or bump the native-4K
  capacity to 34 pages) **and** test it with the `Lbootstrap_tables_exhausted` marker; this is not
  included because the deferred console avoids that path.
* The physical-framebuffer detection patch remains needed; without it `initialize_screen()` treats
  `0xFC800000` as a virtual address and writes to unmapped memory.

## 5. Series order

```
zzzzz-fix-darwinboot-physical-framebuffer.patch
zzzzz-luming-defer-console-init.patch          # new, Patch A
zzzzz-luming-start-signals.patch               # diagnostic
zzzzz-luming-boot-marks.patch                  # diagnostic
# zzzzz-luming-early-console-flush.patch       # inactive: superseded by Patch A
zzz-boot-progress-min.patch
... owner-cache/PMGR/AMFI series ...
zzzzzzzzzzzzzzzzz-luming-ufs-log.patch
zzzzzzzzzzzzzzzzzzz-luming-msgbuf-phys-dump.patch  # new, Patch B
```

Patch A must precede any diagnostic that calls `PE_init_printf(TRUE)`/vcattach; Patch B is
independent of console creation but should be last in the diagnostic group so panics from earlier
patches are captured if enabled.

## 6. Validation

Host-only, using pristine target files fetched at `d8b80295118ef25ac3a784134bcf95cd8e88109f`:

```text
git apply --check zzzzz-luming-defer-console-init.patch
  Checking patch pexpert/arm/pe_init.c... OK
  Checking patch osfmk/kern/startup.c... OK

git apply --check zzzzzzzzzzzzzzzzzzz-luming-msgbuf-phys-dump.patch
  Checking patch osfmk/console/serial_console.c... OK
  Checking patch osfmk/kern/debug.c... OK
```

Also checked: patches are LF-only, no BOM; `scripts/check-luming.py` and
`scripts/check-skeleton.py` results recorded in `docs/VALIDATION-HOST.log`. No device test was
performed.

## 7. Remaining risks

* **Freeze vs panic:** Patch B only captures panics. A pure freeze needs an exception-vector or
  watchdog hook; the dump function is exported for that follow-up.
* **Fixed PA:** `0xE4000000` must be inside the kernel window and not overwritten by the payload/
  bootloader. If DarwinBoot changes its allocation, set `luming-dump-pa` to a measured safe PA
  inside the window. Never point it at live kernel data.
* **PSCI conduit:** the reset sequence uses SMC then HVC; if the platform requires a different
  conduit/EL path, the dump is written but the reset may not happen. The header/timestamp still
  lets a hardware reset be used manually.
* **4K mapping:** if `ml_io_map_unmappable()` still fails after deferral, capture the exact
  `io_map` branch with the early ring (`startup_phase`, `kernel_map`, `virtual_space_start`,
  `pmap_pte` result) before changing bootstrap capacity; do not guess.
