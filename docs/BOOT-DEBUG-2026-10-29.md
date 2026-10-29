# 2026-10-29 device bring-up debugging log (format-2 luming)

## Root cause #1 — the device was never booting our kernel
The phone's `super` partition still held our A-line J2 payload. Firmware `J2HandoffDxe`
reads the J2 blob from `super` and publishes it as an SFS; DarwinBoot boots that kernel
and ignores the boot.img ramdisk payload. Proof: the diagnostic DarwinBoot big-text
printed `BASE 0xFFFFFFF003DC8000`, `Entry-Base 0x3601488`, `End-Base ~0x4797000` — an exact
match for the A-line donor kernel `build/kernel-prelinked-darwin22-ufs-final.macho`, not
for the format-2 prelinked kernel (`BASE 0xFFFFFFF00427C000`, `End-Base 0x4417000`).

## Fix #1 — ship our payload as the J2 blob in super
`build/super-format2*.img`: J2 header + member table (kernel/adt/config/payload) built from
the format-2 `payload.img` (`agents/ufs-ci/tools/fat32_inject.py`). Flashed with
`fastboot flash super`. DarwinBoot then reports `BASE 0xFFFFFFF00427C000` = our kernel.

## Diagnostic firmware (host build, no CI needed)
Source tree: `build/uefi-diag` (extracted `uefi-luming-ci-diag` bundle), rebuilt with
`python Platforms/Xiaomi/lumingPkg/DeviceBuild.py TARGET=RELEASE ENABLE_SECUREBOOT=0
FD_BASE=0xa7100000 FD_SIZE=0x300000 FD_BLOCKS=768 DEVICE_MODEL=0` after installing
`edk2-pytool-extensions edk2-pytool-library pyyaml regex` to `tmp/edk2lib`.
Local `unixnu bootimg` on Windows: `scripts/unixnu` copied to `build/uni-local`, patched for
Windows (utf-8 reads, sys.executable mkbootimg, tolerate existing DTB splash node), run with
msys2 `dtc` (`fdtput/fdtget`) and the bundled LLVM. boot.img rebuilt in ~1 min.

Diag firmware additions: big-text BASE/ADDR/ARGS/ENTRY/SIZE after STAGE2, 30 s stall,
full-screen clear after the stall (so only this boot's kernel marks are visible), boot_args
zeroed before filling (`ZeroMem(ArgsAddress, 16KiB)`).

## Kernel-side bisection method that works on device
Patch `movz w0,#0x8400,lsl16 ; movk w0,#9 ; smc #0` (3 instructions) at a function entry or
at a code boundary. If reached, the SoC performs PSCI SYSTEM_RESET and the phone reboots;
if not reached, the screen freezes. 12-byte patches go straight into the payload kernel inside
the J2 blob (extract payload, `Fat32Volume.replace_file`, rebuild J2 super, flash super).

Results (kernel = run #51 payload; symbol addresses shift +0x60 vs run #50):
- T1-T4b: `arm_init` entry reached; arm_vm_init→ret does NOT produce the stage-1 mark
  (mark1 needs VM, so that test was invalid).
- T5 arm_vm_init entry: reboot. T6 vm_set_page_size: reboot. T7 arm_vm_physmap_slide: reboot.
  T8 arm_vm_page_granular_prot: reboot. T11 after 2nd physmap_slide: reboot.
- T12b (assert path 0x73f3cfc, correct #51 address): no reboot → assert not taken.
- T13 after ldp in ptov assert block: reboot. T10b qsort (0x777221c in #51): reboot.
  T14 after qsort: reboot. T16 arm_auxkc_init (real address): no reboot but later markers show
  the auxkc branch is skipped because `auxkc_mh == 0`.
- T17 after set_mmu_ttb_alternate: reboot. T18 after set_mmu_ttb: reboot. T19 late deref block:
  reboot. T21 exception vectors → PSCI: reboot (an exception happens somewhere later).
- T25 arm_vm_init epilogue: reboot ⇒ **arm_vm_init completes**.
- T26 luming_boot_mark entry: reboot ⇒ mark1 is called.
- T30 PE_create_console entry: reboot. T31 initialize_screen: reboot. T32
  ml_io_map_unmappable: reboot. T33 vcattach: reboot. T34 PE_init_printf: reboot.
- T35 machine_startup: reboot. T36 kernel_bootstrap_thread: reboot. T38 kernel_bootstrap:
  reboot. T39 vm_mem_bootstrap: reboot. T40 vm_map_init: reboot. T41 kmem_init: reboot.
  T42 vm_fault_init: reboot. T43 kernel_memory_populate: reboot. T44 console_init: reboot.
  T45 PE_init_iokit: reboot ⇒ **kernel reaches the very end of kernel_bootstrap**.
- T27 (boot marks patched to `ret`, everything else normal): freezes at the STAGE3 screen.
  T37 (T27 + exception vectors → PSCI): reboots ⇒ the freeze is an exception, not a panic.
  T46 (T27 + PE_init_printf → ret): still freezes ⇒ the crash is NOT the console flush itself.
- T20 (panic → ret): still frozen (crash is not a panic).

So: kernel reaches PE_init_iokit; the fault happens inside PE_init_iokit (or the drawing path it
triggers) after its early prints; the console never shows text, so the framebuffer console is
still dead.

## Framebuffer console investigation
- Firmware prints `video base=0xFC800000 display=1 row=4944 width=1236 height=2750 depth=32`;
  `Args->Video` gets exactly these six fields; remaining Boot_Video fields are now zeroed.
- `initialize_screen` runs the makeMapping path (framebuffer physical, our
  `zzzzz-fix-darwinboot-physical-framebuffer` patch), calls `ml_io_map_unmappable(0xFC800000,
  ~13.6 MiB, VM_WIMG_WCOMB)`, then `vcattach`. No text ever appears; T27 freezes.
- Boot marks (kits/luming/BootMarks.c) call `ml_io_map(0xFC800000, 0x2B00000)`; the stage bands
  never appear (the only bands visible in photos are the DarwinBoot/darwinenter bars and the
  start.s A/B markers).
- 1 GiB window experiment: firmware `WindowSize` is taken from the ADT (256 MiB); forcing it
  to 1 GiB makes DarwinBoot print `SIZE 0x40000000` and `ADDR 0x8C007C000`. That address is
  above 4 GiB, so the kernel linear/identity window does NOT contain the framebuffer at
  `0xFC800000` — physmap-based access to the FB is impossible in that configuration.
- With the 256 MiB window DarwinBoot allocates at `0xE387C000` (window ends at `0xF387C000`,
  just below the FB), so the framebuffer is outside the kernel window there too.

## Next steps (in order)
1. Make the kernel window cover the framebuffer: allocate the DarwinBoot window below 4 GiB and
   including `0xFC800000` (e.g. 512 MiB at `0xE0000000`), or patch `AllocateWindow` to prefer
   such runs. Then the kernel physmap covers the FB and BootMarks can use `phystokv()`; verify
   with the boot-mark bands where the kernel really stops.
2. With visible stage bands, bisect PE_init_iokit: `InitIOKit`, `ConfigureIOKit`, the
   `/chosen/memory-map` lookups, `vc_progress_initialize`.
3. Fix the framebuffer console (`initialize_screen`/`vcattach`) — likely needs the FB inside the
   kernel physmap, then `vcattach` + `PE_init_printf(TRUE)` should print real XNU logs.
4. Then continue toward launchd (userspace root/Data/trust cache, M2/M3).

## Device state / recovery
- Flashed so far: `super` (format-2 J2 payloads), temporary `boot_b` (restored stock from
  `backup/luming-20261022-211723/partitions-raw/boot_a.img|boot_b.img`), `misc` (stock backup,
  to clear the A/B `unbootable` flag after failed boot attempts).
- Stock super backup: `backup/luming-20261022-211723/partitions-raw/super.img` (11.8 GB).
- CI (GitHub Actions) is blocked by account billing/spending limit; all kernel/firmware work in
  this session was done by local binary patching of the payload kernel + local EDK2 build.
