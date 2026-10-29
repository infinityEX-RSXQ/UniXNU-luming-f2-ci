# BOOT-MARKS — diagnostic stage bands (bring-up only)

Purpose: distinguish "XNU died before the video console attaches" from "kernel alive but console
output not flushed" on the DarwinBoot STAGE3/logo screen. No raw physical-address probes: the
framebuffer is mapped with the proper VM API (`ml_io_map`) from the luming boot-log archive.

## Files

| File | Role |
| --- | --- |
| `kits/luming/BootMarks.c` | `void luming_boot_mark(unsigned int stage)`: maps the GOP framebuffer once (`ml_io_map(0xFC800000, 0x2B00000)`), paints a full-width colour band for the stage, `dsb sy` |
| `patches/xnu/device/zzzzz-luming-boot-marks.patch` | five calls in `arm_init`/`kernel_bootstrap_thread`, validated against pinned xnu `d8b8029…` |
| `scripts/build-luming-boot-log.py` | builds `BootMarks.c` into `libLumingBootLog.a` (same compile record as BootLog/BootProcessProbe) |

## Stages and bands (panel is 1236x2750, stride 4944; five bands of 550 rows)

| Stage | Call site | Band rows | Nominal colour |
| --- | --- | --- | --- |
| 1 | right after `arm_vm_init(xmaxmem, args)` | 0–549 | red |
| 2 | right after `kprintf("kprintf initialized\n")` | 550–1099 | green |
| 3 | right after `PE_create_console()` | 1100–1649 | blue |
| 4 | right after `PE_init_platform(TRUE, &BootCpuData)` | 1650–2199 | yellow |
| 5 | just before `PE_init_iokit()` in `kernel_bootstrap_thread` | 2200–2749 | magenta |

Colours may appear R/B-swapped depending on the GOP pixel format; the **position** identifies the
stage unambiguously. The bands overwrite the logo/screen by design.

## Reading the result

- only band 1 → died in/after `arm_vm_init` before kprintf; map/VM/CPU issue.
- bands 1–2 → died between kprintf init and `PE_create_console` (serial/console setup).
- bands 1–3 → died between console creation and `PE_init_platform(TRUE)` (kprintf/printf path).
- bands 1–4 → platform expert up, died before/inside `PE_init_iokit` (KLD/kext/IOKit).
- all 5 bands but no XNU text → kernel reached IOKit; the video console attach/flush path is the
  problem (framebuffer mapping fix `zzzzz-fix-darwinboot-physical-framebuffer.patch` or
  `vcattach()`), not early boot.
- no bands at all → kernel never reached `arm_vm_init` (boot args/entry/DT) or the framebuffer
  mapping failed; use the AI9 firmware QR logger.

## Build / removal

`board.toml [kernel].archives` already includes `build-luming-boot-log.py`, so a normal
`unixnu build kernel` produces the marks. **This is bring-up instrumentation only:** before a
production build, remove `zzzzz-luming-boot-marks.patch` from
`patches/xnu/device/series` and optionally `BootMarks.c` from `kits/luming/`. No boot argument is
needed; the calls are unconditional in the patched diagnostic kernel.
## Early console-flush variant (REAL LOGS; diagnostic)

`patches/xnu/device/zzzzz-luming-early-console-flush.patch` adds, right after the boot-marks
stage-3 paint (i.e. after `PE_create_console()`):

```c
/*
 * luming bring-up: flush the buffered boot log to the video console now,
 * instead of waiting for PE_init_iokit()->vcattach().
 * PE_init_printf(TRUE) is vcattach() in pexpert/gen/pe_gen.c.
 */
PE_init_printf(TRUE);
```

`PE_init_printf(TRUE)` == `vcattach()` (pinned `pexpert/gen/pe_gen.c:135-141`), so the buffered
kprintf text is drawn immediately instead of waiting for `PE_init_iokit()`. This is the variant
that shows **real XNU console text** if the physical-framebuffer fix works.

- Series order: `zzzzz-fix-darwinboot-physical-framebuffer` → `zzzzz-luming-boot-marks` →
  `zzzzz-luming-early-console-flush` → `zzz-boot-progress-min` → …
- The patch is generated against the **post-boot-marks** tree (its context contains the mark-3
  block); validation therefore applies the full three-patch series to pristine pinned xnu files
  (`git apply` sequence PASS; reverse-check PASS).
- Unconditional in this diagnostic build; remove it with the boot-marks patch for production.
- If the screen shows the STAGE3/logo or bands but still no text after this variant, the failure is
  inside `vcattach()`/video console draw, not the early boot path; next step is the UFS BootLog
  read-back (docs/LOGGING.md) or the AI9 QR firmware log.

## Start signals A/B/C (start.s; diagnostic, last localization step)

`patches/xnu/device/zzzzz-luming-start-signals.patch` (applied **before** boot-marks):
- **A** in `_start_first_cpu`, right after `mov x20,x0 / mov x21,#0` (MMU OFF): fill first
  256 KiB of the GOP framebuffer PA `0xFC800000` with **RED** via x27/x28/x29 (unused in pinned
  `start.s`; x26 is loaded later and not touched), `dsb sy`.
- **B** in `common_start`, immediately **before** `MOV64 x0, SCTLR_EL1_DEFAULT` / `msr SCTLR_EL1`
  (MMU still OFF): fill 256 KiB at FB+2 MiB with **GREEN**, `dsb sy`.
- **C** immediately **after** the MMU-enable `msr SCTLR_EL1, x0; isb sy`: PSCI SYSTEM_RESET
  (`movz/movk w0,#0x84000009; smc #0`, `hvc #0` fallback, then `b .`). An automatic reboot proves
  this point was reached.

Registers x27/x28/x29 are unused anywhere in the pinned `osfmk/arm64/start.s`; x29 is chosen as
the colour scratch because it is not used in this file. Colours may appear R/B-swapped depending
on the GOP format; **positions** (FB base vs FB+2 MiB) are authoritative.

| Observation | Inference |
| --- | --- |
| no RED and no GREEN | death at/inside `_start_first_cpu` before signal A, or FB writes blocked (logo visible ⇒ FB works; inspect bootstrap table loop) |
| RED only | death between A and B: bootstrap page-table setup / `create_bootstrap_mapping` / `Lbootstrap_tables_exhausted` spin; consider `BOOTSTRAP_TABLE_SIZE` |
| RED+GREEN, no auto-reboot | death at/inside the MMU enable (`msr SCTLR_EL1`/`isb` fault) or PSCI reset call hung |
| RED+GREEN + auto-reboot while `boot.img` unchanged | MMU switch worked; death is later in C `arm_init` before `arm_vm_init()` (PE_init_platform(FALSE)/ml_parse_cpu_topology/arm_vm_init entry) |
| RED+GREEN + normal boot (no reset) | C did not execute with a reachable reset (PSCI conduit/EL issue) — report |

This is the last localization step before the real fix; remove the start-signals patch (and the
boot-marks/early-flush patches) for production builds.

## Device root cause: stale `super` J2 blob wins over the boot.img ramdisk (2026-10-29)

The diagnostic firmware big text on the phone reported `BASE 0xFFFFFFF003DC8000`, `Entry-Base 0x3601488`,
`End-Base 0x4797000`. That is an exact match for the **old A-line donor kernel**
`build/kernel-prelinked-darwin22-ufs-final.macho` — **not** the format-2 kernel
(`BASE 0xFFFFFFF00427C000`, `End-Base 0x4417000`). Every previous device image was booting the A-line
donor kernel, so the framebuffer fix, boot marks, early console flush and start signals never executed.

Cause: the phone's `super` partition still holds the A-line J2 payload. Firmware `J2HandoffDxe`
(`agents/f2-luming/firmware/.../UniXNUPkg/Driver/J2HandoffDxe`) reads the GPT `super` partition
(4 KiB J2 header at its start, magic `LUMING-J2-BLOB`, member `payload`), publishes a raw
SimpleFileSystem, and DarwinBoot — which consumes SFS + BlockIo — boots the stale SFS instead of the
format-2 FAT ramdisk from `boot.img`.

**Device bring-up prerequisite (P0):** format-2 `boot.img` tests are only meaningful on a device whose
(1) `super` is restored to a pristine/format-2 state, **or** (2) the FD's `J2HandoffDxe` is a no-op /
absent. Otherwise the old A-line kernel boots, regardless of the kernel payload.

### Static FDF/DSC verification of the format-2 payload path

`agents/f2-luming/firmware/uefi/Platforms/Xiaomi/lumingPkg` (uefi-builder-owned):
- `luming.fdf` includes `Include/APRIORI.inc`; APRIORI order: `UniXNURamDiskDxe` (line 23) →
  `DiskIoDxe` (69) → `PartitionDxe` (70) → `UFSDxe` (74) → `Fat.inf` (76); `luming.dsc` also lists
  DiskIo/Partition/EnglishDxe/Fat. **Ramdisk FAT payload path is present and ordered.**
- `UniXNURamDiskDxe` DEPEX `TRUE`; it reads the boot-image initrd from `/chosen`
  (`linux,initrd-start/end`, via the Mu-Silicium SEC x0-DTB HOB) and installs a read-only BlockIo;
  DiskIo/Partition/Fat then expose the ISO/FAT ramdisk to DarwinBoot.
- `J2HandoffDxe` is in the FV after the APRIORI list (DEPEX `GOP AND BlockIo`); its entry publishes
  the super J2 blob as SFS and prints `J2H: SUPER PAYLOAD PUBLISHED AS SimpleFileSystem`.
- `DarwinBoot` consumes SimpleFileSystem + BlockIo, so while the super blob exists the J2 SFS is a
  viable boot volume; with J2 no-op/absent the only filesystem is the ramdisk FAT.

Ordering requirement for format-2: RamDiskDxe before DiskIo/Partition/Fat (APRIORI), Fat after
Partition, J2 no-op/absent; no explicit dependency change is needed for the ramdisk path itself.

### Runtime check (device-state; approval-gated, not executed here)

From a recovery/adb-root context:
`dd if=/dev/block/by-name/super bs=4096 count=1 | strings | grep LUMING-J2-BLOB`
If the magic is present, the phone still carries the J2 blob: either restore a pristine/format-2
`super`, or boot an FD with the J2 no-op. CI cannot inspect the device `super`; `check-luming.py`
therefore only **warns statically** when the built FD contains an active `J2HandoffDxe`.

After a J2 no-op/pristine-super boot the diagnostic big text must show the format-2 kernel addresses
(`BASE 0xFFFFFFF00427C000`, `End-Base 0x4417000`); only then do the start-signals/boot-marks/console
results describe our kernel.
